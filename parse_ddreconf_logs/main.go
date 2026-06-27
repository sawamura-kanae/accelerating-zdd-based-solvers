package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"log"
	"log/slog"
	"os"
	"path/filepath"
	"runtime"
	"slices"
	"strconv"
	"strings"
	"sync"

	"github.com/apache/arrow-go/v18/arrow"
	"github.com/apache/arrow-go/v18/arrow/array"
	"github.com/apache/arrow-go/v18/arrow/memory"
	"github.com/apache/arrow-go/v18/parquet"
	"github.com/apache/arrow-go/v18/parquet/compress"
	"github.com/apache/arrow-go/v18/parquet/pqarrow"
)

var (
	in      = flag.String("in", "", "input directory `paths` (comma separated, no space)")
	ext     = flag.String("ext", ".log", "log file's `extension` with a dot")
	out     = flag.String("out", "", "output file `path` without extension")
	mode    = flag.String("mode", "longest", "solved `mode` {shortest,longest}")
	threads = flag.Uint("threads", uint(runtime.NumCPU()), "spins up `num` goroutines (must be > 1)")
	verbose = flag.Bool("v", false, "log debug")
	logOut  = flag.String("log", "", "write log to this `file`")
)

const (
	// https://parquet.apache.org/docs/file-format/configurations/
	// will be a single row in (wide) format
	flushTotalBytes   = 512 * 1024 * 1024
	scannerBufferSize = 2 * 1024 * 1024 // allocates * (# parser)
)

func main() {
	flag.Parse()

	// quick flag varidation
	if *in == "" || *out == "" {
		fmt.Fprintf(os.Stderr, "-in (%q) or -out (%q) is empty\n", *in, *out)
		flag.Usage()
		os.Exit(2)
	}

	if *mode != "longest" && *mode != "shortest" {
		fmt.Fprintf(os.Stderr, "Unrecognized mode: %q\n", *mode)
		flag.Usage()
		os.Exit(2)
	}

	if *threads < 2 {
		fmt.Fprintf(os.Stderr, "Need > 1 goroutines to run parser but got %d\n", *threads)
		flag.Usage()
		os.Exit(2)
	}

	// open input files
	csvOutputName, pqOutputName := *out+".csv", *out+".parquet"

	csvOutput, err := os.Create(csvOutputName)
	if err != nil {
		fmt.Fprintln(os.Stderr, "cannot open", csvOutputName+":", err)
		flag.Usage()
		os.Exit(1)
	}
	defer csvOutput.Close()

	pqOutput, err := os.Create(pqOutputName)
	if err != nil {
		fmt.Fprintln(os.Stderr, "cannot open", pqOutputName+":", err)
		flag.Usage()
		os.Exit(1)
	}
	defer csvOutput.Close()

	// parse
	logger := log.Default()
	logger.SetFlags(log.Ltime)

	if *verbose {
		slog.SetLogLoggerLevel(slog.LevelDebug)
	}

	if *logOut != "" {
		f, err := os.Create(*logOut)
		if err != nil {
			log.Fatal(err)
		}
		defer f.Close()

		logger.SetOutput(f)
	}

	if err := writeCsvAndParquet(bytes.Split([]byte(*in), []byte(",")), csvOutput, pqOutput); err != nil {
		fmt.Fprintln(os.Stderr, "Parse failed:", err)
		os.Exit(1)
	}

	slog.Info("Done")
}

var csvHeader = []string{
	"graph_name", "vertices", "edges", "dat_file", "tokens", "independent_sets",
	"cpu_time", "wallclock_time", "max_memory", "zdd_time", "zdd_size",
	"solved?",                         // 0 (not solved, other values are invalid), 1 (solved), -1 (error)
	"error",                           // string
	"reconfiguration_sequence_length", // # a - 2
	"type",                            // opt, heur, orig
}

const (
	idxGraphName = iota
	idxVertices
	idxEdges
	idxDatFile
	idxTokens
	idxIndependentSets
	idxCpuTime
	idxWallclockTime
	idxMemory
	idxZddTime
	idxZddSize
	idxSolved
	idxError
	idxReconfigurationSequenceLength
	idxType
)

