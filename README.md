# Accelerating ZDD-Based Solvers for Independent Set Reconfiguration via Path Decomposition

This repository contains code used for the paper.

-----

Each directory contains a short `README.md` describing how to run the programs.
To run all programs in this repository, Java, C++, Go, Racket, and Python are
needed.

Versions used that are not managed:

- Racket >= 8.18
- javac 11.0.25
- Python 3.9 (scripts that are not managed by uv)
- C++17

Other versions may be fine. Other programs are managed by version managers.
Please refer to `README.md` in each direcotry.

## Paper and code differences

Some terms (file names, column headers, code, etc.) in this repository are
named differently from the paper. These names were changed only in the paper,
after this artifact had been prepared; the most part of the repository is
intentionally left unchanged to avoid error-prone bulk renaming.

| paper    | code       | description                     |
| :------- | :--------- | :------------------------------ |
| opt      | pw         | decompotision, input graph name |
| gree     | heur, pwwt | decompotision, input graph name |
| farthest | longest    | variant of ISR                  |

## Programs

All programs used are found in:

To solve ISRP:

- `./pathwidth_opt/` and `./pathwidth_heur/`: computes optimal and heuristic
  path decomposition, run by scripts in `./run_pathwidth_opt/` and
  `./run_pathwidth_heur/`.
- [junkawahara/ddreconf](https://github.com/junkawahara/ddreconf/tree/c4c36fe3cbdc258c0e86f17a6c7aeccecc34e12f):
  ddreconf (commit `c4c36fe`), run by scripts in `./run_ddreconf/`.
  - default configuration of programs in this project assumes the repository
    exists at `./ddreconf/`, possibly by following a symbolic link.

Other programs dealing with input graphs:

- `./make_associated_pathwidth/`: compute associated pathwidth described in
  Lemma 2 in <https://doi.org/10.48550/arXiv.2010.02388>.
- `./parse_pathwidth_logs/`: generate opt and heur graphs.

Parsing and serializing:

- `./make_masterdb/`: list all instances from CoRe Challenge 2023.
- `./parse_ddreconf_logs/`: parse log files from ddreconf. The output is used
  by `./plot/` to generate final CSV files and plots.

## Graphs and Instances

All graphs and instances are found in:

- [core-challenge/2023result](https://github.com/core-challenge/2023result/tree/c1cef80ad721c57ad2181d30fb5fdd0e4cef6dcd):
  CoRe Challenge 2023, orig graphs and all instances.
  - default configuration of programs in this project assumes the repository
    exists at `./2023result/`, possibly by following a symbolic link.
- `./parse_pathwidth_logs/{pw.col,pwwt.col}/`: opt and heur graphs generated
  from orig graphs and corresponding path decompositions.

## Log files

All log files are found in:

- `./run_pathwidth_opt/output_1h/`, `./run_pathwidth_opt/old/output_1h/`: log
  files from opt version of Pathwidth (`./pathwidth_opt/`).
- `./run_pathwidth_heur/output/`: log files from heur version of Pathwidth
  (`./pathwidth_heur/`).
- `./run_ddreconf/opt_shortest/output/`: log files from ddreconf on
  opt-available graphs on the shortest variant.
- `./run_ddreconf/heur/output_shortest/`: log files from ddreconf on heur and
  orig graphs on the shortest variant.
- `./run_ddreconf/opt_farthest/output/`: log files from ddreconf on
  opt-available graphs on the farthest variant.
- `./run_ddreconf/heur/output_farthest/`: log files from ddreconf on heur and
  orig graphs on the farthest variant.

-----

- Log files larger than 10MiB are gzipped. To unzip: `gunzip
  <path/to/file.log>.gz`.
- Gzipped log files larger than 100MiB are split. To unzip: `cat
  <path/to/file.log>.gz.part.* | gunzip > <path/to/file.log>`.

## Final results

The final serialization and scripts for plots and stats are in `./plot/`.

## Directory layout

```text
.
|-- pathwidth_opt/             # Java program for optimal path decompositions
|-- pathwidth_heur/            # Java program for heuristic path decompositions
|-- run_pathwidth_opt/         # scripts and logs for pathwidth_opt
|   `-- old/                   # older opt runs with different metric handling
|-- run_pathwidth_heur/        # scripts and logs for pathwidth_heur
|-- parse_pathwidth_logs/      # parsers for Pathwidth logs and generated graphs
|   |-- pw.col/                # graphs from optimal path decompositions
|   `-- pwwt.col/              # graphs from heuristic path decompositions
|-- run_ddreconf/              # scripts and logs for ddreconf experiments
|   |-- opt_shortest/          # shortest variant on opt-available graphs
|   |-- opt_farthest/          # farthest variant on opt-available graphs
|   `-- heur/                  # shortest/farthest variants on heur and orig graphs
|-- parse_ddreconf_logs/       # Go parser and intermediate ddreconf results
|-- make_masterdb/             # CoRe Challenge 2023 instance list generation
|-- make_associated_pathwidth/ # associated pathwidth computation
|-- util/                      # shared Racket utilities
`-- plot/                      # final serialization and plotting scripts
```
