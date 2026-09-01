"""Figure set for the report's Results section.

Separate from `plots.py`, which draws a *run's* report. These are paper
figures: pooled over both runs, laid out for a page, and painted from the
validated categorical palette rather than matplotlib's default cycle so a
model keeps one colour across every figure in the document.

Descriptive only — no error bars, no intervals, no test statistics. Every bar
carries a printed value, which the palette's light-surface contrast requires
and a reader wants anyway.

Usage: PYTHONPATH=src python scripts/paper_figures.py [out_dir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from codenames_heb.analysis import load_runs  # noqa: E402

RUNS = [
    "results/20260823T191234131145Z",
    "results/20260829T225350499567Z",
]
# The factorial is balanced: every model, method and floor plays every board.
# The top-up is not — it ran two models under one floor — so pooling it would
# credit those two models with the extra games of the best-performing arm.
# Every model / method / floor figure therefore reads the factorial alone;
# only the board-style figures, which are what the top-up was played for,
# pool the two.
FACTORIAL = "20260823T191234131145Z"

# --- validated palette (see dataviz/references/palette.md, light mode) -------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
BLUES = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
# Board style is an ordinal ladder, so it gets an ordinal ramp rather than
# categorical slots — which also keeps the categorical hues meaning "model"
# in every figure of the document. Steps chosen to clear 2:1 on the surface.
STYLE_RAMP = ["#86b6ef", "#2a78d6", "#104281"]

STYLE_ORDER = ["dual_0", "natural", "dual_100"]
STYLE_LABEL = {"dual_0": "dual_0\n(no ambiguity)", "natural": "natural\n(a real deal)",
               "dual_100": "dual_100\n(all ambiguous)"}
FLOOR_ORDER = ["free", "min2", "min3"]
METHOD_LABEL = {"strong_hebrew": "Hebrew-Direct", "translate_pipeline": "English-Pivot"}
OUTCOME_LABEL = {
    "win": "Win",
    "loss_assassin": "Loss — assassin",
    "loss_opponent": "Loss — opponent words gone",
    "incomplete": "Did not complete",
}

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_2,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "savefig.facecolor": SURFACE,
})


# Display names: the full OpenRouter id is too wide for a 16-row table cell.
_RENAME = {"llama-3.3-70b-instruct": "llama-3.3-70b"}


def short(name) -> str:
    base = str(name).split("/")[-1].replace(":free", "")
    return _RENAME.get(base, base)


def tidy(ax, *, ygrid=True, xgrid=False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.xaxis.grid(xgrid)
    ax.yaxis.grid(ygrid)
    ax.tick_params(length=0)


def titles(fig, title, subtitle):
    """Title block measured in inches, so the gap holds at any figure height."""
    h = fig.get_figheight()
    fig.text(0.012, 1 - 0.26 / h, title, ha="left", va="top", fontsize=12.5,
             fontweight="bold", color=INK)
    fig.text(0.012, 1 - 0.52 / h, subtitle, ha="left", va="top", fontsize=9, color=INK_2)
    return 1 - 0.86 / h


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    rd = load_runs(RUNS)
    g = rd.games.copy()
    g["cm"] = g["model"].map(short)
    g["gs"] = g["guesser_model"].map(short)
    g["outcome_class"] = np.where(
        g.outcome == "win", "win",
        np.where(g.outcome == "loss",
                 np.where(g.loss_reason == "assassin", "loss_assassin", "loss_opponent"),
                 "incomplete"))
    r = rd.rounds.copy()
    r["cm"] = r["model"].map(short)
    r["gs"] = r["guesser_model"].map(short)
    return g, r


# Colour follows the model, never its rank in the current chart: a figure that
# sorts by a different metric must not repaint the bars.
MODEL_ORDER = ["gemini-2.5-flash", "gpt-4o-mini", "llama-3.3-70b", "qwen3.5-9b"]
MODEL_COLORS = dict(zip(MODEL_ORDER, SERIES))


def model_colors(models) -> dict:
    return {m: MODEL_COLORS.get(m, MUTED) for m in models}


def order_by(df, key, metric, ascending=False) -> list:
    return list(df.groupby(key)[metric].mean().sort_values(ascending=ascending).index)


def pct_axis(ax):
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")


def bar_panel(ax, labels, values, colors, *, fmt="{:.0%}", title="", ylabel="", pad=0.14):
    x = np.arange(len(labels))
    ax.bar(x, values, width=0.52, color=colors, zorder=3)
    for xi, v in zip(x, values):
        ax.text(xi, v + max(values) * 0.02, fmt.format(v), ha="center", va="bottom",
                fontsize=9, color=INK, fontweight="normal")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5, color=INK_2)
    ax.set_ylim(0, max(values) * (1 + pad))
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, color=INK, loc="left", pad=8)
    if fmt.endswith("%}"):
        pct_axis(ax)
    tidy(ax)


def grouped_panel(ax, groups, series, colors, *, fmt="{:.0%}", title="", ylabel="",
                  label_rot=0):
    """series: dict name -> list of values, one per group."""
    n = len(series)
    x = np.arange(len(groups))
    w = 0.78 / n
    top = max(max(v) for v in series.values())
    for i, (name, vals) in enumerate(series.items()):
        off = (i - (n - 1) / 2) * w
        ax.bar(x + off, vals, width=w * 0.9, color=colors[name], zorder=3, label=name)
        for xi, v in zip(x, vals):
            ax.text(xi + off, v + top * 0.02, fmt.format(v), ha="center", va="bottom",
                    fontsize=7.2, color=INK_2, rotation=label_rot)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=8.5, color=INK_2)
    ax.set_ylim(0, top * 1.18)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, color=INK, loc="left", pad=8)
    if fmt.endswith("%}"):
        pct_axis(ax)
    tidy(ax)


# --------------------------------------------------------------------------
# Level 1 — pooled over every arm
# --------------------------------------------------------------------------

def fig_role_headline(g):
    done = g[g.outcome.isin(["win", "loss"])]
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 6.6))
    for row, (key, role) in enumerate([("cm", "Codemaster"), ("gs", "Guesser")]):
        order = order_by(done, key, "is_win")
        cols = model_colors(order)
        wins = done[done.is_win == 1]
        wr = [done[done[key] == m].is_win.mean() for m in order]
        ln = [wins[wins[key] == m].game_length.mean() for m in order]
        bar_panel(axes[row][0], order, wr, [cols[m] for m in order],
                  title=f"{role} — win rate", ylabel="share of completed games")
        bar_panel(axes[row][1], order, ln, [cols[m] for m in order], fmt="{:.1f}",
                  title=f"{role} — rounds to win", ylabel="mean rounds (wins only)")
    top = titles(fig, "Model performance in each role",
           "Pooled over every prompt method, clue-count floor, board style and partner model. "
           "Rounds-to-win counts only games that were won, so it reads as efficiency.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def fig_outcome_composition(g):
    order = order_by(g[g.outcome.isin(["win", "loss"])], "cm", "is_win")
    classes = ["win", "loss_assassin", "loss_opponent", "incomplete"]
    colors = dict(zip(classes, SERIES))
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    x = np.arange(len(order))
    bottom = np.zeros(len(order))
    for c in classes:
        vals = np.array([(g[g.cm == m].outcome_class == c).mean() for m in order])
        ax.bar(x, vals, bottom=bottom, width=0.6, color=colors[c], zorder=3,
               edgecolor=SURFACE, linewidth=2, label=OUTCOME_LABEL[c])
        for xi, (b, v) in enumerate(zip(bottom, vals)):
            if v > 0.045:
                ax.text(xi, b + v / 2, f"{v:.0%}", ha="center", va="center",
                        fontsize=8, color="white", fontweight="normal")
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(order, fontsize=8.5, color=INK_2)
    ax.set_ylim(0, 1)
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("share of all games", fontsize=9)
    tidy(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4, frameon=False,
              fontsize=8.5, labelcolor=INK_2)
    top = titles(fig, "How games end, by codemaster",
           "All games including those that never played out. The two loss kinds are separated: "
           "one assassin hit ends a game outright, opponent-word losses accumulate.")
    fig.tight_layout(rect=(0, 0.04, 1, top))
    return fig


# --------------------------------------------------------------------------
# Level 2 — the 16 pairs
# --------------------------------------------------------------------------

def _heat(ax, mat, rows, cols, *, fmt, title, cmap=BLUES):
    im = ax.imshow(mat, cmap=cmap, aspect="auto")
    lo, hi = np.nanmin(mat), np.nanmax(mat)
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = mat[i, j]
            if np.isnan(v):
                continue
            shade = (v - lo) / (hi - lo) if hi > lo else 0.5
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=8.5,
                    color="white" if shade > 0.55 else INK)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, fontsize=8, color=INK_2, rotation=20, ha="right")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=8, color=INK_2)
    ax.set_xlabel("Guesser", fontsize=9)
    ax.set_ylabel("Codemaster", fontsize=9)
    ax.set_title(title, fontsize=10, color=INK, loc="left", pad=8)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


def fig_pair_matrix(g):
    done = g[g.outcome.isin(["win", "loss"])]
    rows = order_by(done, "cm", "is_win")
    cols = order_by(done, "gs", "is_win")
    wr = np.array([[done[(done.cm == r) & (done.gs == c)].is_win.mean() for c in cols]
                   for r in rows])
    wins = done[done.is_win == 1]
    ln = np.array([[wins[(wins.cm == r) & (wins.gs == c)].game_length.mean() for c in cols]
                   for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
    _heat(axes[0], wr, rows, cols, fmt="{:.0%}", title="Win rate  (darker = better)")
    _heat(axes[1], ln, rows, cols, fmt="{:.1f}", title="Rounds to win  (darker = slower)")
    top = titles(fig, "Every codemaster against every guesser",
           "16 pairs; the diagonal is self-play. Rows and columns are ordered by that model's "
           "own mean, so a model that is strong in one role and weak in the other shows as an "
           "off-diagonal pattern.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def fig_pair_table(g):
    """The English benchmark's Table I layout, rendered as a figure."""
    done = g[g.outcome.isin(["win", "loss"])]
    recs = []
    for (cm, gs), sub in done.groupby(["cm", "gs"]):
        wins = sub[sub.is_win == 1]
        recs.append({
            "Codemaster": cm, "Guesser": gs, "Games": len(sub),
            "Win": sub.is_win.mean(), "Rounds": sub.game_length.mean(),
            "Rounds (win)": wins.game_length.mean() if len(wins) else np.nan,
            "Targets": sub.targets_found.mean(),
            "Opp.": sub.opponent_words_revealed.mean(),
            "Civ.": sub.civilian_words_revealed.mean(),
            "Assassin": sub.assassin_hit.mean(),
            "Clue size": sub.mean_clue_count.mean(),
        })
    t = pd.DataFrame(recs).sort_values(["Win"], ascending=False).reset_index(drop=True)
    fmt = {"Win": "{:.1%}", "Assassin": "{:.1%}", "Rounds": "{:.2f}",
           "Rounds (win)": "{:.2f}", "Targets": "{:.2f}", "Opp.": "{:.2f}",
           "Civ.": "{:.2f}", "Clue size": "{:.2f}", "Games": "{:,.0f}"}
    cells = [[fmt.get(c, "{}").format(v) if pd.notna(v) else "—" for c, v in row.items()]
             for _, row in t.iterrows()]
    fig, ax = plt.subplots(figsize=(11.6, 5.4))
    ax.axis("off")
    tbl = ax.table(cellText=cells, colLabels=list(t.columns), loc="center",
                   cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.42)
    ncol = len(t.columns)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor("#f0efec")
            cell.set_text_props(color=INK, fontweight="bold")
        else:
            cell.set_facecolor(SURFACE if r % 2 else "#f7f6f3")
            cell.set_text_props(color=INK_2)
        if c < 2:
            cell.set_text_props(ha="left")
            cell.PAD = 0.04
    top = titles(fig, "Pair table, in the English benchmark's layout",
           "One row per codemaster–guesser pair, ordered by win rate. Opp./Civ. are mean "
           "opponent and civilian words revealed per game; clue size is the mean clue number.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


# --------------------------------------------------------------------------
# Level 3 — stratified by a designed factor
# --------------------------------------------------------------------------

def _factor_figure(g, column, levels, level_labels, title, subtitle, *, colors=None):
    done = g[g.outcome.isin(["win", "loss"])]
    wins = done[done.is_win == 1]
    models = order_by(done, "cm", "is_win")
    cols = colors or model_colors(models)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4))
    grouped_panel(
        axes[0], [level_labels[v] for v in levels],
        {m: [done[(done.cm == m) & (done[column] == v)].is_win.mean() for v in levels]
         for m in models},
        cols, title="Win rate", ylabel="share of completed games")
    grouped_panel(
        axes[1], [level_labels[v] for v in levels],
        {m: [wins[(wins.cm == m) & (wins[column] == v)].game_length.mean() for v in levels]
         for m in models},
        cols, fmt="{:.1f}", title="Rounds to win", ylabel="mean rounds (wins only)")
    handles = [Patch(facecolor=cols[m], label=m) for m in models]
    fig.legend(handles=handles, loc="lower center", ncol=len(models), frameon=False,
               fontsize=8.5, labelcolor=INK_2, bbox_to_anchor=(0.5, -0.015))
    top = titles(fig, title, subtitle)
    fig.tight_layout(rect=(0, 0.07, 1, top))
    return fig


