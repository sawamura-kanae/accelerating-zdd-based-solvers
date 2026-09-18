# all plots

import os.path as path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib as mpl
import matplotlib.colors as clrs

mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42

OUTPUT = "./figs"

height = 3


def aspect_ratio(f, h=height):
    return (h * f, h)


alpha = 0.8
pw_cmap = clrs.ListedColormap(
    mpl.colormaps["viridis_r"](np.linspace(0.06, 1, int(256 * 0.94)))
)

# Okabe-Ito Palette with gray
styles = {
    "orig": {"color": "#666666", "marker": "o", "linestyle": (0, (4, 1, 1, 1, 1, 1))},
    "heur": {"color": "#009E73", "marker": "s", "linestyle": "solid"},
    "opt": {"color": "#E69F00", "marker": "^", "linestyle": "dashdot"},
}

grid_kws = {
    "color": "0.8",
    "alpha": 0.6,
    "linestyle": "solid",
    "linewidth": 0.4,
    "zorder": -100,
}

plt.rcParams["font.size"] = 7
plt.rcParams["axes.labelsize"] = 8
plt.rcParams["lines.markersize"] = 4.8
plt.rcParams["axes.spines.right"] = False
plt.rcParams["axes.spines.top"] = False

import util


def savefig(fig, p, **a):
    print(p)
    fig.savefig(p, **a)
    plt.close(fig)


# https://stackoverflow.com/q/50057591
def make_square_axes(ax):
    ax.set_aspect(1 / ax.get_data_ratio())


def graph_scale_overview(outname="graph_scale_overview.pdf"):
    shortest = pd.read_csv(util.SHORTEST_WIDE, dtype=util.DTYPE)
    shortest = shortest.drop_duplicates("graph_name")
    markersize = 8
    linewidths = 1

    fig, ax = plt.subplots(
        figsize=aspect_ratio(1.3, height / 1.2), layout="constrained"
    )

    is_opt_available = (shortest["solved?_opt_preprocess"] == 1) & (
        shortest["wallclock_time_opt_preprocess"] <= 60 * 60
    )
    opt_available = shortest[is_opt_available]
    opt_missing = shortest[~is_opt_available]

    c = ax.scatter(
        opt_available["vertices"],
        opt_available["edges"],
        c=opt_available["pw_opt"],
        norm="log",
        cmap=pw_cmap,
        label=f"opt available ({len(opt_available)})",
        s=markersize + linewidths * 4,  # !?
        # when smaller looks too dark
        # edgecolors="0",
        # linewidths=0.4,
        linewidths=0,
        alpha=alpha,
        zorder=3,
    )

    ax.scatter(
        opt_missing["vertices"],
        opt_missing["edges"],
        label=f"opt missing ({len(opt_missing)})",
        s=markersize,
        linewidths=linewidths,
        zorder=2,
        edgecolors="0.7",
        facecolor="none",
        alpha=alpha,
    )

    # frameon=True because the dots are confusing
    ax.legend(loc="lower right")
    fig.colorbar(c, label="pathwidth $\\mathrm{pw}(G)$")

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_xlabel("vertices $| V |$")
    ax.set_ylabel("edges $| E |$")

    ax.grid(which="major", axis="both", **grid_kws)

    make_square_axes(ax)

    savefig(fig, path.join(OUTPUT, outname), dpi=300)


def pw_three_orders(outname="pw_three_orders.pdf"):
    shortest = pd.read_csv(util.SHORTEST_WIDE, dtype=util.DTYPE)
    shortest = shortest.drop_duplicates("graph_name")
    shortest = util.add_ref(shortest)
    shortest = shortest.drop(columns="pw_heur")

    fig, ax = plt.subplots(
        figsize=aspect_ratio(1.3, height / 1.2), layout="constrained"
    )
    markersize = 7

    opt_available = shortest.drop_duplicates("graph_name").query(
        "`solved?_opt_preprocess` == 1 and wallclock_time_opt_preprocess <= 60 * 60"
    )
    opt_available = opt_available.sort_values(
        ["pw_orig", "pw_heurref", "pw_opt"], ignore_index=True
    )
    opt_available = opt_available.reset_index()

    ax.scatter(
        opt_available["index"],
        opt_available["pw_orig"],
        s=markersize,
        color=styles["orig"]["color"],
        marker=styles["orig"]["marker"],
        label="orig",
        zorder=2,
        alpha=alpha,
    )
    ax.scatter(
        opt_available["index"],
        opt_available["pw_heurref"],
        s=markersize,
        color=styles["heur"]["color"],
        marker=styles["heur"]["marker"],
        label="gree",
        zorder=4,
        alpha=alpha,
    )
    ax.scatter(
        opt_available["index"],
        opt_available["pw_opt"],
        s=markersize,
        color=styles["opt"]["color"],
        marker=styles["opt"]["marker"],
        label="opt",
        zorder=3,
        alpha=alpha,
    )

    ax.vlines(
        opt_available["index"],
        opt_available.filter(like="pw_").min(axis=1),
        opt_available.filter(like="pw_").max(axis=1),
        zorder=-1,
        color="0.6",
        linewidths=0.5,
        alpha=0.5,
    )

    ax.legend(loc="upper left", frameon=False)

    ax.set_yscale("log")

    ax.set_ylabel("decomposition width")
    ax.set_xlabel("graph (sorted by orig width)")

    ax.set_xmargin(0.02)

    ax.grid(which="major", axis="y", **grid_kws)

    savefig(fig, path.join(OUTPUT, outname))


