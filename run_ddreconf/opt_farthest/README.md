`run.py` finds all `.pw.col` files in `pw_col` and runs the farthest variant on
opt, heur, and orig graphs (opt-available). The log files are in `./output/`.

The scripts are almost identical to `../opt_shortest/`. The differences are
timeout duration and variant selection.

Only a single log file of longest timeout duration is in the archive for each
graph and instance pair.

-----

To run:

- Copy `cache.json.in` to `cache.json` (tracks which runs are finished).
- Edit `pw_col`, `pwwt_col`, `instances`, and `OUTPUT` at the top of `run.py`,
  and `elf` in `run.sh`.

```bash
python3 run.py
```