// if err, discard data
func readOne(path string, csvRow []string, pqa pqAdder, id uint) error {
	input, err := os.Open(path)
	if err != nil {
		return err
	}

	scn := bufio.NewScanner(input)
	scn.Buffer(make([]byte, scannerBufferSize), scannerBufferSize)

	for i := range csvRow {
		csvRow[i] = ""
	}

	readAsMuch(scn, csvRow, pqa, id, path)
	err = readTimeFooter(scn, csvRow, pqa)

	if err := scn.Err(); err != nil {
		panic(err) // if I/O/token too large, data is not correctly read
	}

	return err
}

// avoid regexp and allocation as much as possible
// this use of panic is bad engineering

// `^Input graph file parsed. # of vertices = ([0-9]+), # of edges = ([0-9]+)$`
func manualReInputGraph(bs []byte) ([]byte, []byte) {
	bs, ok := bytes.CutPrefix(bs, []byte("Input graph file parsed. # of vertices = "))
	if !ok {
		return nil, nil
	}

	vertices, bs := eatNumber(bs)
	if vertices == nil {
		return nil, nil
	}

	bs, ok = bytes.CutPrefix(bs, []byte(", # of edges = "))
	if !ok {
		return nil, nil
	}

	edges, bs := eatNumber(bs)
	if edges == nil || bs != nil {
		return nil, nil
	}

	return vertices, edges
}

func manualReInputGraphOrDie(bs []byte) ([]byte, []byte) {
	vertices, edges := manualReInputGraph(bs)
	if vertices == nil {
		panic("inputGraph")
	}

	return vertices, edges
}

// `^Solution space ZDD construction time = ([0-9\.]+)$`
func manualReZddTime(bs []byte) []byte {
	bs, ok := bytes.CutPrefix(bs, []byte("Solution space ZDD construction time = "))
	if !ok {
		return nil
	}

	m, bs := eatNumberDot(bs)
	if m == nil || bs != nil {
		return nil
	}

	return m
}

func manualReZddTimeOrDie(bs []byte) []byte {
	m := manualReZddTime(bs)
	if m == nil {
		panic("zddTime")
	}

	return m
}

// `^Solution space ZDD size = ([0-9]+)$`
func manualReZddSize(bs []byte) []byte {
	bs, ok := bytes.CutPrefix(bs, []byte("Solution space ZDD size = "))
	if !ok {
		return nil
	}

	m, bs := eatNumber(bs)
	if m == nil || bs != nil {
		return nil
	}

	return m
}

func manualReZddSizeOrDie(bs []byte) []byte {
	m := manualReZddSize(bs)
	if m == nil {
		panic("zddSize")
	}

	return m
}

// `^# of elements in the solution space = ([0-9]+)$`
func manualReIndependentSets(bs []byte) []byte {
	bs, ok := bytes.CutPrefix(bs, []byte("# of elements in the solution space = "))
	if !ok {
		return nil
	}

	m, bs := eatNumber(bs)
	if m == nil || bs != nil {
		return nil
	}

	return m
}

func manualReIndependentSetsOrDie(bs []byte) []byte {
	m := manualReIndependentSets(bs)
	if m == nil {
		panic("independentSets")
	}

	return m
}

// `^Step [0-9]+ time = ([0-9\.]+), # ZDD nodes = ([0-9]+), # elems = [0-9]+$`
func manualReSteps(bs []byte) ([]byte, []byte) {
	bs, ok := bytes.CutPrefix(bs, []byte("Step "))
	if !ok {
		return nil, nil
	}

	i, bs := eatNumber(bs)
	if i == nil {
		return nil, nil
	}

	bs, ok = bytes.CutPrefix(bs, []byte(" time = "))
	if !ok {
		return nil, nil
	}

	stepTime, bs := eatNumberDot(bs)
	if stepTime == nil {
		return nil, nil
	}

	bs, ok = bytes.CutPrefix(bs, []byte(", # ZDD nodes = "))
	if !ok {
		return nil, nil
	}

	zddNode, bs := eatNumber(bs)
	if zddNode == nil {
		return nil, nil
	}

	bs, ok = bytes.CutPrefix(bs, []byte(", # elems = "))
	if !ok {
		return nil, nil
	}

	i, bs = eatNumber(bs)
	if i == nil || bs != nil {
		return nil, nil
	}

	return stepTime, zddNode
}

