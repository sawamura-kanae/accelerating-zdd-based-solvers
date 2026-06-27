This directory contains scripts to run the program in `../pathwidth_heur/` and
collect its log files, which are used for generating heur graphs.

The scripts are almost identical to `../run_pathwidth_opt/`. The only
difference is timeout duration.

Only `queen200x200.col` was taken by a slightly different script, but it was
run the same way as other inputs, and it can be obtained by running scripts in
this directory.

-----

To run:

- Copy `cache.json.in` to `cache.json` (tracks which runs are finished) and
  `state.json.in` to `state.json` (tracks timeout minute).
- Edit `instances` and `output` at the top of `run.py`, and `classpath` and
  `javaflag` in `run.sh`.

```bash
python3 run.py
```
