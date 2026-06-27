import os
import os.path as path
import subprocess
import time
import glob

# where to find heur graphs
pwwt_col = "../../parse_pathwidth_logs/pwwt.col/"
# where to find original graphs and dat files
instances = "../../2023result/docs/solver/benchmark/"

# where to store shortest log files
output_shortest = "output_shortest"
# where to store farthest log files
output_farthest = "output_farthest"

ddreconf = "../../ddreconf/ddreconf"

# run these graphs first
# not opt-available, but solved in heur
PRIORITY = [
         'LGC_exp_instance007',         'SAT_exp_instance014',
         'SAT_exp_instance016',         'SAT_exp_instance018',
                        'anna',                 'grid020x020',
                    'ph-05-04', 'random_instance006_graph005',
 'random_instance007_graph001', 'random_instance007_graph003',
 'random_instance007_graph005']

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

def get_original_graph_path(graph_name):
    original = glob.glob(f"{instances}/**/{graph_name}.col", recursive=True)
    return original

def run_if_not_found(graph_name, graph_path, dat_name, dat_path, time_str):
    outpath_shortest = make_outpath(graph_name, "orig", dat_name, time_str, out_dir=output_shortest)
    outpath_farthest = make_outpath(graph_name, "orig", dat_name, time_str, out_dir=output_farthest)

    if not path.isfile(outpath_shortest):
        cmd_shortest = ["/usr/bin/time", "-v",
                "timeout", time_str,
                ddreconf, graph_path, f"--stfile={dat_path}",
                "--tj", "--indset", "--st"]
        call_shell(outpath_shortest, cmd_shortest)

    if not path.isfile(outpath_farthest):
        cmd_farthest = ["/usr/bin/time", "-v",
                "timeout", time_str,
                ddreconf, graph_path, f"--stfile={dat_path}",
                "--tj", "--indset", "--longest"]
        call_shell(outpath_farthest, cmd_farthest)

def main():
    timeout_min = 30
    time_str = f"{timeout_min}m"

    for graph_name in PRIORITY:
        original = get_original_graph_path(graph_name)
        if len(original) != 1:
            raise Exception(original) # these particular graphs should be found
        [original_path] = original

        for dat_dot_dat, dat_path in find_dats(graph_name):
            dat_name = dat_dot_dat[:-len(".dat")]

            run_if_not_found(graph_name, original_path, dat_name, dat_path, time_str)

    for root, _dirs, files in os.walk(pwwt_col):
        for file in files:
            graph_name = file[:-len(".pwwt.col")]
            original = get_original_graph_path(graph_name)

            if len(original) != 1:
                print(f"[{time.asctime()}]", "search for", graph_name, "but got", original, flush=True)
                continue
            [original_path] = original

            for dat_dot_dat, dat_path in find_dats(graph_name):
                dat_name = dat_dot_dat[:-len(".dat")]

                run_if_not_found(graph_name, original_path, dat_name, dat_path, time_str)


if __name__ == "__main__":
    main()
