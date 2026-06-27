This directory contains the program to compute heuristic decomposition
originally written by Yasuaki Kobayashi.

Two lines are added to L55 of Pathwidth.java found in `../pathwidth_opt/` to
let it early return.

To run:

```bash
make build
java -cp .build/pathwidth.jar Pathwidth <.col path>
```
