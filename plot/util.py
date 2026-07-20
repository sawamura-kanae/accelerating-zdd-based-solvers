import pandas as pd
import os.path as path

# consts and functions

# CSV file paths
SHORTEST_WIDE = "shortest_wide.csv"
FARTHEST_WIDE = "farthest_wide.csv"
PARQUET_PARENT = "../parse_ddreconf_logs"

# dtypes for wide-form csv
DTYPE = {
    "vertices": "Int32",
    "edges": "Int32",
    "tokens": "Int32",
    "reconfiguration_sequence_length": "Int32",
    "pw_opt": "Int32",
    "pw_heur": "Int32",
    "pw_orig": "Int32",
    "cpu_time_opt": "Float32",
    "cpu_time_heur": "Float32",
    "cpu_time_orig": "Float32",
    "wallclock_time_opt": "Float32",
    "wallclock_time_heur": "Float32",
    "wallclock_time_orig": "Float32",
    "max_memory_opt": "Int32",
    "max_memory_heur": "Int32",
    "max_memory_orig": "Int32",
    "zdd_time_opt": "Float32",
    "zdd_time_heur": "Float32",
    "zdd_time_orig": "Float32",
    "zdd_size_opt": "Int32",
    "zdd_size_heur": "Int32",
    "zdd_size_orig": "Int32",
    "solved?_opt": "Int8",
    "solved?_heur": "Int8",
    "solved?_orig": "Int8",
    "cpu_time_opt_preprocess": "Float32",
    "cpu_time_heur_preprocess": "Float32",
    "wallclock_time_opt_preprocess": "Float32",
    "wallclock_time_heur_preprocess": "Float32",
    "max_memory_opt_preprocess": "Int32",
    "max_memory_heur_preprocess": "Int32",
    "solved?_opt_preprocess": "Int8",
    "solved?_heur_preprocess": "Int8",
}


def read_parquet(pref):
    zdd_nodes = pd.read_parquet(path.join(PARQUET_PARENT, pref, "zdd_nodes"))
    step_times = pd.read_parquet(path.join(PARQUET_PARENT, pref, "step_times"))

    return zdd_nodes.join(step_times["step_times"])


def add_ref(data):
    prefs = ["pw", "wallclock_time", "solved?", "zdd_size", "zdd_time", "max_memory"]
    for pref in prefs:
        data[f"{pref}_heurref"] = data[f"{pref}_heur"].mask(
            data[f"pw_heur"] > data[f"pw_orig"], data[f"{pref}_orig"]
        )

    times = ["wallclock_time"]
    for pref in times:
        data[f"total_{pref}_opt"] = data[f"{pref}_opt"] + data[f"{pref}_opt_preprocess"]
        data[f"total_{pref}_heurref"] = (
            data[f"{pref}_heurref"] + data[f"{pref}_heur_preprocess"]
        )
        data[f"total_{pref}_orig"] = data[f"{pref}_orig"]

    return data