def fig_method(g):
    return _factor_figure(
        g, "method", ["strong_hebrew", "translate_pipeline"], METHOD_LABEL,
        "Prompt method, by codemaster",
        "Both conditions play the same boards, so the comparison is paired within board.")


def fig_style(g):
    return _factor_figure(
        g, "board_style", STYLE_ORDER, STYLE_LABEL,
        "Board ambiguity, by codemaster",
        "The three board styles are different boards, so this is the one contrast board-to-board "
        "variation does not cancel out of.")


def fig_floor(g):
    return _factor_figure(
        g, "count_constraint", FLOOR_ORDER, {v: v for v in FLOOR_ORDER},
        "Clue-count floor, by codemaster",
        "`min2` and `min3` require the clue to point at at least that many words; `free` lets "
        "the codemaster choose.")


def fig_ambition(g, r):
    """What the floor actually changes: the distribution of clue numbers."""
    models = order_by(g[g.outcome.isin(["win", "loss"])], "cm", "is_win")
    cols = model_colors(models)
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.9), sharey=True)
    counts = [0, 1, 2, 3, 4, 5]
    for ax, floor in zip(axes, FLOOR_ORDER):
        sub = r[r.count_constraint == floor]
        x = np.arange(len(counts))
        w = 0.78 / len(models)
        for i, m in enumerate(models):
            s = sub[sub.cm == m]
            vals = [(s["count"] == c).mean() for c in counts[:-1]]
            vals.append((s["count"] >= counts[-1]).mean())
            ax.bar(x + (i - (len(models) - 1) / 2) * w, vals, width=w * 0.9,
                   color=cols[m], zorder=3, label=m)
        ax.set_xticks(x)
        ax.set_xticklabels([str(c) for c in counts[:-1]] + ["5+"], fontsize=8.5)
        ax.set_title(floor, fontsize=10, color=INK, loc="left", pad=8)
        ax.set_xlabel("clue number", fontsize=9)
        pct_axis(ax)
        tidy(ax)
    axes[0].set_ylabel("share of rounds", fontsize=9)
    handles = [Patch(facecolor=cols[m], label=m) for m in models]
    fig.legend(handles=handles, loc="lower center", ncol=len(models), frameon=False,
               fontsize=8.5, labelcolor=INK_2, bbox_to_anchor=(0.5, -0.02))
    top = titles(fig, "What the clue-count floor changes",
           "Distribution of the clue number the codemaster chose, per floor. A floor removes the "
           "small clues by construction; whether it produces good large ones is the question.")
    fig.tight_layout(rect=(0, 0.08, 1, top))
    return fig