def fig_secondphase_trajectory(outname="fig_secondphase_trajectory.pdf"):
    graph = "mug88_1"
    shortest_pq = pd.read_parquet(
        path.join(util.PARQUET_PARENT, "shortest", "zdd_nodes"),
        columns=["graph_name", "zdd_nodes", "type"],
        filters=[("graph_name", "==", graph)],
    )
    fig, ax = plt.subplots(
        figsize=aspect_ratio(1.3, height / 1.2),
        layout="constrained",
    )
    markersize = 3.3

    to_plot = shortest_pq.query("graph_name == @graph")
    annotate_i = 18

    for typ, type_name in [("orig", "orig"), ("heur", "gree"), ("opt", "opt")]:
        data = to_plot.query("type == @typ").iloc[0]
        ax.plot(
            np.arange(1, len(data["zdd_nodes"]) + 1),
            data["zdd_nodes"],
            color=styles[typ]["color"],
            marker=styles[typ]["marker"],
            markersize=markersize,
            alpha=alpha,
            zorder=3,
            linewidth=1,
        )

        ax.annotate(
            type_name,
            xy=(annotate_i + 1, data["zdd_nodes"][annotate_i]),
            xycoords="data",
            xytext=(0, -0.7),
            textcoords="offset fontsize",
            va="top",
            ha="center",
            fontsize=plt.rcParams["axes.labelsize"],
            color=styles[typ]["color"],
            weight="bold",
        )

    locator = ticker.MaxNLocator(4)
    locator.set_params(integer=True)
    ax.xaxis.set_major_locator(locator)

    ax.set_xmargin(0.02)
    ax.set_yscale("log")

    ax.set_xlabel("reconfiguration step $i$")
    ax.set_ylabel("intermediate ZDD size $| Z^i |$")

    ax.grid(which="major", axis="y", **grid_kws)

    savefig(fig, path.join(OUTPUT, outname))