func manualReStepsOrDie(bs []byte) ([]byte, []byte) {
	stepTime, zddNode := manualReSteps(bs)
	if stepTime == nil {
		panic("steps")
	}

	return stepTime, zddNode
}

// `^Reconfiguration time = [0-9\.]+$`
func manualReReconfigurationTimeOrDie(bs []byte) {
	bs, ok := bytes.CutPrefix(bs, []byte("Reconfiguration time = "))
	if !ok {
		panic("reconfigurationTime")
	}

	i, bs := eatNumberDot(bs)
	if i == nil || bs != nil {
		panic("reconfigurationTime")
	}
}

func readAsMuch(scn *bufio.Scanner, csvRow []string, pqa pqAdder, id uint, path string) {
	unrecoverable := false // Go, I'm so sorry

	defer func() {
		if r := recover(); r != nil && !unrecoverable {
			slog.Debug("Possible timeout", "id", id, "path", path, "error", r)
			slog.Warn("Not solved?", "name", filepath.Base(path), "line", scn.Bytes())
			csvRow[idxSolved] = "0"
		}
	}()

	// possible errors in the log files:
	// terminate called after throwing an instance of 'std::runtime_error'
	// The number of vertices must be less than 8192.
	line := readOrDie(scn)

	if bytes.Equal(line, []byte("terminate called after throwing an instance of 'std::runtime_error'")) {
		unrecoverable = true

		line = readOrDie(scn)
		if !bytes.HasSuffix(line, []byte("No such vertex")) {
			panic("not a 'No such vertex' error")
		}

		line = readOrDie(scn)
		if !bytes.Equal(line, []byte("timeout: the monitored command dumped core")) {
			panic("not a 'No such vertex' error")
		}

		line = readOrDie(scn)
		if !bytes.Equal(line, []byte("Command terminated by signal 6")) {
			panic("not a 'No such vertex' error")
		}

		csvRow[idxSolved] = "-1"
		csvRow[idxError] = "No such vertex"
		return
	} else if bytes.Equal(line, []byte("The number of vertices must be less than 8192.")) {
		unrecoverable = true

		line = readOrDie(scn)
		if !bytes.Equal(line, []byte("Command exited with non-zero status 255")) {
			panic("not a 'The number of vertices must be less than 8192.' error")
		}

		csvRow[idxSolved] = "-1"
		csvRow[idxError] = "The number of vertices"
		return
	}

	vertices, edges := manualReInputGraphOrDie(line)
	csvRow[idxVertices] = string(vertices)
	csvRow[idxEdges] = string(edges)

	l := bytesCutPrefixOrDie(readOrDie(scn), "s ")
	csvRow[idxTokens] = strconv.FormatInt(int64(bytes.Count(l, []byte(" "))+1), 10)

	if *mode == "shortest" {
		bytesHasPrefixOrDie(readOrDie(scn), "t ")
	}

	bytesEqualOrDie(readOrDie(scn), "Solution space ZDD construction start")
	bytesEqualOrDie(readOrDie(scn), "Solution space ZDD construction end")

	zddTime := manualReZddTimeOrDie(readOrDie(scn))
	csvRow[idxZddTime] = string(zddTime)

	zddSize := manualReZddSizeOrDie(readOrDie(scn))
	csvRow[idxZddSize] = string(zddSize)

	independentSets := manualReIndependentSetsOrDie(readOrDie(scn))
	csvRow[idxIndependentSets] = string(independentSets)

	if *mode == "shortest" {
		bytesEqualOrDie(readOrDie(scn), "Start searching a reconfiguration sequence from s to t")
	} else {
		bytesEqualOrDie(readOrDie(scn), "Start searching the longest reconfiguration sequence")
	}

	numA := 0
	for {
		line := readOrDie(scn)

		if bytes.HasPrefix(line, []byte("a ")) { // a NO
			numA++
			break
		}
		if *mode == "shortest" && bytes.Equal(line, []byte("t found")) {
			break
		}

		stepTime, zddNode := manualReStepsOrDie(line)
		stepTimeP, zddNodeP := parseFloat32OrDie(stepTime), uncheckedParseInt32(zddNode)
		pqa.stepTimesAdd(stepTimeP)
		pqa.zddNodesAdd(zddNodeP)
	}

	for {
		line := readOrDie(scn)

		if bytes.HasPrefix(line, []byte("a ")) {
			numA++
			continue
		}

		manualReReconfigurationTimeOrDie(line)
		break
	}

	switch *mode {
	case "shortest":
		// NO: numA counts 'a NO', yields -1
		// YES: numA counts 'a YES', 'a <independent set s>', ...
		csvRow[idxReconfigurationSequenceLength] = strconv.FormatInt(int64(numA-2), 10)
	case "longest":
		// exclude independent set s
		csvRow[idxReconfigurationSequenceLength] = strconv.FormatInt(int64(numA-1), 10)
	}

	csvRow[idxSolved] = "1"
}

