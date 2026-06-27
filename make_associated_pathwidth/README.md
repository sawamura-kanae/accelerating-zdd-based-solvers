This directory contains a program to compute path decomposition implementing
the algorithm of Kobayashi and Nakahata described in Lemma 2 in
<https://doi.org/10.48550/arXiv.2010.02388>.

`compute_pathwidth_of_edge_ordering.cc` implements the algorithm. `run.py`
hands off graphs to it and outputs `pathwidth_of_ordering.csv` listing graphs
and associated pathwidths.

-----

To run:

- Build `compute_pathwidth_of_edge_ordering.cc`:

```bash
make build
```

- `run.py`:

It takes directories as arguments and walks them. For example:

```bash
python3 run.py ../2023result/docs/solver/benchmark/ ../parse_pathwidth_logs/pw.col/ ../parse_pathwidth_logs/pwwt.col/
```

Options:

- `--output`: the name of the resulting CSV file
- `--command`: this script runs `command <path/to/file.col>`