def reconf_length_time(outname="reconf_length_time.pdf"):
    shortest = pd.read_csv(util.SHORTEST_WIDE, dtype=util.DTYPE)
    markersize = plt.rcParams["lines.markersize"] * 2

    fig, ax = plt.subplots(
        figsize=aspect_ratio(1.3, height / 1.2), layout="constrained"
    )

    to_plot = util.add_ref(shortest)
    to_plot = to_plot.query(
        "`solved?_heurref` == 1 and \
            total_wallclock_time_heurref <= 30 * 60 and \
            reconfiguration_sequence_length > 0"
    )
    # YES instances

    c = ax.scatter(
        to_plot["reconfiguration_sequence_length"],
        to_plot["wallclock_time_heur"].mask(
            to_plot["pw_heur"] > to_plot["pw_orig"], to_plot["wallclock_time_orig"]
        ),
        c=to_plot["pw_heur"],
        norm="log",
        cmap=pw_cmap,
        alpha=alpha,
        s=markersize,
        zorder=3,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.axhline(30 * 60, ls="--", c="0.7", lw=1)
    ax.annotate(
        "30 min",
        xy=(2e2, 30 * 60),
        xycoords="data",
        xytext=(0, -0.4),
        textcoords="offset fontsize",
        va="top",
        ha="center",
        fontsize=plt.rcParams["axes.labelsize"],
        color="0.6",
        zorder=3,
        weight="bold",
    )

    ax.grid(which="major", axis="both", **grid_kws)

    ax.set_xlabel("reconfiguration length $ \\ell $")
    ax.set_ylabel("solving time (s)")

    fig.colorbar(c)

    savefig(fig, path.join(OUTPUT, outname), dpi=300)


def fig_secondphase_scatter(outname="fig_secondphase_scatter.pdf"):
    markersize = plt.rcParams["lines.markersize"] * 2

    shortest_pq = pd.read_parquet(
        path.join(util.PARQUET_PARENT, "shortest", "zdd_nodes")
    )
    shortest_pq = shortest_pq.drop_duplicates(["dat_file", "type"])
    shortest = pd.read_csv(util.SHORTEST_WIDE, dtype=util.DTYPE)
    shortest = util.add_ref(shortest)

    solved = shortest.query(
        " and ".join(
            [
                f"`solved?_{typ}` == 1 and total_wallclock_time_{typ} <= 30 * 60"
                for typ in ["orig", "heurref", "opt"]
            ]
        )
    )

    zdd_nodes = shortest_pq.query("dat_file in @solved['dat_file']")  # commonly solved

    shortest_melt = shortest.melt(
        id_vars="dat_file",
        value_vars=["zdd_size_opt", "zdd_size_heur", "zdd_size_orig"],
        var_name="type",
        value_name="|Zsol|",
    )
    shortest_melt["type"] = shortest_melt["type"].str[len("zdd_size_") :]
    zdd_nodes = zdd_nodes.merge(shortest_melt, how="left", on=["dat_file", "type"])

    zdd_nodes["max |Zi|"] = zdd_nodes["zdd_nodes"].map(
        lambda x: x.max(initial=0)
    )  # empty array means not solved => pw_orig < pw_heur (heur not needed here..)
    zdd_nodes_pivoted = zdd_nodes.pivot(
        index="dat_file", values=["max |Zi|", "|Zsol|"], columns="type"
    )

    zdd_nodes_pivoted["|Zsol| (orig/opt)"] = (
        zdd_nodes_pivoted["|Zsol|", "orig"] / zdd_nodes_pivoted["|Zsol|", "opt"]
    )
    zdd_nodes_pivoted["max |Zi| (orig/opt)"] = (
        zdd_nodes_pivoted["max |Zi|", "orig"] / zdd_nodes_pivoted["max |Zi|", "opt"]
    )

    fig, ax = plt.subplots(
        figsize=aspect_ratio(1.1, height / 1.2), layout="constrained"
    )

    ax.scatter(
        zdd_nodes_pivoted["|Zsol| (orig/opt)"],
        zdd_nodes_pivoted["max |Zi| (orig/opt)"],
        s=markersize,
        alpha=alpha * 0.8,
        zorder=3,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")

    ax.set_xmargin(0.05)
    ax.set_ymargin(0.05)

    ax.set_aspect("equal", "box")
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    ax.set_xlim(xmin=min(xmin, ymin), xmax=max(xmax, ymax))
    ax.set_ylim(ymin=min(xmin, ymin), ymax=max(xmax, ymax))

    ax.grid(which="major", axis="both", **grid_kws)

    ax.axline((0, 0), (1, 1), color="0.7", lw=1, ls="--")
    ax.annotate(
        "$y = x$",
        xy=(0.97, 0.99),
        xycoords="axes fraction",
        xytext=(-0.8, 0),
        textcoords="offset fontsize",
        va="top",
        ha="right",
        fontsize=plt.rcParams["axes.labelsize"],
        color="0.4",  # not bold
        zorder=2,
    )

    ax.set_xlabel("first-phase shrink factor of\n$| Z_{\\mathrm{sol}} |$ (orig/opt)")
    ax.set_ylabel("second-phase shrink factor of\n$\\max_i | Z^i |$ (orig/opt)")

    savefig(fig, path.join(OUTPUT, outname))


def cactus_all693(outname="cactus_all693.pdf"):
    shortest = pd.read_csv(util.SHORTEST_WIDE, dtype=util.DTYPE)
    shortest = util.add_ref(shortest)

    fig, ax = plt.subplots(
        figsize=aspect_ratio(1.5, height / 1.25), layout="constrained"
    )

    for v, q, typ, type_name in [
        (
            "wallclock_time_orig",
            "`solved?_orig` == 1 and \
                    total_wallclock_time_orig <= 30 * 60",
            "orig",
            "orig",
        ),
        (
            "wallclock_time_heurref",
            "`solved?_heurref` == 1 and \
                    total_wallclock_time_heurref <= 30 * 60",
            "heur",
            "gree",
        ),
        (
            "wallclock_time_opt",
            "`solved?_opt` == 1 and \
                    total_wallclock_time_opt <= 30 * 60",
            "opt",
            "opt",
        ),
    ]:
        solved = shortest.query(q)
        num_solved = len(solved)

        vals = solved[v].mask(lambda x: x > 30 * 60).dropna()
        vals = vals.sort_values(ignore_index=True)

        if vals.iloc[-1] < 30 * 60:
            vals = pd.concat([vals, pd.Series([30 * 60])], ignore_index=True)

        ax.step(
            vals,
            vals.index + 1,  # no zero in log scale
            label=f"{type_name} ({num_solved})",
            c=styles[typ]["color"],
            ls=styles[typ]["linestyle"],
            alpha=alpha,
            zorder=3,
            linewidth=1.3,  # too thin?
        )

    ax.set_xscale("log")
    ax.set_ylabel("instances solved")
    ax.set_xlabel("time allowed per instance (s)")

    ax.legend(loc="upper left", frameon=False)

    ax.axvline(30 * 60, ls="--", c="0.7", lw=1)

    ax.grid(which="major", axis="both", **grid_kws)
    ax.set_xmargin(0.014)  # multiplicative
    ax.set_ylim(ymin=0)

    savefig(fig, path.join(OUTPUT, outname))


def main() -> None:
    graph_scale_overview()
    pw_three_orders()
    fig_secondphase_trajectory()
    reconf_length_time()
    fig_secondphase_scatter()
    cactus_all693()


if __name__ == "__main__":
    main()