// `^\tCommand being timed: "timeout .*/(.+?)\.col.*/(.+?)\.dat.*"`
// this match fails if the file paths are not in a directory!
func manualReColDat(bs []byte) ([]byte, []byte) {
	bs, ok := bytes.CutPrefix(bs, []byte("\tCommand being timed: \"timeout "))
	if !ok {
		return nil, nil
	}

	colLast := bytes.Index(bs, []byte(".col"))
	if colLast == -1 {
		return nil, nil
	}
	colFirst := bytes.LastIndexByte(bs[:colLast], '/')
	if colFirst == -1 || colFirst+1 == colLast {
		return nil, nil
	}
	col := bs[colFirst+1 : colLast]
	bs = bs[colLast+len(".col"):]

	datLast := bytes.Index(bs, []byte(".dat"))
	if datLast == -1 {
		return nil, nil
	}
	datFirst := bytes.LastIndexByte(bs[:datLast], '/')
	if datFirst == -1 || datFirst+1 == datLast {
		return nil, nil
	}
	dat := bs[datFirst+1 : datLast]

	return col, dat
}

func manualReColDatOrDie(bs []byte) ([]byte, []byte) {
	col, dat := manualReColDat(bs)
	if col == nil {
		panic("colDat")
	}

	return col, dat
}

func readTimeFooter(scn *bufio.Scanner, csvRow []string, pqa pqAdder) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("%v line=%q", r, scn.Bytes())
		}
	}()

	var l []byte

	// don't recover

	col, dat := manualReColDatOrDie(readOrDie(scn))

	typ, graph := typeAndGraph(col)

	csvRow[idxType] = typ
	pqa.typeAdd(typ)

	csvRow[idxGraphName] = graph
	pqa.graphAdd(graph)

	pqa.datFileAdd(string(dat))
	csvRow[idxDatFile] = string(dat)

	// rationale: I tested
	l = bytesCutPrefixOrDie(readOrDie(scn), "\tUser time (seconds): ")
	usr := parseFloat32OrDie(l)

	l = bytesCutPrefixOrDie(readOrDie(scn), "\tSystem time (seconds): ")
	sys := parseFloat32OrDie(l)

	csvRow[idxCpuTime] = formatFloat32(usr + sys)

	bytesHasPrefixOrDie(readOrDie(scn), "\tPercent of CPU this job got: ")

	l = bytesCutPrefixOrDie(readOrDie(scn), "\tElapsed (wall clock) time (h:mm:ss or m:ss): ")
	csvRow[idxWallclockTime] = formatFloat32(timeToSecOrDie(l))

	bytesHasPrefixOrDie(readOrDie(scn), "\tAverage shared text size (kbytes): ")
	bytesHasPrefixOrDie(readOrDie(scn), "\tAverage unshared data size (kbytes): ")
	bytesHasPrefixOrDie(readOrDie(scn), "\tAverage stack size (kbytes): ")
	bytesHasPrefixOrDie(readOrDie(scn), "\tAverage total size (kbytes): ")

	l = bytesCutPrefixOrDie(readOrDie(scn), "\tMaximum resident set size (kbytes): ")
	csvRow[idxMemory] = string(l)
	// we totally lose interest here...
	return
}

