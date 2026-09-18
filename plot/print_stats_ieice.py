# print stats for paper text

import pandas as pd, pandas.testing as tm
import numpy as np
import os.path
import functools
from scipy import stats

import util


def columns_heur_to_gree(df):
    df.columns = [x.replace("heur", "gree") for x in df.columns]
    return df


def columns_ref_to_fallback(df):
    df.columns = [x.replace("ref", "fb") for x in df.columns]
    return df


def geometric_mean(v):
    return np.exp(np.log(v).mean())


def main() -> None:
    print("(greefb means gree with fallback)")
    print()

    time_ref = "wallclock_time"
    solve_time_min = 30
    solve_time = solve_time_min * 60

    decom_cat_dtype = pd.CategoricalDtype(
        categories=["orig", "greefb", "opt"],
        ordered=True,
    )
    variant_cat_dtype = pd.CategoricalDtype(
        categories=["shortest", "farthest"], ordered=True
    )

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

    print("## 4.1 Experimental Setup")
    print()
    print("### Benchmarks.")
    print()
    print(
        "total:",
        shortest_wide["dat_file"].nunique(),
        "instances, drawn from",
        shortest_wide["graph_name"].nunique(),
        "graphs",
    )

    graphs = shortest_wide.drop_duplicates("graph_name")
    print()
    print(graphs["vertices"].agg(["min", "max", "median"]).to_markdown())
    print()
    print(graphs["edges"].agg(["min", "max", "median"]).to_markdown())

    print()
    print("## 4.2 Input Graphs and Widths of the Three Decompositions")
    print()

    opt_available_shortest = shortest_wide.query("`opt_available?` == 1")

    print(
        "opt was obtained for",
        opt_available_shortest["graph_name"].nunique(),
        "graphs,",
        opt_available_shortest["dat_file"].nunique(),
        "instances",
    )

    print()
    print("**table 1**:")
    print()
    print("all graphs")
    table1 = shortest_wide
    # https://github.com/astanin/python-tabulate/commit/e6a24aa6e00ca8ce9a1987f28c11ca08c6f19383
    # sad
    table1["\\|V\\|"] = pd.cut(
        table1["vertices"],
        [-1, 50, 100, 200, 500, 1000, np.inf],
        labels=["≤50", "51–100", "101–200", "201–500", "501–1000", ">1000"],
    )
    table1 = table1.groupby("\\|V\\|", observed=False).agg(
        **{
            "#graphs": ("graph_name", "nunique"),
            "#inst.": ("dat_file", "size"),
        }
    )
    table1 = table1.reset_index()
    print()
    print(table1.to_markdown(index=False))

    print()
    print("opt-available graphs")
    table1 = opt_available_shortest
    table1["\\|V\\|"] = pd.cut(
        table1["vertices"],
        [-1, 50, 100, 200, 500, 1000, np.inf],
        labels=["≤50", "51–100", "101–200", "201–500", "501–1000", ">1000"],
    )
    table1_agg = table1.groupby("\\|V\\|", observed=False).agg(
        **{
            "#graphs": ("graph_name", "nunique"),
            "#inst.": ("dat_file", "size"),
            "pw(G) min": ("pw_opt", "min"),
            "pw(G) max": ("pw_opt", "max"),
        }
    )
    table1_pw_med = (
        table1.drop_duplicates("graph_name")
        .groupby("\\|V\\|", observed=False)
        .agg(**{"pw(G) median": ("pw_opt", "median")})
    )
    table1_agg = table1_agg.reset_index()
    table1_pw_med = table1_pw_med.reset_index()
    table1 = table1_agg.merge(table1_pw_med, how="left", on="\\|V\\|")
    print()
    print(table1.to_markdown(index=False))

    print()
    print(
        "gree is computed on",
        shortest_wide[
            (shortest_wide["solved?_gree_preprocess"] == 1)
            & (shortest_wide[f"{time_ref}_gree_preprocess"] <= 60 * 60)
        ]["graph_name"].nunique(),
        "graphs",
    )

    print()
    print("queen200x200:")
    print()
    queen200x200_inst = shortest_wide.query("graph_name == 'queen200x200'")
    print(
        queen200x200_inst[
            ["graph_name", "vertices", "edges", "solved?_gree_preprocess"]
        ]
        .iloc[0]
        .to_markdown()
    )

    print()
    width_gree_worse = shortest_wide.query("pw_gree > pw_orig")
    # width of gree of queen200x200 is defined as $\infty$
    print(
        "- gree width > orig width for",
        width_gree_worse["graph_name"].nunique(),
        "graphs + queen200x200",
    )
    print(
        "- the number of instances is",
        width_gree_worse["dat_file"].nunique(),
        "+",
        queen200x200_inst["dat_file"].nunique(),
        "(queen200x200)",
    )

    width_gree_worse_opt_available = width_gree_worse.query("`opt_available?` == 1")
    print(
        "  - out of these graphs, opt is available for",
        width_gree_worse_opt_available["graph_name"].nunique(),
        "graphs,",
        width_gree_worse_opt_available["dat_file"].nunique(),
        "instances",
    )

    print()
    print("median width on opt-available:")
    print()
    opt_available_shortest_graphs = opt_available_shortest.drop_duplicates("graph_name")
    print(
        opt_available_shortest_graphs.filter(like="pw_")
        .drop(columns="pw_gree")
        .agg("median")
        .to_markdown()
    )

    print()
    print(
        "opt width == gree width for",
        (
            opt_available_shortest_graphs["pw_opt"]
            == opt_available_shortest_graphs["pw_greefb"]
        ).sum(),
        "graphs",
    )

    print()
    print("on opt-available graphs:")
    print()
    print(
        opt_available_shortest_graphs.agg(
            {
                f"{time_ref}_gree_preprocess": ["median", "max"],
                f"{time_ref}_opt_preprocess": ["median", "max"],
            }
        )
        .round(1)
        .to_markdown()
    )

    num_opt_available_within_10sec = (
        opt_available_shortest_graphs[f"{time_ref}_opt_preprocess"] < 10
    ).sum()
    print()
    print(
        f"{num_opt_available_within_10sec / len(opt_available_shortest_graphs):.0%}",
        "finish within 10 sec",
    )

    opt_available_farthest = farthest_wide.query(
        "graph_name in @opt_available_shortest['graph_name']"
    )

    q = f"`solved?_opt_preprocess` != 1 or {time_ref}_opt_preprocess > 60 * 60"
    opt_missing_shortest = shortest_wide.query(q)
    opt_missing_farthest = farthest_wide.query(q)

    print()
    print(
        "opt not computed:",
        opt_missing_shortest["graph_name"].nunique(),
        "graphs,",
        opt_missing_shortest["dat_file"].nunique(),
        "instances",
    )

    opt_missing_shortest_graphs = opt_missing_shortest.drop_duplicates("graph_name")

    # remove fallback that's already applied
    queen_index = opt_missing_shortest_graphs.query(
        "graph_name == 'queen200x200'"
    ).index
    opt_missing_shortest_graphs.loc[queen_index, "pw_greefb"] = np.nan

    print()
    print("**table 2**:")
    print()
    print("opt-available:")
    print()
    print(
        opt_available_shortest_graphs.filter(like="pw_")
        .drop(columns="pw_gree")
        .quantile([0.5, 0.25, 0.75])[["pw_orig", "pw_greefb", "pw_opt"]]
        .round()
        .transpose()
        .to_markdown()
    )
    print()
    print("opt-missing:")
    print()
    print(
        opt_missing_shortest_graphs.filter(like="pw_")
        .drop(columns="pw_gree")
        .quantile([0.5, 0.25, 0.75])[["pw_orig", "pw_greefb", "pw_opt"]]
        .round()
        .transpose()
        .to_markdown()
    )

    print()
    print(
        "- on opt-available graphs, gree width ≤ 20:",
        (opt_available_shortest_graphs["pw_greefb"] <= 20).sum(),
        "graphs",
    )
    print(
        "- on opt-missing graphs, gree width ≤ 20:",
        (opt_missing_shortest_graphs["pw_greefb"] <= 20).sum(),
        "graphs",
    )

    print()
    print("## 4.3 Solved Instances")

    print()
    print("**table 3**:")
    solved_within_time_cols = [
        f"solved{solve_time_min}_opt",
        f"solved{solve_time_min}_greefb",
        f"solved{solve_time_min}_orig",
    ]
    table3_shortest = shortest_wide.melt(
        id_vars=["dat_file", "opt_available?"], value_vars=solved_within_time_cols
    )
    table3_shortest["problem"] = "shortest"
    table3_farthest = farthest_wide.melt(
        id_vars=["dat_file", "opt_available?"], value_vars=solved_within_time_cols
    )
    table3_farthest["problem"] = "farthest"
    table3 = pd.concat([table3_shortest, table3_farthest])

    table3["variable"] = (
        table3["variable"]
        .str[len(f"solved{solve_time_min}_") :]
        .astype(decom_cat_dtype)
    )
    table3["problem"] = table3["problem"].astype(variant_cat_dtype)
    table3["opt_available?"] = pd.Categorical(
        np.where(table3["opt_available?"], "opt-available", "opt-missing"),
        categories=["opt-available", "opt-missing"],
        ordered=True,
    )

    table3 = table3.groupby(["opt_available?", "problem", "variable"])["value"].sum()
    table3 = table3.reset_index()
    table3 = table3.pivot(
        index="variable", columns=["opt_available?", "problem"], values="value"
    )

    print()
    print("```")
    print(table3.to_string())
    print("```")

    table3["opt-available"] = (
        table3["opt-available"] / len(opt_available_shortest) * 100
    )
    table3["opt-missing"] = table3["opt-missing"] / len(opt_missing_shortest) * 100

    print()
    print("percentages:")
    print()
    print("```")
    print(table3.round(1).to_string())
    print("```")

    print()
    print("### Effects of choosing decompositions.")

    print()
    print("the solved sets are nested:")
    print()
    print("on opt-available instances:")
    print("- _every instance solved under orig is also solved under gree_")
    q = f"`solved{solve_time_min}_orig` == 1 and `solved{solve_time_min}_greefb` != 1"
    print(
        "  - conversely, the number of instances solved in orig but not gree is",
        len(opt_available_shortest.query(q)),
        "for shortest, and",
        len(opt_available_farthest.query(q)),
        "for farthest",
    )
    print("- _every instance solved under gree is also solved under opt_")
    q = f"`solved{solve_time_min}_greefb` == 1 and `solved{solve_time_min}_opt` != 1"
    print(
        "  - conversely, the number of instances solved in gree but not opt is",
        len(opt_available_shortest.query(q)),
        "for shortest, and",
        len(opt_available_farthest.query(q)),
        "for farthest",
    )

    print()
    print("on opt-missing instances:")
    print("- _every instance solved under orig is also solved under gree_")
    q = f"`solved{solve_time_min}_orig` == 1 and `solved{solve_time_min}_greefb` != 1"
    print(
        "  - conversely, the number of instances solved in orig but not gree is",
        len(opt_missing_shortest.query(q)),
        "for shortest, and",
        len(opt_missing_farthest.query(q)),
        "for farthest",
    )
    print("- (opt is not obtained)")

    print()
    print("### Nesting across variants.")

    print()
    print(
        "- 'every instance solved on the farthest variant is also solved on the shortest one'"
    )
    print(
        "  - conversely, the number of instances solved on farthest but not shortest is",
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

    print()
    print("### Width for the flipped instances.")

    q = f"solved{solve_time_min}_orig == 0 and \
            (solved{solve_time_min}_greefb == 1 or solved{solve_time_min}_opt == 1)"
    table4_flipped_shortest = shortest_wide.query(q)
    table4_flipped_farthest = farthest_wide.query(q)

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

    table4_flipped_shortest = table4_flipped_shortest[cols]
    table4_flipped_farthest = table4_flipped_farthest[cols]

    table4_flipped_shortest = table4_flipped_shortest.set_index("dat_file")
    table4_flipped_farthest = table4_flipped_farthest.set_index("dat_file")

    table5_flipped_shortest = table4_flipped_shortest
    table5_flipped_farthest = table4_flipped_farthest

    table4_flipped_shortest, table4_flipped_farthest = table4_flipped_shortest.align(
        table4_flipped_farthest, join="inner"
    )
    table4 = table4_flipped_shortest[
        table4_flipped_shortest.eq(table4_flipped_farthest).min(axis=1)
    ]
    table5_table4_dat = table4

    table4 = table4.groupby("graph_name").agg(
        **{
            "\\|V\\|": ("vertices", "first"),
            "\\|E\\|": ("edges", "first"),
            "orig": ("pw_orig", "first"),
            "gree": ("pw_greefb", "first"),
            "opt": ("pw_opt", "first"),
            "#flip": ("vertices", "size"),
            "solved opt": (f"solved{solve_time_min}_opt", "max"),
            "solved gree": (f"solved{solve_time_min}_greefb", "max"),
            "opt-available": ("opt_available?", "first"),
        }
    )

    table4["solved gree, opt"] = table4["solved opt"] & table4["solved gree"]
    table4["solved opt"] = table4["solved opt"] ^ table4["solved gree, opt"]
    table4["solved gree"] = table4["solved gree"] ^ table4["solved gree, opt"]

    cols = table4.filter(like="solved ").columns
    table4["solved by"] = pd.from_dummies(table4[cols])
    table4["solved by"] = table4["solved by"].str[len("solved ") :]
    table4 = table4.drop(columns=cols)

    # looks like sorted by pw_orig?
    table4 = table4.sort_values("orig", ascending=False)

    table4_opt_available = table4[table4["opt-available"]].drop(columns="opt-available")
    table4_opt_missing = table4[~table4["opt-available"]].drop(columns="opt-available")

    print()
    print("**table 4**:")
    print()
    print(table4_opt_available.to_markdown())
    print()
    print(table4_opt_missing.to_markdown())

    table5_mask = functools.reduce(
        lambda x, y: x | (shortest_wide[y] != farthest_wide[y]),
        solved_within_time_cols,
        initial=False,
    )

    table5 = (
        shortest_wide[table5_mask]
        .join(farthest_wide[table5_mask][solved_within_time_cols], rsuffix=" farthest")
        .groupby("graph_name")
        .agg(
            **{
                "\\|V\\|": ("vertices", "first"),
                "\\|E\\|": ("edges", "first"),
                "orig": ("pw_orig", "first"),
                "gree": ("pw_greefb", "first"),
                "opt": ("pw_opt", "first"),
                "shortest solved orig": (f"solved{solve_time_min}_orig", "max"),
                "shortest solved opt": (f"solved{solve_time_min}_opt", "max"),
                "shortest solved gree": (f"solved{solve_time_min}_greefb", "max"),
                "farthest solved orig": (
                    f"solved{solve_time_min}_orig farthest",
                    "max",
                ),
                "farthest solved opt": (f"solved{solve_time_min}_opt farthest", "max"),
                "farthest solved gree": (
                    f"solved{solve_time_min}_greefb farthest",
                    "max",
                ),
                "opt-available": ("opt_available?", "first"),
            }
        )
    )

    table5["shortest solved orig, gree, opt"] = functools.reduce(
        lambda x, y: x & table5[y],
        [f"shortest solved {typ}" for typ in ["orig", "opt", "gree"]],
        initial=True,
    )
    table5["shortest solved orig"] = (
        table5["shortest solved orig"] ^ table5["shortest solved orig, gree, opt"]
    )
    table5["shortest solved gree"] = (
        table5["shortest solved gree"] ^ table5["shortest solved orig, gree, opt"]
    )
    table5["shortest solved opt"] = (
        table5["shortest solved opt"] ^ table5["shortest solved orig, gree, opt"]
    )

    table5["shortest solved gree, opt"] = functools.reduce(
        lambda x, y: x & table5[y],
        [f"shortest solved {typ}" for typ in ["opt", "gree"]],
        initial=True,
    )
    table5["shortest solved gree"] = (
        table5["shortest solved gree"] ^ table5["shortest solved gree, opt"]
    )
    table5["shortest solved opt"] = (
        table5["shortest solved opt"] ^ table5["shortest solved gree, opt"]
    )

    table5["farthest solved gree, opt"] = functools.reduce(
        lambda x, y: x & table5[y],
        [f"farthest solved {typ}" for typ in ["opt", "gree"]],
        initial=True,
    )
    table5["farthest solved gree"] = (
        table5["farthest solved gree"] ^ table5["farthest solved gree, opt"]
    )
    table5["farthest solved opt"] = (
        table5["farthest solved opt"] ^ table5["farthest solved gree, opt"]
    )

    cols = table5.filter(like="shortest solved ").columns
    table5["shortest solved by"] = pd.from_dummies(
        table5[cols], default_category="shortest solved ---"
    )
    table5 = table5.drop(columns=cols)
    table5["shortest solved by"] = table5["shortest solved by"].str[
        len("shortest solved ") :
    ]

    cols = table5.filter(like="farthest solved ").columns
    table5["farthest solved by"] = pd.from_dummies(
        table5[cols], default_category="farthest solved ---"
    )
    table5 = table5.drop(columns=cols)
    table5["farthest solved by"] = table5["farthest solved by"].str[
        len("farthest solved ") :
    ]

    table5 = table5.sort_values("orig", ascending=False)

    print()
    print("**table 5**:")
    print()
    print(
        table5.query("`opt-available` == True")
        .drop(columns="opt-available")
        .to_markdown()
    )
    print()
    print(
        table5.query("`opt-available` == False")
        .drop(columns="opt-available")
        .to_markdown()
    )

    table5_flipped_shortest = table5_flipped_shortest.query(
        "index not in @table5_table4_dat.index"
    )
    table5_flipped_farthest = table5_flipped_farthest.query(
        "index not in @table5_table4_dat.index"
    )

    # parentheses
    print()
    print("shortest flipped:")
    print()
    print(
        table5_flipped_shortest.groupby("graph_name")
        .agg(**{"#flip": ("vertices", "size")})
        .to_markdown()
    )
    print()
    print("farthest flipped:")
    print()
    print(
        table5_flipped_farthest.groupby("graph_name")
        .agg(**{"#flip": ("vertices", "size")})
        .to_markdown()
    )

    gree_w = shortest_wide.query(
        f"not solved{solve_time_min}_orig and solved{solve_time_min}_greefb"
    )

    gree_w_orig_first_finish = gree_w["zdd_time_orig"] <= 30 * 60
    print()
    print("gree solves and orig does not for", len(gree_w), "instances:")
    print()
    print(
        "- on",
        len(gree_w) - (gree_w_orig_first_finish).sum(),
        "instances, orig does not finish the first phase within 30 min",
    )
    print(
        "- out of them, the minimum time taken for the whole search by gree is",
        gree_w[gree_w["zdd_time_orig"].isna() | (gree_w["zdd_time_orig"] > 30 * 60)][
            f"{time_ref}_greefb"
        ].min(),
    )

    print()
    print("# 5. Analyses")
    print()
    print("the range of the size of solution-space ZDD under orig is wide:")
    print()
    print(opt_available_shortest["zdd_size_orig"].agg(["min", "max"]).to_markdown())

    print()
    print("## 5.1 The First Phase: Building the Solution-Space ZDD")

    all_wide = pd.concat(
        [
            shortest_wide.assign(variant="shortest"),
            farthest_wide.assign(variant="farthest"),
        ]
    )
    table6_mask = functools.reduce(
        lambda x, y: x & (all_wide[y]), solved_within_time_cols, initial=True
    )
    table6 = all_wide[table6_mask]

    def melt(x):
        melted = table6.melt(
            id_vars=["dat_file", "variant"],
            value_vars=[f"{x}_{typ}" for typ in ["opt", "greefb", "orig"]],
            var_name="type",
            value_name=x,
        )
        melted["type"] = melted["type"].str[len(f"{x}_") :]
        return melted

    table6_ids = ["dat_file", "type", "variant"]
    table6 = functools.reduce(
        lambda x, y: x.merge(y, how="left", on=table6_ids),
        map(melt, ["pw", "zdd_size"]),
    )

    table6["variant"] = table6["variant"].astype(variant_cat_dtype)
    table6["type"] = table6["type"].astype(decom_cat_dtype)

    shortest_zdd = pd.read_parquet(
        os.path.join(util.PARQUET_PARENT, "shortest", "zdd_nodes"),
        columns=["dat_file", "zdd_nodes", "type"],
        filters=[("dat_file", "in", table6["dat_file"])],
    )
    shortest_zdd = shortest_zdd.drop_duplicates(["dat_file", "type"])
    shortest_zdd["variant"] = "shortest"

    farthest_zdd = pd.read_parquet(
        os.path.join(util.PARQUET_PARENT, "farthest", "zdd_nodes"),
        columns=["dat_file", "zdd_nodes", "type"],
        filters=[("dat_file", "in", table6["dat_file"])],
    )
    farthest_zdd = farthest_zdd.drop_duplicates(["dat_file", "type"])
    farthest_zdd["variant"] = "farthest"

    all_zdd = pd.concat([shortest_zdd, farthest_zdd])
    all_zdd_pivoted = all_zdd.pivot(
        index=["dat_file", "variant"], columns="type", values="zdd_nodes"
    )
    all_zdd_pivoted = all_zdd_pivoted.reset_index()

    gree_fallback_dat = shortest_wide[lambda x: x["pw_gree"] > x["pw_orig"]]["dat_file"]
    all_zdd_fallback_mask = all_zdd_pivoted["dat_file"].isin(gree_fallback_dat)
    all_zdd_pivoted["greefb"] = all_zdd_pivoted["heur"].mask(
        all_zdd_fallback_mask, all_zdd_pivoted["orig"]
    )

    all_zdd = all_zdd_pivoted.melt(
        id_vars=["dat_file", "variant"],
        value_vars=["opt", "greefb", "orig"],
        var_name="type",
        value_name="zdd_nodes",
    )

    table6 = table6.merge(all_zdd, how="left", on=table6_ids)

    assert table6["zdd_nodes"].isna().sum() == 0

    table6["zdd_nodes_peak"] = table6["zdd_nodes"].map(max)
    table6["zdd_nodes_average"] = table6["zdd_nodes"].map(lambda x: x.mean())

    table6["type"] = table6["type"].astype(decom_cat_dtype)
    table6["variant"] = table6["variant"].astype(variant_cat_dtype)

    table6_detail = table6

    table6 = (
        table6.rename(
            columns={
                "pw": "width",
                "zdd_size": "|Zsol|",
                "zdd_nodes_peak": "peak |Zi|",
                "zdd_nodes_average": "average |Zi|",
            }
        )
        .groupby(["variant", "type"])[["width", "|Zsol|", "peak |Zi|", "average |Zi|"]]
        .agg([geometric_mean, "max"])
    )

    print()
    print("**table 6**:")
    print()
    print("```")
    print(
        table6.round(
            {
                ("width", "geometric_mean"): 1,
                ("|Zsol|", "geometric_mean"): 0,
                ("peak |Zi|", "geometric_mean"): 0,
                ("average |Zi|", "geometric_mean"): 0,
                ("average |Zi|", "max"): 0,
            }
        ).to_string()
    )
    print("```")

    stubs = ["zdd_time", time_ref, "max_memory"]
    all_long = pd.wide_to_long(
        all_wide[table6_mask],
        i=["dat_file", "variant"],
        j="type",
        stubnames=stubs,
        sep="_",
        suffix=r"\w+",
    )

    all_long = all_long.loc[(slice(None), slice(None), ["opt", "greefb", "orig"]), :]
    all_long = all_long.reset_index()
    all_long["variant"] = all_long["variant"].astype(variant_cat_dtype)
    all_long["type"] = all_long["type"].astype(decom_cat_dtype)

    all_long["max_memory"] /= 1024
    all_long = all_long.groupby(["variant", "type"])[stubs].agg([geometric_mean, "max"])

    print()
    print("**table 7**:")
    print()
    print("```")
    print(
        all_long.astype(np.float64)
        .round(
            {
                ("zdd_time", "geometric_mean"): 3,
                ("zdd_time", "max"): 1,
                ("wallclock_time", "geometric_mean"): 2,
                ("wallclock_time", "max"): 1,
                ("max_memory", "geometric_mean"): 0,
                ("max_memory", "max"): 0,
            }
        )
        .to_string()
    )
    print("```")

    shortest_all_solved = all_wide[table6_mask].query("variant == 'shortest'")
    corrs = pd.DataFrame(
        [
            stats.spearmanrho(
                shortest_all_solved["pw_orig"], shortest_all_solved["zdd_size_orig"]
            ),
            stats.spearmanrho(
                shortest_all_solved["pw_greefb"], shortest_all_solved["zdd_size_greefb"]
            ),
            stats.spearmanrho(
                shortest_all_solved["pw_opt"], shortest_all_solved["zdd_size_opt"]
            ),
        ],
        columns=["Spearman correlation", "p-value"],
        index=["orig", "greefb", "opt"],
    )
    print()
    print("Spearman correlation between (width, size):")
    print()
    print(corrs.round({"Spearman correlation": 2}).to_markdown())

    print()
    print("opt ZDD size > orig:")
    print()
    a = shortest_all_solved.eval("zdd_size_opt - zdd_size_orig")
    print(f"- on {(a > 0).sum() / len(a):.0%} of the instances")
    print(
        f"- difference is at most {(a / shortest_all_solved['zdd_size_opt']).max():.0%} in size, {a.max()} in absolute terms"
    )
    print(
        f"- at most {shortest_all_solved.query('zdd_size_opt > zdd_size_orig')['zdd_size_orig'].max()} nodes under orig"
    )
    print()
    print("range of the size of ZDD under orig")
    print()
    print(shortest_all_solved["zdd_size_orig"].agg(["min", "max"]).to_markdown())

    print()
    print("## 5.2 The Second Phase: Rebuilding the ZDD at Each Step")
    print()
    shrink_factors = table6_detail.pivot(
        index=["dat_file", "variant"],
        columns="type",
        values=["zdd_size", "zdd_nodes_peak", "zdd_nodes_average"],
    )
    shrink_factors["Zsol"] = (
        shrink_factors["zdd_size", "orig"] / shrink_factors["zdd_size", "opt"]
    )
    shrink_factors["peak Zi"] = (
        shrink_factors["zdd_nodes_peak", "orig"]
        / shrink_factors["zdd_nodes_peak", "opt"]
    )
    shrink_factors["average Zi"] = (
        shrink_factors["zdd_nodes_average", "orig"]
        / shrink_factors["zdd_nodes_average", "opt"]
    )
    shrink_factors = shrink_factors.reset_index()

    corrs = pd.DataFrame(
        [
            stats.spearmanrho(
                shrink_factors[lambda x: x["variant"] == "shortest"]["Zsol"].astype(
                    np.float64
                ),
                shrink_factors[lambda x: x["variant"] == "shortest"]["peak Zi"].astype(
                    np.float64
                ),
            ),
        ],
        columns=["Spearman correlation", "p-value"],
    )
    print()
    print("Spearman correlation between shrink (Zsol, peak Zi):")
    print()
    print(corrs.round({"Spearman correlation": 2}).to_markdown())

    print()
    print(
        shrink_factors[lambda x: x["variant"] == "shortest"][["Zsol", "peak Zi"]]
        .astype(np.float64)
        .agg([geometric_mean])
        .round(1)
        .to_markdown()
    )
    a = (
        shrink_factors[lambda x: x["variant"] == "shortest"]["peak Zi"]
        <= shrink_factors[lambda x: x["variant"] == "shortest"]["Zsol"]
    )
    print()
    print(
        "second-phase factor ≤ first-phase factor on",
        f"{a.sum() / len(a):.0%}",
        "of the instances",
    )

    print()
    print(
        "on shrink factor of Zsol ≥ 10, median of shrink factor of max |Zi| is",
        shrink_factors[lambda x: x["variant"] == "shortest"][lambda x: x["Zsol"] >= 10][
            "peak Zi"
        ]
        .median()
        .round(),
    )

    print()
    print("Spearman correlation between shrink (peak, average)")
    print(
        "shortest:",
        stats.spearmanrho(
            shrink_factors[lambda x: x["variant"] == "shortest"]["peak Zi"].astype(
                np.float64
            ),
            shrink_factors[lambda x: x["variant"] == "shortest"]["average Zi"].astype(
                np.float64
            ),
        ).statistic.round(2),
    )
    print(
        "farthest:",
        stats.spearmanrho(
            shrink_factors[lambda x: x["variant"] == "farthest"]["peak Zi"].astype(
                np.float64
            ),
            shrink_factors[lambda x: x["variant"] == "farthest"]["average Zi"].astype(
                np.float64
            ),
        ).statistic.round(2),
    )

    print()
    print("### Pronounced examples.")

    table8_dat = ["mug88_1_02", "LGC_exp_instance007_01", "anna_02"]
    table8 = shortest_wide.query("dat_file in @table8_dat")

    shortest_zdd = pd.read_parquet(
        os.path.join(util.PARQUET_PARENT, "shortest", "zdd_nodes"),
        columns=["dat_file", "zdd_nodes", "type"],
        filters=[("dat_file", "in", table8_dat)],
    )
    shortest_zdd = shortest_zdd.drop_duplicates(["dat_file", "type"])
    shortest_zdd = shortest_zdd.pivot(
        index="dat_file", columns="type", values="zdd_nodes"
    )

    shortest_zdd = shortest_zdd.reset_index()
    shortest_zdd["greefb"] = shortest_zdd["heur"].mask(
        shortest_zdd["dat_file"].isin(gree_fallback_dat), shortest_zdd["orig"]
    )

    shortest_zdd = shortest_zdd.melt(
        id_vars="dat_file", value_vars=["opt", "greefb", "orig"], value_name="zdd_nodes"
    )

    stubs = ["pw", "zdd_size", "zdd_time", time_ref, "max_memory"]
    table8_long = pd.wide_to_long(
        table8,
        i="dat_file",
        j="type",
        stubnames=stubs,
        sep="_",
        suffix=r"\w+",
    )

    table8_long = table8_long.loc[(slice(None), ["opt", "greefb", "orig"]), :]
    table8_long = table8_long.reset_index()

    table8_long = table8_long.merge(shortest_zdd, on=["dat_file", "type"], how="left")
    table8_long["peak Zi"] = table8_long["zdd_nodes"].map(max, na_action="ignore")
    table8_long["average Zi"] = table8_long["zdd_nodes"].map(
        lambda x: x.mean(), na_action="ignore"
    )

    table8 = table8_long[
        [
            "dat_file",
            "type",
            "vertices",
            "edges",
            "pw",
            "zdd_size",
            "zdd_time",
            "peak Zi",
            "average Zi",
            time_ref,
            "max_memory",
        ]
    ]
    table8["max_memory"] /= 1024

    table8["dat_file"] = pd.Categorical(
        table8["dat_file"], categories=table8_dat, ordered=True
    )
    table8["type"] = table8["type"].astype(decom_cat_dtype)

    table8 = table8.rename(columns={"pw": "width", "zdd_size": "Zsol"})

    print()
    print("**table 8**:")
    print()
    print("```")
    print(
        (table8.groupby(["dat_file", "vertices", "edges", "type"]).agg("first"))
        .astype(np.float64)
        .round({"zdd_time": 3, "average Zi": 0, "wallclock_time": 2, "max_memory": 0})
        .to_string()
    )
    print("```")

    print()
    print("## 5.3 Reconfiguration Length")
    print()

    print("range of ℓ, shortest")
    print()
    print(
        shortest_wide.query(
            f"(solved{solve_time_min}_opt == 1 or \
            solved{solve_time_min}_greefb == 1 or \
            solved{solve_time_min}_orig == 1) and \
            reconfiguration_sequence_length > 0"
        )["reconfiguration_sequence_length"]
        .agg(["min", "max"])
        .to_markdown()
    )

    shortest_gree = shortest_wide.query(f"solved{solve_time_min}_greefb == 1")
    print()
    print("width of ℓ ≥ 100, shortest")
    print()
    print(
        shortest_gree.query("reconfiguration_sequence_length >= 100")["pw_greefb"]
        .agg(["max", "median"])
        .to_markdown()
    )
    print()
    print("_no instance of large width reaches such lengths_")
    a = shortest_gree.query("reconfiguration_sequence_length >= 100")["pw_greefb"].max()
    print(
        "- instances of larger widths have reached ℓ ≤",
        shortest_gree.query("pw_greefb > @a")["reconfiguration_sequence_length"].max(),
    )

    print()
    print("## 5.4 Width and Solvability")

    shortest_wide["width20"] = np.where(
        shortest_wide["pw_greefb"] <= 20, "width≤20", "width>20"
    )
    shortest_gree = shortest_wide.reset_index()
    shortest_gree["solved?_greefb"] = (
        shortest_gree[f"solved{solve_time_min}_greefb"] > 0
    )
    shortest_gree["|V|"] = pd.cut(
        shortest_gree["vertices"],
        [-1, 100, 200, 500, np.inf],
        labels=["≤100", "101–200", "201–500", ">500"],
    )
    shortest_gree = shortest_gree.groupby(["|V|", "width20"], observed=False)[
        "solved?_greefb"
    ].agg(["sum", len])

    shortest_gree = shortest_gree.unstack()[
        [
            ("sum", "width≤20"),
            ("len", "width≤20"),
            ("sum", "width>20"),
            ("len", "width>20"),
        ]
    ]

    print()
    print("shortest:")
    print()
    print("```")
    print(shortest_gree.to_string())
    print("```")

    print()
    print("percentages:")
    print()
    print("```")
    print(
        (shortest_gree["sum"] / shortest_gree["len"] * 100)
        .round(0)
        .astype(int)
        .to_string()
    )
    print("```")

    farthest_wide["width20"] = np.where(
        farthest_wide["pw_greefb"] <= 20, "width≤20", "width>20"
    )
    farthest_gree = farthest_wide.reset_index()
    farthest_gree["solved?_greefb"] = (
        farthest_gree[f"solved{solve_time_min}_greefb"] > 0
    )
    farthest_gree["|V|"] = pd.cut(
        farthest_gree["vertices"],
        [-1, 100, 200, 500, np.inf],
        labels=["≤100", "101–200", "201–500", ">500"],
    )
    farthest_gree = farthest_gree.groupby(["|V|", "width20"], observed=False)[
        "solved?_greefb"
    ].agg(["sum", len])

    farthest_gree = farthest_gree.unstack()[
        [
            ("sum", "width≤20"),
            ("len", "width≤20"),
            ("sum", "width>20"),
            ("len", "width>20"),
        ]
    ]

    print()
    print("farthest is similar to shortest:")
    print()
    print("```")
    print(farthest_gree.to_string())
    print("```")


if __name__ == "__main__":
    from contextlib import redirect_stdout

    filename = __file__ + ".md"
    print("write", filename)
    with open(filename, "w", encoding="utf8") as fs:
        with redirect_stdout(fs):
            main()
