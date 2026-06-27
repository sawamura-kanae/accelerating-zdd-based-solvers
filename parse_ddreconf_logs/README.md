This directory contains scripts to parse log files from ddreconf and produce an
intermediate CSV file and a Parquet for each variant.

- The intermediate CSV files are used by `../plot/` to generate the final CSV
  files.
- Parquet files contain the node count and time taken for each reconfiguration
  step.

-----

To run:

- Filter log files with longest timeout in case there are failed runs due to
  timeout but longer runs are available.

`filter_by_time.py` takes 3 arguments and picks longest runs. For example:

```bash
python3 filter_by_time.py ../run_ddreconf/heur/output_shortest ../run_ddreconf/heur/output_shortest_copied timeout
```

The above command selects log files with longest timeout from
`../run_ddreconf/heur/output_shortest` for each instance and copies them to
`../run_ddreconf/heur/output_shortest_copied`. Timeout duration follows
`"timeout"` in the file names. Log files included in this repository are
already filtered.

This step might not be needed, but duplicates are simply dropped in the final
CSV files.

-----

Build and run the parser:

```bash
go build .
```

The above command produces an executable `parse_ddreconf_logs[.EXE]`. It takes
several arguments and can parse log files from both shortest and farthest
variants. In particular, specify these options:

- `-in`: comma separated paths to directories to read from.
- `-out`: output file name without extension.
- `-mode`: `"shortest"` or `"longest"` (called farthest in the paper).

For example:

```
parse_ddreconf_logs -in ../run_ddreconf/opt_shortest/output,../run_ddreconf/heur/output_shortest -out shortest -mode shortest
```

The above command reads from `../run_ddreconf/opt_shortest/output` and
`../run_ddreconf/heur/output_shortest`, assuming shortest variant, and
generates `shortest.csv` and `shortest.parquet`. It warns failed runs and
parses as much as possible. Warnings are safe to ignore if the lines it reports
actually indicate the runs did not succeed, for example `"Command exited with
non-zero status 124"` (the run timed out). It gives up on unrecognized errors
rather than keep going.
