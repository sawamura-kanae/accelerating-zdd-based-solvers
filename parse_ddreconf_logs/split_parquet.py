# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pyarrow>=24.0.0",
# ]
# ///

# split parquet files so GitHub doesn't choke

import pyarrow.parquet as pq


def split():
    shortest = pq.read_table("shortest.parquet")

    pq.write_to_dataset(
        shortest.select(["graph_name", "dat_file", "zdd_nodes", "type"]),
        "shortest/zdd_nodes",
        partition_cols=["type"],
        basename_template="{i}.parquet",
    )
    pq.write_to_dataset(
        shortest.select(["graph_name", "dat_file", "step_times", "type"]),
        "shortest/step_times",
        partition_cols=["type"],
        basename_template="{i}.parquet",
    )

    farthest = pq.read_table("farthest.parquet")

    pq.write_to_dataset(
        farthest.select(["graph_name", "dat_file", "zdd_nodes", "type"]),
        "farthest/zdd_nodes",
        partition_cols=["type"],
        basename_template="{i}.parquet",
    )
    pq.write_to_dataset(
        farthest.select(["graph_name", "dat_file", "step_times", "type"]),
        "farthest/step_times",
        partition_cols=["type"],
        basename_template="{i}.parquet",
    )


def main() -> None:
    split()


if __name__ == "__main__":
    main()
