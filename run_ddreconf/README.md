This directory contains scripts to run ddreconf and collect its log files.

- `./opt_shortest/`: runs the shortest variant on opt, heur, and orig graphs.
- `./opt_farthest/`: runs the farthest variant on opt, heur, and orig graphs.
- `./heur/`: runs both variants on heur and orig graphs.

Each directory contains a short README.md.

Scripts in this directory run some instances not on `master-db.csv` as it's
globbing `.dat` files based on each discovered `.col` file. It results in some
invalid graph and instance pairs on graphs whose names share the same prefix.
As the `.dat` files are named predictably, there is not a lacking instance.
Such runs are discarded at the serialization step, and such log files are
omitted from the archives found in each directory.
