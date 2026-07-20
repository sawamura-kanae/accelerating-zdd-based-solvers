This directory contains scripts to produce final CSV files, plots, and
reproduce numbers from the paper text.

## CSV files

`shortest_wide.csv` and `farthest_wide.csv` are the final CSV files. The
decomposition gree is called heur in the CSV files. The columns in the CSV are
described below.

Columns from ddreconf log files:

- `graph_name`: `<graph_name>.col`
- `vertices`: number of nodes
- `edges`: number of edges
- `dat_file`: `<dat_file>.dat`
- `tokens`: number of tokens
- `independent_sets`: number of elements in the solution space
- `reconfiguration_sequence_length`: reconfiguration sequence length (for
  shortest variant, NO is -1, which is $\infty$ in the paper)
- `pw_{opt,heur,orig}`: associated pathwidth
- `cpu_time_{opt,heur,orig}`: _User time_ + _System time_ (seconds)
- `wallclock_time_{opt,heur,orig}`: _Elapsed (wall clock) time_ (seconds)
- `max_memory_{opt,heur,orig}`: _Maximum resident set size_ (kbytes)
- `zdd_time_{opt,heur,orig}`: solution space ZDD construction time
- `zdd_size_{opt,heur,orig}`: solution space ZDD size
- `solved?_{opt,heur,orig}`: 1 if the instance is solved in the log files, 0 if
  not solved, -1 if ddreconf cannot run
- `error_{opt,heur,orig}`: part of error message if ddreconf cannot run

Columns from Pathwidth log files:

- `cpu_time_{opt,heur}_preprocess`: _User time_ + _System time_ (seconds)
- `wallclock_time_{opt,heur}_preprocess`: _Elapsed (wall clock) time_ (seconds)
- `max_memory_{opt,heur}_preprocess`: _Maximum resident set size_ (kbytes)
- `solved?_{opt,heur}_preprocess`: 1 if the decomposition is found, 0 otherwise

## Scripts

To run scripts in this directory:

- This project uses uv to manage dependencies. To prepare the environment:

```bash
uv sync
```

-----

To generate final CSV files:

```bash
uv run long_to_wide.py ../parse_ddreconf_logs/shortest.csv shortest_wide.csv
uv run long_to_wide.py ../parse_ddreconf_logs/farthest.csv farthest_wide.csv
```

The above commands output the final CSV files.

-----

To generate plots:

```bash
uv run plot_figures.py
```

The above command writes pdf files to `./figs/`.

-----

To print stats in the paper text:

```bash
uv run print_stats.py
```

The output of the command is saved as `print_stats.py.txt` for reference.
