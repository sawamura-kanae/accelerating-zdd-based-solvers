`walk_col.py` finds all `.pw.col` files in `pw_col` and runs the shortest
variant on opt, heur, and orig graphs (opt-available). The log files are in
`output.tar.gz`.

Some log files in the archive were run on different timeout duration not
exactly configurable by `walk_col.py`, but those runs were tried until they
succeed as well, and the same results can be obtained by running scripts in
this directory.

Only a single log file of longest timeout duration is in the archive for each
graph and instance pair.

-----

To run:

- Copy `cache.json.in` to `cache.json` (tracks which runs are finished).
- Edit `pw_col`, `pwwt_col`, `instances`, and `OUTPUT` at the top of
  `walk_col.py`, and `elf` in `walk_col.sh`.

```bash
python3 walk_col.py
```
