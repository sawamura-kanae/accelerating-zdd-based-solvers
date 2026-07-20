import pandas as pd


def long_to_wide_with_pw(
    in_csv: str,
    out_csv: str,
    pathwidth_csv: str,
    pathwidth_runs_opt_csv: str,
    pathwidth_runs_heur_csv: str,
    master_db: str,
):
    master = pd.read_csv(
        master_db,
        dtype={
            "vertices": pd.Int32Dtype(),
            "edges": pd.Int32Dtype(),
            "tokens": pd.Int32Dtype(),
        },
    )

    data = pd.read_csv(
        in_csv,
        dtype={
            "vertices": pd.Int32Dtype(),
            "edges": pd.Int32Dtype(),
            "tokens": pd.Int32Dtype(),
            "zdd_size": pd.Int64Dtype(),
            "max_memory": pd.Int32Dtype(),
            "solved?": pd.Int32Dtype(),
            "reconfiguration_sequence_length": pd.Int32Dtype(),
            "error": str,
        },
    )

    indices = ["graph_name", "dat_file"]
    duplicates = data[indices + ["type"]].duplicated()

    if duplicates.sum() != 0:
        print("there are duplicates:")
        print(data[duplicates].reset_index(drop=True)[indices + ["type"]])

        # select solved and longer ones
        data = data.sort_values(
            ["solved?", "cpu_time"],
            ascending=[False, False],
            ignore_index=True,
        )
        data = data.drop_duplicates(indices + ["type"])

    data = data.pivot(index=["graph_name", "dat_file"], columns=["type"])
    data.columns = [x if y == "" else f"{x}_{y}" for x, y in data.columns]
    data = data.reset_index()

    # rows from master-db
    data = master[indices].merge(data, how="left", on=indices)

    # only solved instances fill these columns
    common_columns = [
        "vertices",
        "edges",
        "tokens",
        "independent_sets",
        "reconfiguration_sequence_length",
    ]
    for c in common_columns:
        cols = data.filter(like=f"{c}_")

        bad = cols.nunique(axis=1) > 1
        if bad.sum() != 0:
            raise Exception(data[bad])

        data[c] = cols.max(axis=1)
        data = data.drop(columns=cols.columns)

    # should match master-db
    take_master = ["vertices", "edges", "tokens"]
    data = data.fillna(master[take_master])
    if not data[take_master].equals(master[take_master]):
        print("doesn't match")  # either parser is wrong

    # instances that are not run
    data[["solved?_heur", "solved?_opt", "solved?_orig"]] = data[
        ["solved?_heur", "solved?_opt", "solved?_orig"]
    ].fillna(0)

    pathwidth = pd.read_csv(pathwidth_csv, dtype={"pw": pd.Int32Dtype()})
    pathwidth = pathwidth.drop_duplicates()
    pathwidth = pathwidth.pivot(index="graph_name", columns="type")

    pathwidth.columns = [f"{x}_{y}" for x, y in pathwidth.columns]
    pathwidth = pathwidth.reset_index()

    data = data.merge(pathwidth, how="left", on="graph_name")

    opt_time = pd.read_csv(
        pathwidth_runs_opt_csv, dtype={"maximum_resident_set_size": pd.Int32Dtype()}
    )
    heur_time = pd.read_csv(
        pathwidth_runs_heur_csv, dtype={"maximum_resident_set_size": pd.Int32Dtype()}
    )

    opt_time = opt_time.query("exit_status == 0")
    heur_time = heur_time.query("exit_status == 0")

    opt_time = opt_time.rename(
        columns={
            "cpu_time": "cpu_time_opt_preprocess",
            "wallclock_time": "wallclock_time_opt_preprocess",
            "maximum_resident_set_size": "max_memory_opt_preprocess",
        }
    )
    heur_time = heur_time.rename(
        columns={
            "cpu_time": "cpu_time_heur_preprocess",
            "wallclock_time": "wallclock_time_heur_preprocess",
            "maximum_resident_set_size": "max_memory_heur_preprocess",
        }
    )

    data = data.merge(opt_time, how="left", on="graph_name")
    data = data.merge(heur_time, how="left", on="graph_name")

    data["solved?_opt_preprocess"] = (
        data["graph_name"].isin(opt_time["graph_name"]).astype(int)
    )
    data["solved?_heur_preprocess"] = (
        data["graph_name"].isin(heur_time["graph_name"]).astype(int)
    )

    # these columns are described in README.md
    data = data[
        [
            "graph_name",
            "vertices",
            "edges",
            "dat_file",
            "tokens",
            "independent_sets",
            "reconfiguration_sequence_length",
            "pw_opt",
            "pw_heur",
            "pw_orig",
            "cpu_time_opt",
            "cpu_time_heur",
            "cpu_time_orig",
            "wallclock_time_opt",
            "wallclock_time_heur",
            "wallclock_time_orig",
            "max_memory_opt",
            "max_memory_heur",
            "max_memory_orig",
            "zdd_time_opt",
            "zdd_time_heur",
            "zdd_time_orig",
            "zdd_size_opt",
            "zdd_size_heur",
            "zdd_size_orig",
            "solved?_opt",
            "solved?_heur",
            "solved?_orig",
            "error_opt",
            "error_heur",
            "error_orig",
            "cpu_time_opt_preprocess",
            "cpu_time_heur_preprocess",
            "wallclock_time_opt_preprocess",
            "wallclock_time_heur_preprocess",
            "max_memory_opt_preprocess",
            "max_memory_heur_preprocess",
            "solved?_opt_preprocess",
            "solved?_heur_preprocess",
        ]
    ]

    data.to_csv(out_csv, index=False)
    print("wrote", out_csv)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_long",
        type=str,
        help="long-form csv to read from",
    )
    parser.add_argument(
        "output_wide",
        type=str,
        help="output wide-form csv",
    )
    parser.add_argument(
        "--pathwidth_csv",
        type=str,
        default="../make_associated_pathwidth/pathwidth_of_ordering.csv",
    )
    parser.add_argument(
        "--pathwidth_runs_opt_csv",
        type=str,
        default="../parse_pathwidth_logs/pathwidth_opt_time.csv",
    )
    parser.add_argument(
        "--pathwidth_runs_heur_csv",
        type=str,
        default="../parse_pathwidth_logs/pathwidth_heur_time.csv",
    )
    parser.add_argument(
        "--master_db_csv",
        type=str,
        default="../make_masterdb/master-db.csv",
    )

    args = parser.parse_args()

    long_to_wide_with_pw(
        args.input_long,
        args.output_wide,
        args.pathwidth_csv,
        args.pathwidth_runs_opt_csv,
        args.pathwidth_runs_heur_csv,
        args.master_db_csv,
    )
