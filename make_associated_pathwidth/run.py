import os
from os import path
import subprocess
import csv

EXT = ".col"

def graph_and_type(name):
    if name.endswith(".pwwt"):
        return name[:-len(".pwwt")], "heur"
    elif name.endswith(".pw"):
        return name[:-len(".pw")], "opt"
    else:
        return name, "orig"

def walk_and_call(indirs, com, w):
    for indir in indirs:
        for root, _dirs, files in os.walk(indir):
            for file in files:
                if not file.endswith(EXT):
                    continue

                graph_dot = file[:-len(EXT)]
                graph_path = path.join(root, file)

                graph, typ = graph_and_type(graph_dot)

                print("call", graph_path, flush=True)
                ran = subprocess.run(
                        [com, graph_path],
                        capture_output=True,
                )

                if ran.returncode != 0:
                    raise Exception()

                w.writerow([graph, int(ran.stdout.strip()), typ])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("indirs",
                        type=str,
                        nargs="+",
                        help="walks each directory recursively",
                        )
    parser.add_argument("--output",
                        type=str,
                        help="write csv to this file",
                        default="pathwidth_of_ordering.csv",
                        )
    parser.add_argument("--command",
                        type=str,
                        default="./compute_pathwidth_of_edge_ordering.out",
                        )

    args = parser.parse_args()

    with open(args.output, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["graph_name", "pw", "type"])

        walk_and_call(args.indirs, args.command, writer)

    print("done")