# --------------------------------------------------------------------------
# Level 4 — distributions and dynamics
# --------------------------------------------------------------------------

def fig_board_spread(g):
    done = g[g.outcome.isin(["win", "loss"])]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.3))
    rng = np.random.default_rng(0)
    per_board = (done.groupby(["board_style", "board_seed"])
                 .agg(win=("is_win", "mean")).reset_index())
    for i, style in enumerate(STYLE_ORDER):
        vals = per_board[per_board.board_style == style]["win"].values
        jitter = rng.normal(0, 0.055, len(vals))
        axes[0].scatter(np.full(len(vals), i) + jitter, vals, s=11, alpha=0.45,
                        color=SERIES[0], edgecolors="none", zorder=3)
        axes[0].plot([i - 0.28, i + 0.28], [vals.mean()] * 2, color=SERIES[1],
                     lw=2.4, zorder=4, solid_capstyle="round")
        axes[0].text(i, 1.02, f"{vals.mean():.0%}", ha="center", fontsize=9, color=INK)
    axes[0].set_xticks(range(len(STYLE_ORDER)))
    axes[0].set_xticklabels([STYLE_LABEL[s] for s in STYLE_ORDER], fontsize=8.5, color=INK_2)
    axes[0].set_ylim(0, 1.09)
    axes[0].set_ylabel("win rate on that board", fontsize=9)
    axes[0].set_title("Every board, by style", fontsize=10, color=INK, loc="left", pad=8)
    pct_axis(axes[0])
    tidy(axes[0])

    lengths = done.game_length.values
    for i, style in enumerate(STYLE_ORDER):
        vals = done[done.board_style == style].game_length
        axes[1].hist(vals, bins=np.arange(0.5, max(lengths) + 1.5, 1), histtype="step",
                     lw=1.8, color=STYLE_RAMP[i], label=STYLE_LABEL[style].split("\n")[0],
                     density=True, zorder=3)
    axes[1].set_xlabel("rounds played", fontsize=9)
    axes[1].set_ylabel("share of games", fontsize=9)
    axes[1].set_title("Game length", fontsize=10, color=INK, loc="left", pad=8)
    pct_axis(axes[1])
    axes[1].legend(frameon=False, fontsize=8.5, labelcolor=INK_2)
    tidy(axes[1])
    top = titles(fig, "Board-to-board variation",
           "Each dot is one board's win rate over every game played on it; the bar is the style "
           "mean. The spread within a style is the reason board is the unit of observation.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


GAME_KEY = ["run_id", "model", "guesser_model", "method", "count_constraint",
            "board_style", "board_seed", "trial"]


def targets_by_round(r: pd.DataFrame, max_round: int = 14) -> pd.DataFrame:
    """Mean targets revealed by the end of round k, over ALL games.

    A game that has ended keeps its final total for every later round rather
    than dropping out of the average. Averaging only over games still alive
    conditions on survival, which lets the mean drift past 9 — an impossible
    value for a board that holds nine targets.
    """
    r = r.sort_values(GAME_KEY + ["round"]).copy()
    r["cum"] = r.groupby(GAME_KEY, sort=False)["n_correct"].cumsum()
    wide = r.pivot_table(index=GAME_KEY, columns="round", values="cum")
    wide = wide.reindex(columns=range(1, max_round + 1)).ffill(axis=1).fillna(0)
    wide["cm"] = [k[GAME_KEY.index("model")] for k in wide.index]
    wide["cm"] = wide["cm"].map(short)
    return wide.groupby("cm").mean()


def fig_trajectory(g, r):
    done = g[g.outcome.isin(["win", "loss"])]
    models = order_by(done, "cm", "is_win")
    cols = model_colors(models)
    prog = targets_by_round(r)
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
    for m in models:
        axes[0].plot(prog.columns, prog.loc[m].values, lw=2, color=cols[m], label=m, zorder=3)
        sub = r[r.cm == m]
        alive = sub.groupby("round").size()
        alive = (alive / alive.iloc[0])[alive.index <= 14]
        axes[1].plot(alive.index, alive.values, lw=2, color=cols[m], label=m, zorder=3)
    axes[0].axhline(9, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
    axes[0].text(1.2, 9.18, "all 9 targets — the board is won", fontsize=8, color=MUTED)
    axes[0].set_ylim(0, 9.9)
    axes[0].set_xlabel("round", fontsize=9)
    axes[0].set_ylabel("targets revealed, cumulative", fontsize=9)
    axes[0].set_title("How fast the board comes apart", fontsize=10, color=INK, loc="left",
                      pad=8)
    axes[1].set_xlabel("round", fontsize=9)
    axes[1].set_ylabel("share of games still running", fontsize=9)
    axes[1].yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    axes[1].set_title("Games still running", fontsize=10, color=INK, loc="left", pad=8)
    for ax in axes:
        tidy(ax)
    axes[0].legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="lower right")
    top = titles(fig, "How a game unfolds, by codemaster",
                 "Left: mean targets revealed by the end of each round, over every game — a game "
                 "that has ended holds its final total, so the curve flattens as games die. "
                 "Right: the share of games still being played.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def fig_stopping(g, r):
    models = order_by(g[g.outcome.isin(["win", "loss"])], "gs", "is_win")
    cols = model_colors(models)
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
    elig = r[r.early_stop_eligible == 1]
    bonus = r[r.bonus_eligible == 1]
    bar_panel(axes[0], models, [elig[elig.gs == m].is_early_stop.mean() for m in models],
              [cols[m] for m in models], title="Stops before reaching the count",
              ylabel="share of eligible rounds")
    bar_panel(axes[1], models, [bonus[bonus.gs == m].is_bonus_taken.mean() for m in models],
              [cols[m] for m in models], title="Takes the bonus guess",
              ylabel="share of eligible rounds")
    top = titles(fig, "Guesser stopping behaviour",
           "Two decisions the clue does not make for the guesser: whether to stop short of the "
           "clue's number, and whether to spend the one extra guess the rules allow.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


# `scope` says which dataset a figure reads: "factorial" or "pooled".
FIGURES = {
    "fig01_role_headline": ("factorial", lambda g, r: fig_role_headline(g)),
    "fig02_outcome_composition": ("factorial", lambda g, r: fig_outcome_composition(g)),
    "fig03_pair_matrix": ("factorial", lambda g, r: fig_pair_matrix(g)),
    "fig04_pair_table": ("factorial", lambda g, r: fig_pair_table(g)),
    "fig05_method": ("factorial", lambda g, r: fig_method(g)),
    "fig06_board_style": ("factorial", lambda g, r: fig_style(g)),
    "fig07_count_floor": ("factorial", lambda g, r: fig_floor(g)),
    "fig08_ambition": ("factorial", fig_ambition),
    "fig09_board_spread": ("pooled", lambda g, r: fig_board_spread(g)),
    "fig10_trajectory": ("factorial", fig_trajectory),
    "fig11_stopping": ("factorial", fig_stopping),
}


def main(out_dir: str = "docs/paper_figures") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    games, rounds = load()
    fac_g, fac_r = games[games.run_id == FACTORIAL], rounds[rounds.run_id == FACTORIAL]
    print(f"pooled {len(games):,} games / factorial {len(fac_g):,} games")
    data = {"pooled": (games, rounds), "factorial": (fac_g, fac_r)}
    for name, (scope, build) in FIGURES.items():
        fig = build(*data[scope])
        path = out / f"{name}.png"
        fig.savefig(path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print("wrote", path)


if __name__ == "__main__":
    main(*sys.argv[1:])
