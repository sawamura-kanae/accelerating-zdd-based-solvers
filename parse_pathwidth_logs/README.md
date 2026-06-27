This directory contains a program to parse log files from Pathwidth, and a
program to generate opt and heur graphs.

- `make-graphs.rkt` reads log files from Pathwidth and generates opt and heur
  graphs for each completed run. We used graphs in `./pw.col` for opt and
  `./pwwt.col` for heur.
- `parse-metrics.rkt` parses output from `time` command and outputs CSV files.
  It is used by `../plot/` to collect runtime of Pathwidth.

-----

To generate graphs using `make-graphs.rkt`, specify these options.

- `--indir`: path to log files
- `--graphs`: path to original graph files
- `--out`: directory to output generated graphs to
- `--suffix-name`: added to generated file names before `.col`. Log files
  included in this repository used `.pw` for opt graphs, and `.pwwt` for heur
  graphs.

For example:

```bash
racket make-graphs.rkt --indir ../run_pathwidth_opt/output_1h/ --graphs ../2023result/docs/solver/benchmark/ --out ./pw.col --suffix-name .pw
racket make-graphs.rkt --indir ../run_pathwidth_heur/output/ --graphs ../2023result/docs/solver/benchmark/ --out ./pwwt.col --suffix-name .pwwt
```

The above commands generate opt and heur graphs.

-----

To parse log files for `../plot/` using `parse-metrics.rkt`, specify `--indir`
and `--out`. For example:

```bash
racket parse-metrics.rkt --indir ../run_pathwidth_opt/output_1h --out pathwidth_opt_time.csv
racket parse-metrics.rkt --indir ../run_pathwidth_heur/output --out pathwidth_heur_time.csv
```
