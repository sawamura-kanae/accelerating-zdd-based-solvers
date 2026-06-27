This directory contains scripts to run the program in `../pathwidth_opt/` and
collect its log files, which are used for generating opt graphs.

`run.py` finds all `.col` files in `instances` and hands them off to `run.sh`.
It remembers runs returning nonzero and keeps going until all runs succeed, but
here we included in `output_1h.tar.gz` log files we used which are ran for 1
hour.

As for log files not in `output_1h.tar.gz`, we also used scripts in the
subdirectory `./old/` which basically function the same way as scripts in this
directory, but execution metrics are counted differently. Log files in
`./old/output_1h.tar.gz` are ran for 1 hour as well and all timed out. Runs of
all the graphs are found in `./output_1h.tar.gz` or `./old/output_1h.tar.gz`.

Only `queen200x200.col` was taken by a slightly different script, but it was
run the same way as other inputs, and it can be obtained by running scripts in
this directory.

-----

To run:

- Copy `cache.json.in` to `cache.json` (tracks which runs are finished) and
  `state.json.in` to `state.json` (tracks timeout hour).
- Edit `instances` and `output` at the top of `run.py`, and `classpath` and
  `javaflag` in `run.sh`.

```bash
python3 run.py
```

-----

Scripts in `./old/` are run similarly with the same `cache.json.in` and
`state.json.in`.
