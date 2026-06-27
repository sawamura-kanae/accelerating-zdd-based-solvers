import os
import os.path as path
import subprocess
import time
import json

# where to find opt graphs (flat)
pw_col = "../../parse_pathwidth_logs/pw.col/"
# where to find heur graphs (flat)
pwwt_col = "../../parse_pathwidth_logs/pwwt.col/"
# where to find original graphs and dat files
instances = "../../2023result/docs/solver/benchmark/"

# where to store opt log files
OUTPUT = "output/"

dotsh = "walk_col.sh"

def find_dats(graph_name: str):
    for root, _dirs, files in os.walk(instances):
        for file in filter(
            lambda file: file.startswith(graph_name) and file.endswith(".dat"), files
        ):
            yield file, path.join(root, file)
    return


def find_old_graph(graph_name: str):
    for root, _dirs, files in os.walk(instances):
        for file in filter(lambda file: file == f"{graph_name}.col", files):
            yield file, path.join(root, file)
            return  # TODO: only one file should exist

def remove_pw_dot_col(pw_dot_col: str):
    return pw_dot_col[: -len(".pw.col")]

def make_timeout_str(timeout_hour: float):
    return f"{timeout_hour}h"

def make_outpath(
    graph_name: str,
    graph_id: str,
    dat_name: str,
    timeout_hour: float,
):
    time_str = make_timeout_str(timeout_hour)
    out_name = f"{graph_name}__{graph_id}.{dat_name}.timeout{time_str}.log"

    return path.join(OUTPUT, out_name)


def call_shell(
    out_path: str,
    graph_path: str,
    dat_path: str,
    timeout_hour: float,
):
    time_str = make_timeout_str(timeout_hour)

    print(f"[{time.asctime()}]", "writing to", out_path, flush=True)
    with open(out_path, mode="w", encoding="utf8", newline="") as out:
        ran = subprocess.run(
            ["bash", dotsh, graph_path, dat_path, time_str],
            stdout=out,
            stderr=out,
        )

        return ran.returncode

def read_json(file):
    with open(file, encoding="utf8", newline="") as j:
        return json.load(j)

def write_json(file, data):
    with open(file, mode="w", encoding="utf8", newline="") as j:
        json.dump(data, j, separators=(",", ":"))


def main():
    timeout_hour = 0.5
    cache = read_json("cache.json")

    while True:
        nochange = True

        for root, _dirs, files in os.walk(pw_col):
            for file in files:
                if not file.endswith(".pw.col"):
                    continue

                graph_path = path.join(root, file)
                graph_name = remove_pw_dot_col(file)

                for dat_dot_dat, dat_path in find_dats(graph_name):
                    dat_name = dat_dot_dat[: -len(".dat")]

                    for _old_graph, old_graph_path in find_old_graph(graph_name):

                        def doit(cache_graph_name, id, graph_path):
                            nonlocal nochange

                            keys = [cache_graph_name, dat_name]

                            # ugly
                            if (
                                keys[0] in cache
                                and keys[1] in cache[keys[0]]
                                and cache[keys[0]][keys[1]] == 1
                            ):
                                return

                            if keys[0] not in cache:
                                cache[keys[0]] = dict()
                            cache[keys[0]][keys[1]] = 0
                            nochange = False

                            out_path = make_outpath(
                                graph_name, id, dat_name, timeout_hour
                            )
                            if os.path.isfile(out_path):
                                return

                            if (
                                call_shell(out_path, graph_path, dat_path, timeout_hour)
                                == 0
                            ):
                                cache[keys[0]][keys[1]] = 1

                        doit(f"{graph_name}.pw", "pw", graph_path)
                        doit(graph_name, "orig", old_graph_path)
                        doit(
                            f"{graph_name}.pwwt",
                            "pwwt",
                            path.join(pwwt_col, f"{graph_name}.pwwt.col"),
                        )

                        write_json("cache.json", cache)

        if nochange:
            return

        timeout_hour *= 2


if __name__ == "__main__":
    main()
