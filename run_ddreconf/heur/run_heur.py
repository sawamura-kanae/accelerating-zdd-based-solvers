import os
import os.path as path
import subprocess
import time

# where to find heur graphs
pwwt_col = "../../parse_pathwidth_logs/pwwt.col/"
# where to find original graphs and dat files
instances = "../../2023result/docs/solver/benchmark/"

# where to store shortest log files
output_shortest = "output_shortest"
# where to store farthest log files
output_farthest = "output_farthest"

ddreconf = "../../ddreconf/ddreconf"

def find_dats(graph_name: str):
    for root, _dirs, files in os.walk(instances):
        for file in filter(
            lambda file: file.startswith(graph_name) and file.endswith(".dat"), files
        ):
            yield file, path.join(root, file)
    return

def make_outpath(
    graph_name: str,
    graph_id: str,
    dat_name: str,
    time_str: str,
    out_dir: str,
):
    out_name = f"{graph_name}__{graph_id}.{dat_name}.timeout{time_str}.log"

    return path.join(out_dir, out_name)

def call_shell(out_path, cmd):
    print(f"[{time.asctime()}]", "writing to", out_path, flush=True)
    with open(out_path, mode="w", encoding="utf8", newline="") as out:
        ran = subprocess.run(
                cmd,
                stdout=out,
                stderr=out,
                )

        if ran.returncode != 0:
            print(f"[{time.asctime()}]", " ".join(cmd), "exited with", ran.returncode, flush=True)

def main():
    timeout_min = 30
    time_str = f"{timeout_min}m"

    for root, _dirs, files in os.walk(pwwt_col):
        for file in files:
            col_path = path.join(root, file)
            graph_name = file[:-len(".pwwt.col")]

            for dat_dot_dat, dat_path in find_dats(graph_name):
                dat_name = dat_dot_dat[:-len(".dat")]

                outpath_shortest = make_outpath(graph_name, "pwwt", dat_name, time_str, out_dir=output_shortest)
                outpath_farthest = make_outpath(graph_name, "pwwt", dat_name, time_str, out_dir=output_farthest)

                if not path.isfile(outpath_shortest):
                    cmd_shortest = ["/usr/bin/time", "-v",
                            "timeout", time_str,
                            ddreconf, col_path, f"--stfile={dat_path}",
                            "--tj", "--indset", "--st"]
                    call_shell(outpath_shortest, cmd_shortest)

                if not path.isfile(outpath_farthest):
                    cmd_farthest = ["/usr/bin/time", "-v",
                            "timeout", time_str,
                            ddreconf, col_path, f"--stfile={dat_path}",
                            "--tj", "--indset", "--longest"]
                    call_shell(outpath_farthest, cmd_farthest)


if __name__ == "__main__":
    main()