// please pqWriter.Close() when err == nil
// need csvWriter.Flush() to write to file
func prepareWriters(csvOutput, pqOutput io.Writer) (*csv.Writer, *pqarrow.FileWriter, *arrow.Schema, error) {
	// prepare csv
	csvWriter := csv.NewWriter(csvOutput)
	csvWriter.Write(csvHeader)

	// prepare parquet
	pqWriterProps := parquet.NewWriterProperties(
		parquet.WithCompression(compress.Codecs.Snappy),
		parquet.WithDictionaryDefault(true),
	)
	arrowWriterProps := pqarrow.NewArrowWriterProperties(
		pqarrow.WithStoreSchema(),
	)

	pqField := []arrow.Field{
		{Name: "graph_name", Type: arrow.BinaryTypes.String, Nullable: false},
		{Name: "dat_file", Type: arrow.BinaryTypes.String, Nullable: false},
		{Name: "step_times", Type: arrow.ListOf(arrow.PrimitiveTypes.Float32), Nullable: false}, // just use empty list as null?
		{Name: "zdd_nodes", Type: arrow.ListOf(arrow.PrimitiveTypes.Int32), Nullable: false},
		{Name: "type", Type: arrow.BinaryTypes.String, Nullable: false},
	}

	pqSchema := arrow.NewSchema(pqField, nil)

	pqWriter, err := pqarrow.NewFileWriter(pqSchema, pqOutput, pqWriterProps, arrowWriterProps)
	if err != nil {
		return nil, nil, nil, err
	}

	return csvWriter, pqWriter, pqSchema, nil
}

// (loads all the paths and) sorts according to file sizes
func walkDir(indirs [][]byte, ctx context.Context, cancel context.CancelCauseFunc) (<-chan string, int) {
	filePaths := make([]string, 0)
	fileSizes := make([]int64, 0)

	for _, indir := range indirs {
		if err := filepath.WalkDir(string(indir), func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return err
			}

			if d.IsDir() || !strings.HasSuffix(d.Name(), *ext) {
				return nil
			}

			info, err := d.Info()
			if err != nil {
				slog.Debug("Stat error", "error", err)
				slog.Info("Skip log", "path", path)
				return nil
			}

			filePaths = append(filePaths, path)
			fileSizes = append(fileSizes, info.Size())

			return nil
		}); err != nil {
			cancel(err)
		}
	}

	if err := ctx.Err(); err != nil {
		slog.Error("Giving up", "error", err)
		files := make(chan string)
		close(files)
		return files, 0
	}

	files := make(chan string, len(filePaths))
	defer func() {
		slog.Debug("Sent all files")
		close(files)
	}()

	indices := make([]int, len(filePaths))
	for i := range indices {
		indices[i] = i
	}

	slices.SortFunc(indices, func(a, b int) int {
		if fileSizes[a] < fileSizes[b] {
			return 1
		} else if fileSizes[a] > fileSizes[b] {
			return -1
		}

		return 0
	})

	for _, i := range indices {
		files <- filePaths[i]
	}

	return files, len(filePaths)
}

