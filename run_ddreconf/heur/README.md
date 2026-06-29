- `run_heur.py` finds all `.pwwt.col` files in `pwwt_col` and runs both
  variants on heur graphs.
- `run_orig.py` finds all orig graphs whose `.pwwt.col` files are present in
  `pwwt_col` and runs both variants on orig graphs.

The log files are in `./output_shortest/` for the shortest variant, and
`./output_farthest/` for the farthest variant.

-----

To run:

- Edit `pwwt_col`, `instances`, `output_shortest`, `output_farthest` and
  `ddreconf` at the top of `run_orig.py` and `run_heur.py`.

```bash
python3 run_heur.py
python3 run_orig.py
```
