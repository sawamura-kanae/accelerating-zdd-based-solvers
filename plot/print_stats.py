# prints stats for the paper text

import pandas as pd, pandas.testing as tm
import numpy as np
import os.path

import util


def columns_heur_to_gree(df):
    df.columns = [x.replace("heur", "gree") for x in df.columns]
    return df


def columns_ref_to_fallback(df):
    df.columns = [x.replace("ref", "fb") for x in df.columns]
    return df


def spearman_corr(x, y):
    x_rank = x.rank(method="min", ascending=False)
    y_rank = y.rank(method="min", ascending=False)
    return (np.cov(x_rank, y_rank) / (np.std(x_rank) * np.std(y_rank)))[0, -1]


def main() -> None:
    print("(greefb means gree with fallback)")
    print()

    time_ref = "wallclock_time"
    solve_time_min = 30
    solve_time = solve_time_min * 60

    shortest_wide = pd.read_csv(util.SHORTEST_WIDE, dtype=util.DTYPE)
    farthest_wide = pd.read_csv(util.FARTHEST_WIDE, dtype=util.DTYPE)

    shortest_wide = util.add_ref(shortest_wide)
    farthest_wide = util.add_ref(farthest_wide)

    shortest_wide = columns_heur_to_gree(shortest_wide)
    farthest_wide = columns_heur_to_gree(farthest_wide)

    shortest_wide = columns_ref_to_fallback(shortest_wide)
    farthest_wide = columns_ref_to_fallback(farthest_wide)

    q = lambda t: f"total_{time_ref}_{t} <= @solve_time and `solved?_{t}` == 1"
    for typ in ["opt", "greefb", "orig"]:
        shortest_wide[f"solved{solve_time_min}_{typ}"] = shortest_wide.eval(q(typ))
        farthest_wide[f"solved{solve_time_min}_{typ}"] = farthest_wide.eval(q(typ))

    q = f"`solved?_opt_preprocess` == 1 and {time_ref}_opt_preprocess <= 60 * 60"
    shortest_wide["opt_available?"] = shortest_wide.eval(q)
    farthest_wide["opt_available?"] = farthest_wide.eval(q)

    # common stats are the same
    common = [
        "graph_name",
        "dat_file",
        "vertices",
        "edges",
        "pw_opt",
        "pw_gree",
        "pw_orig",
        "solved?_opt_preprocess",
        "solved?_gree_preprocess",
    ]
    tm.assert_frame_equal(shortest_wide[common], farthest_wide[common])

    print("## IV. A., B.")
    print(
        "total:",
        shortest_wide["graph_name"].nunique(),
        "graphs,",
        shortest_wide["dat_file"].nunique(),
        "instances",
    )

    opt_available_shortest = shortest_wide.query("`opt_available?` == 1")

    print(
        "opt-available:",
        opt_available_shortest["graph_name"].nunique(),
        "graphs,",
        opt_available_shortest["dat_file"].nunique(),
        "instances",
    )

    print()
    print("table I:")
    table1 = opt_available_shortest
    table1["|V|"] = pd.cut(
        table1["vertices"],
        [-1, 50, 100, 200, 500, 1000],
        labels=["≤50", "51–100", "101–200", "201–500", "501–1000"],
    )
    table1_agg = table1.groupby("|V|").agg(
        **{
            "#graphs": ("graph_name", "nunique"),
            "#inst.": ("dat_file", "size"),
            "|E| min": ("edges", "min"),
            "|E| max": ("edges", "max"),
            "pw(G) min": ("pw_opt", "min"),
            "pw(G) max": ("pw_opt", "max"),
        }
    )
    table1_pw_med = (
        table1.drop_duplicates("graph_name")
        .groupby("|V|")
        .agg(**{"pw(G) md": ("pw_opt", "median")})
    )
    table1_agg = table1_agg.reset_index()
    table1_pw_med = table1_pw_med.reset_index()
    table1 = table1_agg.merge(table1_pw_med, how="left", on="|V|")
    print(table1.to_string(index=False))

    print()
    print("queen200x200:")
    queen200x200_inst = shortest_wide.query("graph_name == 'queen200x200'")
    print(
        queen200x200_inst[
            ["graph_name", "vertices", "edges", "solved?_gree_preprocess"]
        ]
        .iloc[0]
        .to_string()
    )

    print(
        "gree is computed on other",
        shortest_wide.drop_duplicates("graph_name")["solved?_gree_preprocess"].sum(),
        "graphs",
    )

    print()
    width_gree_worse = shortest_wide.query("pw_gree > pw_orig")
    # width of gree of queen200x200 is defined as $\infty$
    print(
        "gree width > orig width for",
        width_gree_worse["graph_name"].nunique(),
        "graphs + queen200x200",
    )
    print(
        "the number of instances are",
        width_gree_worse["dat_file"].nunique(),
        "+",
        queen200x200_inst["dat_file"].nunique(),
    )

    width_gree_worse_opt_available = width_gree_worse.query("`opt_available?` == 1")
    print(
        "opt is available for",
        width_gree_worse_opt_available["graph_name"].nunique(),
        "graphs,",
        width_gree_worse_opt_available["dat_file"].nunique(),
        "instances",
    )

    print()
    print("median width on opt-available:")
    opt_available_shortest_graphs = opt_available_shortest.drop_duplicates("graph_name")
    print(
        opt_available_shortest_graphs.filter(like="pw_")
        .drop(columns="pw_greefb")
        .agg("median")
        .to_string()
    )

    print(
        "opt width == gree width for",
        (
            opt_available_shortest_graphs["pw_opt"]
            == opt_available_shortest_graphs["pw_gree"]
        ).sum(),
        "graphs",
    )

    print()
    print("on opt-available graphs:")
    print(
        opt_available_shortest_graphs.agg(
            {
                f"{time_ref}_gree_preprocess": ["median", "max"],
                f"{time_ref}_opt_preprocess": ["median", "max"],
            }
        )
    )

    print()
    print("## IV. C. Solved Instances")
    print("table II:")
    opt_available_farthest = farthest_wide.query(
        "graph_name in @opt_available_shortest['graph_name']"
    )

    q = f"`solved?_opt_preprocess` == 0 or {time_ref}_opt_preprocess > 60 * 60"
    opt_missing_shortest = shortest_wide.query(q)
    opt_missing_farthest = farthest_wide.query(q)

    table2_opt_missing_shortest = opt_missing_shortest
    table2_opt_missing_farthest = opt_missing_farthest

    table2_opt_available_shortest = opt_available_shortest
    table2_opt_available_farthest = opt_available_farthest

    print("shortest opt-available")
    print(
        table2_opt_available_shortest.filter(like=f"solved{solve_time_min}_")
        .sum()
        .to_string()
    )

    print()
    print("farthest opt-available")
    print(
        table2_opt_available_farthest.filter(like=f"solved{solve_time_min}_")
        .sum()
        .to_string()
    )

    print()
    print("shortest opt-missing")
    print(
        table2_opt_missing_shortest.filter(like=f"solved{solve_time_min}_")
        .drop(columns=f"solved{solve_time_min}_opt")
        .sum()
        .to_string()
    )

    print()
    print("farthest opt-missing")
    print(
        table2_opt_missing_farthest.filter(like=f"solved{solve_time_min}_")
        .drop(columns=f"solved{solve_time_min}_opt")
        .sum()
        .to_string()
    )

    print()
    print("a) opt-available instances")
    print("'every instance solved under orig is also solved under gree'")
    q = f"`solved{solve_time_min}_orig` == 1 and `solved{solve_time_min}_greefb` != 1"
    print(
        "conversely, the number of instances solved in orig but not gree is",
        len(table2_opt_available_shortest.query(q)),
        "for shortest, and",
        len(table2_opt_available_farthest.query(q)),
        "for farthest",
    )
    print("'every instance solved under gree is also solved under opt'")
    q = f"`solved{solve_time_min}_greefb` == 1 and `solved{solve_time_min}_opt` != 1"
    print(
        "conversely, the number of instances solved in gree but not opt is",
        len(table2_opt_available_shortest.query(q)),
        "for shortest, and",
        len(table2_opt_available_farthest.query(q)),
        "for farthest",
    )

    print()
    print("b) opt-missing instances")
    print("'every instance solved under orig is also solved under gree'")
    q = f"`solved{solve_time_min}_orig` == 1 and `solved{solve_time_min}_greefb` != 1"
    print(
        "conversely, the number of instances solved in orig but not gree is",
        len(table2_opt_missing_shortest.query(q)),
        "for shortest, and",
        len(table2_opt_missing_farthest.query(q)),
        "for farthest",
    )

    print()
    print("c) Nesting across variants")
    print(
        "'every instance solved on the farthest variant is also solved on the shortest one'"
    )
    print(
        "conversely, the number of instances solved on farthest but not shortest is",
        (
            farthest_wide.query(f"solved{solve_time_min}_orig == 1")["dat_file"].isin(
                shortest_wide.query(f"solved{solve_time_min}_orig != 1")["dat_file"]
            )
        ).sum(),
        "in orig,",
        (
            farthest_wide.query(f"solved{solve_time_min}_greefb == 1")["dat_file"].isin(
                shortest_wide.query(f"solved{solve_time_min}_greefb != 1")["dat_file"]
            )
        ).sum(),
        "in gree, and",
        (
            farthest_wide.query(f"solved{solve_time_min}_opt == 1")["dat_file"].isin(
                shortest_wide.query(f"solved{solve_time_min}_opt != 1")["dat_file"]
            )
        ).sum(),
        "in opt",
    )

    q = f"solved{solve_time_min}_orig == 0 and \
            (solved{solve_time_min}_greefb == 1 or solved{solve_time_min}_opt == 1)"
    table3_flipped_shortest = shortest_wide.query(q)
    table3_flipped_farthest = farthest_wide.query(q)

    cols = [
        "graph_name",
        "dat_file",
        "vertices",
        "edges",
        "pw_orig",
        "pw_greefb",
        "pw_opt",
        f"solved{solve_time_min}_greefb",
        f"solved{solve_time_min}_opt",
        "opt_available?",
    ]

    table3_flipped_shortest = table3_flipped_shortest[cols]
    table3_flipped_farthest = table3_flipped_farthest[cols]

    table3_flipped_shortest = table3_flipped_shortest.set_index("dat_file")
    table3_flipped_farthest = table3_flipped_farthest.set_index("dat_file")

    table3_flipped_shortest, table3_flipped_farthest = table3_flipped_shortest.align(
        table3_flipped_farthest, join="inner"
    )
    table3 = table3_flipped_shortest[
        table3_flipped_shortest.eq(table3_flipped_farthest).min(axis=1)
    ]

    table3 = table3.groupby("graph_name").agg(
        **{
            "|V|": ("vertices", "first"),
            "|E|": ("edges", "first"),
            "orig": ("pw_orig", "first"),
            "gree": ("pw_greefb", "first"),
            "opt": ("pw_opt", "first"),
            "#flip": ("vertices", "size"),
            "solved opt": (f"solved{solve_time_min}_opt", "max"),
            "solved gree": (f"solved{solve_time_min}_greefb", "max"),
            "opt-available": ("opt_available?", "first"),
        }
    )

    table3["solved gree, opt"] = table3["solved opt"] & table3["solved gree"]
    table3["solved opt"] = table3["solved opt"] ^ table3["solved gree, opt"]
    table3["solved gree"] = table3["solved gree"] ^ table3["solved gree, opt"]

    cols = table3.filter(like="solved ").columns
    table3["solved by"] = pd.from_dummies(table3[cols])
    table3["solved by"] = table3["solved by"].str[len("solved ") :]
    table3 = table3.drop(columns=cols)

    # looks like sorted by pw_orig?
    table3 = table3.sort_values("orig", ascending=False)

    table3_opt_available = table3[table3["opt-available"]].drop(columns="opt-available")
    table3_opt_missing = table3[~table3["opt-available"]].drop(columns="opt-available")

    print()
    print("table III")
    print(table3_opt_available.to_string())
    print("-------------------------------------------------------------------------")
    print(table3_opt_missing.to_string())

    print()
    print("## V. A.")
    print("table IV")

    def geometric_mean(v):
        return np.exp(np.log(v).mean())

    q = f"solved{solve_time_min}_opt == 1 \
            and solved{solve_time_min}_greefb == 1 \
            and solved{solve_time_min}_orig == 1"
    table4_shortest = shortest_wide.query(q)
    table4_farthest = farthest_wide.query(q)

    stubs = ["pw", "zdd_size", "zdd_time", time_ref, "max_memory"]
    table4_shortest = pd.wide_to_long(
        table4_shortest, i="dat_file", j="type", stubnames=stubs, sep="_", suffix=r"\w+"
    )
    table4_shortest = table4_shortest.loc[(slice(None), ["opt", "greefb", "orig"]), :]

    table4_farthest = pd.wide_to_long(
        table4_farthest, i="dat_file", j="type", stubnames=stubs, sep="_", suffix=r"\w+"
    )
    table4_farthest = table4_farthest.loc[(slice(None), ["opt", "greefb", "orig"]), :]

    for name, df in [("shortest", table4_shortest), ("farthest", table4_farthest)]:
        df["max_memory"] = df["max_memory"] / 1024
        df = df[stubs].groupby(level="type").agg([geometric_mean, "max"])
        df = df.loc[["orig", "greefb", "opt"]]
        print()
        print(name)
        print(df.to_string())

    # talking about shortest

    print()
    print("Spearman correlation between width and ZDD size")
    print(
        "shortest",
        spearman_corr(table4_shortest["pw"], table4_shortest["zdd_size"]),
    )

    q = f"solved{solve_time_min}_opt == 1 \
            and solved{solve_time_min}_greefb == 1 \
            and solved{solve_time_min}_orig == 1"
    shortest_common = shortest_wide.query(q)
    print()
    print("ZDD size opt > orig:")
    a = (
        shortest_common["zdd_size_opt"] > shortest_common["zdd_size_orig"]
    ).sum() / len(shortest_common)
    print("shortest", f"{a:%}")
    a = (
        (shortest_common["zdd_size_opt"] - shortest_common["zdd_size_orig"])
        / shortest_common["zdd_size_opt"]
    ).max()
    print(f"{a:%}", "in size")
    a = (shortest_common["zdd_size_opt"] - shortest_common["zdd_size_orig"]).max()
    print(a, "in absolute terms")
    a = shortest_common.query("zdd_size_opt > zdd_size_orig")["zdd_size_orig"].max()
    print("at most", a, "nodes under orig")
    print("range of ZDD nodes under orig:")
    print(shortest_common["zdd_size_orig"].agg(["min", "max"]).to_string())

    shortest_zdd = pd.read_parquet(
        os.path.join(util.PARQUET_PARENT, "shortest", "zdd_nodes"),
        columns=["dat_file", "zdd_nodes", "type"],
        filters=[("dat_file", "in", shortest_common["dat_file"])],
    )
    shortest_zdd = shortest_zdd.drop_duplicates(["dat_file", "type"])
    shortest_zdd = shortest_zdd.pivot(index="dat_file", columns="type")
    shortest_zdd.columns = [
        x if y == "" else f"{x}_{y}" for x, y in shortest_zdd.columns
    ]

    shortest_zdd = columns_heur_to_gree(shortest_zdd)

    shortest_common_zdd = shortest_common.merge(shortest_zdd, on="dat_file", how="left")
    shortest_common_zdd["zdd_nodes_greefb"] = shortest_common_zdd[
        "zdd_nodes_gree"
    ].mask(
        shortest_common_zdd["pw_gree"] > shortest_common_zdd["pw_orig"],
        shortest_common_zdd["zdd_nodes_orig"],
    )
    for typ in ["opt", "greefb", "orig"]:
        # nonempty, not nan
        shortest_common_zdd[f"max|Zi|_{typ}"] = shortest_common_zdd[
            f"zdd_nodes_{typ}"
        ].map(np.max)

    shortest_common_zdd["shrink Zsol"] = (
        shortest_common_zdd["zdd_size_orig"] / shortest_common_zdd["zdd_size_opt"]
    )
    shortest_common_zdd["shrink max|Zi|"] = (
        shortest_common_zdd["max|Zi|_orig"] / shortest_common_zdd["max|Zi|_opt"]
    )

    print()
    print("## B.")
    print("Spearman correlation between shrink factor of (Zsol, peak |Zi|)")
    print(
        "shortest",
        spearman_corr(
            shortest_common_zdd["shrink Zsol"], shortest_common_zdd["shrink max|Zi|"]
        ),
    )
    print()
    print(shortest_common_zdd.filter(like="shrink").agg([geometric_mean]))
    a = (
        shortest_common_zdd["shrink max|Zi|"] <= shortest_common_zdd["shrink Zsol"]
    ).sum() / len(shortest_common_zdd)
    print()
    print("second-phase factor ≤ first-phase factor on", f"{a:%}", "of the instances")

    print()
    print(
        "on shrink factor of Zsol ≥ 10, median of shrink factor of max |Zi| is",
        shortest_common_zdd.query("`shrink Zsol` >= 10")["shrink max|Zi|"].median(),
    )

    print()
    print(
        shortest_common_zdd.query("dat_file == 'mug88_1_02'")
        .set_index("dat_file")[
            [
                "pw_orig",
                "pw_greefb",
                "pw_opt",
                "max|Zi|_orig",
                "max|Zi|_greefb",
                "max|Zi|_opt",
            ]
        ]
        .to_string()
    )

    shortest_yes = shortest_wide.query(
        f"(solved{solve_time_min}_opt == 1 \
            or solved{solve_time_min}_greefb == 1 \
            or solved{solve_time_min}_orig == 1) \
            and reconfiguration_sequence_length > 0"
    )
    print()
    print("## C.")
    print("range of ℓ, shortest")
    print(
        shortest_yes["reconfiguration_sequence_length"].agg(["min", "max"]).to_string()
    )

    shortest_gree = shortest_wide.query(f"solved{solve_time_min}_greefb == 1")
    print()
    print("width of ℓ ≥ 100, shortest")
    print(
        shortest_gree.query("reconfiguration_sequence_length >= 100")["pw_greefb"]
        .agg(["max", "median"])
        .to_string()
    )
    print()
    print("'no instance of large width reaches such length'")
    a = shortest_gree.query("reconfiguration_sequence_length >= 100")["pw_greefb"].max()
    print(
        "instances of larger widths have reached ℓ ≤",
        shortest_gree.query("pw_greefb > @a")["reconfiguration_sequence_length"].max(),
    )


if __name__ == "__main__":
    main()