func runParser(files <-chan string, id uint, pqSchema *arrow.Schema, writes chan csvAndPq, ctx context.Context, cancel context.CancelCauseFunc, wg *sync.WaitGroup) {
	wg.Go(func() {
		defer func() { // log reader panics because of I/O
			if r := recover(); r != nil {
				cancel(fmt.Errorf("[id %d] %v", id, r))
			}
		}()

		csvRow := make([]string, len(csvHeader))

		// parquet builder
		pqBuilder := array.NewRecordBuilder(memory.DefaultAllocator, pqSchema)
		defer pqBuilder.Release()

		graphBuilder := pqBuilder.Field(0).(*array.StringBuilder)
		graphAdd := graphBuilder.Append

		datFileBuilder := pqBuilder.Field(1).(*array.StringBuilder)
		datFileAdd := datFileBuilder.Append

		stepTimesBuilder := pqBuilder.Field(2).(*array.ListBuilder)
		stepTimesValues := stepTimesBuilder.ValueBuilder().(*array.Float32Builder)
		stepTimesAdd := func(a float32) {
			stepTimesValues.Append(a)
		}

		zddNodesBuilder := pqBuilder.Field(3).(*array.ListBuilder)
		zddNodesValues := zddNodesBuilder.ValueBuilder().(*array.Int32Builder)
		zddNodesAdd := func(a int32) {
			zddNodesValues.Append(a)
		}

		typeBuilder := pqBuilder.Field(4).(*array.StringBuilder)
		typeAdd := typeBuilder.Append

		pqa := pqAdder{graphAdd, datFileAdd, stepTimesAdd, zddNodesAdd, typeAdd}

		for file := range files {
			stepTimesBuilder.Append(true)
			zddNodesBuilder.Append(true)

			slog.Debug("Read", "id", id, "path", file)
			if err := readOne(file, csvRow, pqa, id); err != nil {
				cancel(fmt.Errorf("too many errors: id=%d, path=%v, error=%v", id, file, err))
				slog.Error("Cancel", "name", filepath.Base(file))
				// ugly
				for _, b := range [...]*array.StringBuilder{graphBuilder, datFileBuilder, typeBuilder} {
					if b.Len() < stepTimesBuilder.Len() {
						b.AppendEmptyValue()
					}
				}
				pqBuilder.NewRecordBatch().Release()

				if ctx.Err() != nil {
					slog.Error("Canceled", "id", id)
					return
				}
			} else {
				select {
				case writes <- csvAndPq{record: pqBuilder.NewRecordBatch(), rows: slices.Clone(csvRow)}:
				case <-ctx.Done():
					slog.Error("Canceled", "id", id)
					return
				}
			}
		}

		slog.Debug("Return", "id", id)
	})
}

func consumeWrites(writes chan csvAndPq, csvWriter *csv.Writer, pqWriter *pqarrow.FileWriter, ctx context.Context, cancel context.CancelCauseFunc) <-chan struct{} {
	done := make(chan struct{})

	go func() {
		for write := range writes {
			csvWriter.Write(write.rows)

			pqRecord := write.record
			slog.Debug("Write", "graph_name", write.rows[idxGraphName], "dat_file", write.rows[idxDatFile], "type", write.rows[idxType])
			if err := pqWriter.WriteBuffered(pqRecord); err != nil {
				cancel(err)
			}
			pqRecord.Release()

			if pqWriter.RowGroupTotalBytesWritten() > flushTotalBytes {
				slog.Debug("Flush Parquet buffer")
				pqWriter.NewBufferedRowGroup()
			}

			if ctx.Err() != nil {
				slog.Error("Releasing writers")

				for rest := range writes {
					rest.record.Release()
				}
			}
		}

		slog.Debug("Writer return")
		done <- struct{}{}
	}()

	return done
}

func writeCsvAndParquet(indirs [][]byte, csvOutput, pqOutput io.Writer) error {
	csvWriter, pqWriter, pqSchema, err := prepareWriters(csvOutput, pqOutput)
	if err != nil {
		return err
	}
	defer csvWriter.Flush()
	defer pqWriter.Close()

	// parallel read/write
	ctx, cancel := context.WithCancelCause(context.Background())
	var producers sync.WaitGroup

	files, n := walkDir(indirs, ctx, cancel)
	writes := make(chan csvAndPq, n)

	numParsers := *threads - 1
	slog.Info(fmt.Sprintf("Running %d parsers", numParsers))
	for id := range numParsers {
		runParser(files, id, pqSchema, writes, ctx, cancel, &producers)
	}

	consumeWritesDone := consumeWrites(writes, csvWriter, pqWriter, ctx, cancel)

	producers.Wait()
	close(writes)
	slog.Info("Parsed all files")

	<-consumeWritesDone

	if err := context.Cause(ctx); err != context.Canceled {
		return err
	}

	return nil
}

