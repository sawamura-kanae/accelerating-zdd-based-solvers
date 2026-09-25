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
    r = lambda t: f"{time_ref}_{t} <= @solve_time and `solved?_{t}` == 1"
    for typ in ["opt", "greefb", "orig"]:
        shortest_wide[f"solved{solve_time_min}_{typ}"] = shortest_wide.eval(q(typ))
        farthest_wide[f"solved{solve_time_min}_{typ}"] = farthest_wide.eval(q(typ))

        if (
            shortest_wide.eval(r(typ)) != shortest_wide[f"solved{solve_time_min}_{typ}"]
        ).sum() != 0:
            raise Exception("the same instances should be solved even with preprocess")
        if (
            farthest_wide.eval(r(typ)) != farthest_wide[f"solved{solve_time_min}_{typ}"]
        ).sum() != 0:
            raise Exception("the same instances should be solved even with preprocess")

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

    print("# IV. Experimental Results")
    print("## A. Experimental Setup")
    print("### a) Benchmarks")
    print()
    print(
        "total:",
        shortest_wide["dat_file"].nunique(),
        "instances, drawn from",
        shortest_wide["graph_name"].nunique(),
        "graphs",
    )

    print(
        "-",
        shortest_wide.groupby("graph_name")["dat_file_s_id"].agg("nunique").sum(),
        "instances for farthest as well",
    )

    graphs = shortest_wide.drop_duplicates("graph_name")
    print()
    print(graphs["vertices"].agg(["min", "max", "median"]).to_markdown())
    print()
    print(graphs["edges"].agg(["min", "max", "median"]).to_markdown())

    print()
    print("## B. Input Graphs and Widths of the Three Decompositions")
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
    print("**table I**:")
    print()
    table1 = opt_available_shortest
    table1["\\|V\\|"] = pd.cut(
        table1["vertices"],
        [-1, 50, 100, 200, 500, 1000, np.inf],
        labels=["≤50", "51–100", "101–200", "201–500", "501–1000", ">1000"],
    )
    table1_agg = table1.groupby("\\|V\\|", observed=True).agg(
        **{
            "#graphs": ("graph_name", "nunique"),
            "#inst.": ("dat_file", "size"),
            "\\|E\\| min": ("edges", "min"),
            "\\|E\\| max": ("edges", "max"),
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
    print("(Figure 2 is pw_three_box)")

    print()
    print("quartiles of widths on opt-available:")
    print()
    opt_available_shortest_graphs = opt_available_shortest.drop_duplicates("graph_name")
    print(
        opt_available_shortest_graphs.filter(like="pw_")
        .drop(columns="pw_gree")
        .quantile([0.5, 0.25, 0.75])[["pw_orig", "pw_greefb", "pw_opt"]]
        .rename(index={0.5: "median", 0.25: "lower quartile", 0.75: "upper quartile"})
        .round()
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

    print()
    print("## C. Solved Instances")

    print()
    print("**table II**:")
    solved_within_time_cols = [
        f"solved{solve_time_min}_opt",
        f"solved{solve_time_min}_greefb",
        f"solved{solve_time_min}_orig",
    ]
    table2_shortest = shortest_wide.melt(
        id_vars=["dat_file", "opt_available?"], value_vars=solved_within_time_cols
    )
    table2_shortest["problem"] = "shortest"
    table2_farthest = farthest_wide.melt(
        id_vars=["dat_file", "opt_available?"], value_vars=solved_within_time_cols
    )
    table2_farthest["problem"] = "farthest"
    table2 = pd.concat([table2_shortest, table2_farthest])

    table2["variable"] = (
        table2["variable"]
        .str[len(f"solved{solve_time_min}_") :]
        .astype(decom_cat_dtype)
    )
    table2["problem"] = table2["problem"].astype(variant_cat_dtype)
    table2["opt_available?"] = pd.Categorical(
        np.where(table2["opt_available?"], "opt-available", "opt-missing"),
        categories=["opt-available", "opt-missing"],
        ordered=True,
    )

    table2 = table2.groupby(["opt_available?", "problem", "variable"])["value"].sum()
    table2 = table2.reset_index()
    table2 = table2.pivot(
        index="problem", columns=["opt_available?", "variable"], values="value"
    )

    print()
    print("```")
    print(table2.to_string())
    print("```")

    print()
    print("the solved sets are nested:")
    print()
    print("### a) opt-available instances:")
    print()
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
    print("### b) on opt-missing instances:")
    print()
    print("- _every instance solved under orig is also solved under gree_")
    q = f"`solved{solve_time_min}_orig` == 1 and `solved{solve_time_min}_greefb` != 1"
    print(
        "  - conversely, the number of instances solved in orig but not gree is",
        len(opt_missing_shortest.query(q)),
        "for shortest, and",
        len(opt_missing_farthest.query(q)),
        "for farthest",
    )

    print()
    print("### c) Nesting across variants:")
    print()
    print(
        "- _every instance solved on the farthest variant is also solved on the shortest one_"
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

    q = f"solved{solve_time_min}_orig == 0 and \
            (solved{solve_time_min}_greefb == 1 or solved{solve_time_min}_opt == 1)"
    flipped_shortest = shortest_wide.query(q)
    flipped_farthest = farthest_wide.query(q)

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

    flipped_shortest = flipped_shortest[cols]
    flipped_farthest = flipped_farthest[cols]

    flipped_shortest = flipped_shortest.set_index("dat_file")
    flipped_farthest = flipped_farthest.set_index("dat_file")

    flipped_shortest, flipped_farthest = flipped_shortest.align(
        flipped_farthest, join="inner"
    )
    flipped = flipped_shortest[flipped_shortest.eq(flipped_farthest).min(axis=1)]

    print()
    print("### d) Width for the flipped instances")
    print()

    print(
        flipped["graph_name"].nunique(),
        "graphs,",
        flipped.drop_duplicates("graph_name")["opt_available?"].sum(),
        "of them opt-available,",
        len(flipped),
        "instances",
    )
    print()
    print(
        flipped.drop_duplicates("graph_name")[["pw_orig", "pw_greefb"]]
        .agg(["min", "max", "median"])
        .transpose()
        .round()
        .to_markdown()
    )

    print()
    print("# V. Analyses")
    print()
    print("the range of the size of solution-space ZDD under orig is wide:")
    print()
    print(opt_available_shortest["zdd_size_orig"].agg(["min", "max"]).to_markdown())

    print()
    print("## A. The First Phase: Building the Solution-Space ZDD")

    all_wide = pd.concat(
        [
            shortest_wide.assign(variant="shortest"),
            farthest_wide.assign(variant="farthest"),
        ]
    )
    table3_mask = functools.reduce(
        lambda x, y: x & (all_wide[y]), solved_within_time_cols, initial=True
    )
    table3 = all_wide[table3_mask]

    def melt(x):
        melted = table3.melt(
            id_vars=["dat_file", "variant"],
            value_vars=[f"{x}_{typ}" for typ in ["opt", "greefb", "orig"]],
            var_name="type",
            value_name=x,
        )
        melted["type"] = melted["type"].str[len(f"{x}_") :]
        return melted

    table3_ids = ["dat_file", "type", "variant"]
    table3 = functools.reduce(
        lambda x, y: x.merge(y, how="left", on=table3_ids),
        map(melt, ["pw", "zdd_size", "zdd_time", "wallclock_time", "max_memory"]),
    )

    table3["variant"] = table3["variant"].astype(variant_cat_dtype)
    table3["type"] = table3["type"].astype(decom_cat_dtype)

    table3["max_memory"] /= 1024

    print()
    print("**table III**:")
    print()
    print("```")
    print(
        table3.set_index("dat_file")
        .groupby(["variant", "type"])
        .agg([geometric_mean, "max"])
        .astype(np.float64)
        .round(
            {
                ("pw", "geometric_mean"): 1,
                ("zdd_size", "geometric_mean"): 0,
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

    shortest_all_solved = all_wide[table3_mask].query("variant == 'shortest'")
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
    print("## B. The Second Phase: Rebuilding the ZDD at Each Step")

    shortest_zdd = pd.read_parquet(
        os.path.join(util.PARQUET_PARENT, "shortest", "zdd_nodes"),
        columns=["dat_file", "zdd_nodes", "type"],
        filters=[("dat_file", "in", table3["dat_file"])],
    )
    shortest_zdd = shortest_zdd.drop_duplicates(["dat_file", "type"])
    shortest_zdd["variant"] = "shortest"

    farthest_zdd = pd.read_parquet(
        os.path.join(util.PARQUET_PARENT, "farthest", "zdd_nodes"),
        columns=["dat_file", "zdd_nodes", "type"],
        filters=[("dat_file", "in", table3["dat_file"])],
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

    shrink_factors = table3.merge(all_zdd, how="left", on=table3_ids)

    assert shrink_factors["zdd_nodes"].isna().sum() == 0

    shrink_factors["zdd_nodes_peak"] = shrink_factors["zdd_nodes"].map(max)
    shrink_factors["zdd_nodes_average"] = shrink_factors["zdd_nodes"].map(
        lambda x: x.mean()
    )

    shrink_factors_details = shrink_factors

    shrink_factors = shrink_factors.pivot(
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

    example = "mug88_1_02"
    print()
    print(
        shortest_wide[
            ["dat_file", "vertices", "edges", "pw_orig", "pw_greefb", "pw_opt"]
        ]
        .query("dat_file == @example")
        .to_markdown(index=False)
    )
    print()
    print(
        shrink_factors_details[
            lambda x: (x["variant"] == "shortest") & (x["dat_file"] == example)
        ][["type", "zdd_nodes_peak"]].to_markdown(index=False)
    )

    print()
    print("# C. Reconfiguration Length")
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
    print("ℓ < 100")
    print()
    print(
        shortest_gree.query("reconfiguration_sequence_length < 100")["pw_greefb"]
        .agg(["max", "median"])
        .to_markdown()
    )


if __name__ == "__main__":
    from contextlib import redirect_stdout

    filename = __file__ + ".md"
    print("write", filename)
    with open(filename, "w", encoding="utf8") as fs:
        with redirect_stdout(fs):
            main()