type pqAdder struct {
	graphAdd     func(string)
	datFileAdd   func(string)
	stepTimesAdd func(float32) // rationale: running time scales at minutes and it'll be <10^38
	zddNodesAdd  func(int32)
	typeAdd      func(string)
}

type csvAndPq struct {
	record arrow.RecordBatch
	rows   []string
}

func readOrDie(scn *bufio.Scanner) []byte {
	if !scn.Scan() {
		panic("exhausted lines")
	}

	return scn.Bytes()
}

// parses as f64 but returns f32
func parseFloat32OrDie(s []byte) float32 {
	f, err := strconv.ParseFloat(string(s), 64)
	if err != nil {
		panic(err)
	}

	return float32(f)
}

func typeAndGraph(col []byte) (typ, graph string) {
	switch {
	case bytes.HasSuffix(col, []byte(".pwwt")):
		typ = "heur"
		graph = string(col[:len(col)-len(".pwwt")])
	case bytes.HasSuffix(col, []byte(".pw")):
		typ = "opt"
		graph = string(col[:len(col)-len(".pw")])
	default:
		typ = "orig"
		graph = string(col)
	}

	return
}

func formatFloat32(f float32) string {
	return strconv.FormatFloat(float64(f), 'f', -1, 32)
}

// the part may not be malformed (as it's from /usr/bin/time)
func timeToSecOrDie(s []byte) float32 {
	times := bytes.Split(s, []byte(":"))

	// 10^9 sec = 277778 hr ...
	if len(times) == 3 { // `^(\d+):(\d\d):(\d\d)$`
		return float32(uncheckedParseInt32(times[0])*60*60 + uncheckedParseInt32(times[1])*60 + uncheckedParseInt32(times[2]))
	}

	if len(times) == 2 { // `^(\d+):(\d\d(?:\.\d\d)?)$`
		return float32(uncheckedParseInt32(times[0])*60) + parseFloat32OrDie(times[1])
		// rationale: seconds part is not big
	}

	panic(fmt.Sprintf("%q is not time\n", s))
}

func bytesHasPrefixOrDie(bs []byte, prefix string) {
	if !bytes.HasPrefix(bs, []byte(prefix)) {
		panic(fmt.Sprintf("%q is not prefix of %q\n", prefix, bs))
	}
}

func bytesCutPrefixOrDie(bs []byte, prefix string) []byte {
	suf, ok := bytes.CutPrefix(bs, []byte(prefix))

	if !ok {
		panic(fmt.Sprintf("%q is not prefix of %q\n", prefix, bs))
	}

	return suf
}

func bytesEqualOrDie(bs []byte, to string) {
	if !bytes.Equal(bs, []byte(to)) {
		panic(fmt.Sprintf("%q does not equal %q\n", bs, to))
	}
}

func eatNumber(bs []byte) (numbers []byte, suf []byte) {
	for i := range len(bs) {
		if bs[i] < '0' || '9' < bs[i] {
			return bs[:i], bs[i:]
		}
	}

	return bs, nil
}

func eatNumberDot(bs []byte) (numbers []byte, suf []byte) {
	for i := range len(bs) {
		if (bs[i] < '0' || '9' < bs[i]) && bs[i] != '.' {
			return bs[:i], bs[i:]
		}
	}

	return bs, nil
}

func uncheckedParseInt32(s []byte) int32 {
	tens := [...]int32{1e9, 1e8, 1e7, 1e6, 1e5, 1e4, 1e3, 1e2, 1e1, 1e0}

	acc := int32(0)
	off := len(tens) - len(s)
	for i, b := range s {
		acc += tens[i+off] * int32(b-'0')
	}

	return acc
}
