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

from codenames_heb import plots  # noqa: E402
from codenames_heb.analysis import load_runs, pair_table  # noqa: E402
from codenames_heb.glosses import SENSES, gloss_counts, sense_shares  # noqa: E402
from codenames_heb.palette import (  # noqa: E402
    BASELINE, GRID, INK, INK_2, MUTED, SEQ_BLUE, SERIES, STYLE_RAMP, SURFACE,
    MODEL_ORDER as _FULL_MODEL_ORDER, display_model,
)

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

# The palette lives in `codenames_heb.palette` so the run-report figures and
# these paper figures give a model the same colour.
BLUES = LinearSegmentedColormap.from_list("seq_blue", list(SEQ_BLUE))

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


def short(name) -> str:
    return display_model(name)


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
MODEL_ORDER = [display_model(m) for m in _FULL_MODEL_ORDER]
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



# --------------------------------------------------------------------------
# The selected set — figures rebuilt to the shape the report actually uses
# --------------------------------------------------------------------------

SUBSET_MODELS = ["gemini-2.5-flash", "gpt-4o-mini"]


def n_boards(df) -> int:
    """Distinct boards, not distinct seeds.

    A board is `(style, seed)`: the same seed draws different words for each
    style. Counting seeds alone reports 30 for an arm that actually played all
    90 boards of the factorial.
    """
    return len(df[["board_style", "board_seed"]].drop_duplicates())


def board_note(df) -> str:
    """`90 boards · 4,217 games` — the denominator behind one column."""
    return f"{n_boards(df)} boards · {len(df):,} games"


def two_model_subset(g):
    """The pair grid the top-up actually played, on all 450 pooled boards."""
    return g[g.cm.isin(SUBSET_MODELS) & g.gs.isin(SUBSET_MODELS)]


def fig_factors_separately(g, models=None, *, title=None, subtitle=None):
    """Prompt method and board ambiguity side by side — one figure, two graphs.

    Each panel averages over *everything* except its own factor and the
    codemaster, so the method bars pool all three board styles and the
    ambiguity bars pool both methods. Combining the two into a single grid
    would make every bar a method x style cell instead, which is a different
    and much thinner quantity.
    """
    models = models or MODEL_ORDER
    done = g[g.outcome.isin(["win", "loss"])]
    wins = done[done.is_win == 1]
    cols = model_colors(models)
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.0), sharey="row",
                             gridspec_kw={"width_ratios": [2, 3]})

    factors = [
        ("method", ["strong_hebrew", "translate_pipeline"], METHOD_LABEL, "Prompt method"),
        ("board_style", STYLE_ORDER,
         {k: v.splitlines()[0] for k, v in STYLE_LABEL.items()}, "Board ambiguity"),
    ]
    for j, (column, levels, labels, factor_name) in enumerate(factors):
        for i, (frame, metric, fmt, ylabel) in enumerate([
            (done, "is_win", "{:.0%}", "win rate"),
            (wins, "game_length", "{:.1f}", "rounds to win"),
        ]):
            ax = axes[i][j]
            groups = [
                f"{labels[v]}\n{board_note(done[done[column] == v])}" if i == 0
                else labels[v]
                for v in levels
            ]
            series = {m: [frame[(frame.cm == m) & (frame[column] == v)][metric].mean()
                          for v in levels] for m in models}
            grouped_panel(ax, groups, series, cols, fmt=fmt,
                          title=factor_name if i == 0 else "",
                          ylabel=ylabel if j == 0 else "")
    for i in range(2):
        row_max = max(ax.get_ylim()[1] for ax in axes[i])
        for ax in axes[i]:
            ax.set_ylim(0, row_max)
    handles = [Patch(facecolor=cols[m], label=m) for m in models]
    fig.legend(handles=handles, loc="lower center", ncol=len(models), frameon=False,
               fontsize=8.5, labelcolor=INK_2, bbox_to_anchor=(0.5, -0.012))
    top = titles(
        fig,
        title or "The two designed factors, one panel each",
        subtitle or "Left: prompt method, pooling all three board styles. Right: board "
        "ambiguity, pooling both prompt methods. Every bar also averages over the "
        "clue-count floor and the guesser.")
    fig.tight_layout(rect=(0, 0.055, 1, top))
    return fig


def fig_board_variance(g):
    """Every board's own win rate — the spread the whole study sits inside."""
    done = g[g.outcome.isin(["win", "loss"])]
    per_board = (done.groupby(["board_style", "board_seed"])
                 .agg(win=("is_win", "mean"), n=("is_win", "size")).reset_index())
    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    rng = np.random.default_rng(0)
    for i, style in enumerate(STYLE_ORDER):
        vals = per_board[per_board.board_style == style]["win"].values
        ax.scatter(np.full(len(vals), i) + rng.normal(0, 0.058, len(vals)), vals,
                   s=15, alpha=0.42, color=STYLE_RAMP[1], edgecolors="none", zorder=3)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        ax.plot([i - 0.30, i + 0.30], [vals.mean()] * 2, color=SERIES[1], lw=2.6,
                zorder=5, solid_capstyle="round")
        ax.plot([i, i], [q1, q3], color=SERIES[1], lw=1.2, zorder=4, alpha=0.8)
        ax.text(i, 1.055, f"mean {vals.mean():.0%}", ha="center", fontsize=9, color=INK)
        ax.text(i, 1.015, f"IQR {q1:.0%}–{q3:.0%}", ha="center", fontsize=8, color=MUTED)
    ax.set_xticks(range(len(STYLE_ORDER)))
    ax.set_xticklabels([f"{STYLE_LABEL[s]}\n{board_note(done[done.board_style == s])}"
                        for s in STYLE_ORDER], fontsize=8.6, color=INK_2)
    ax.set_ylim(-0.03, 1.12)
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.set_ylabel("win rate on that board", fontsize=9)
    pct_axis(ax)
    tidy(ax)
    top = titles(fig, "Board-to-board variation dwarfs every model effect",
                 "One dot per board: its win rate over every game any pair played on it. "
                 "The thick bar is the style mean, the thin line its interquartile range. "
                 "Both runs pooled.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def fig_length_by_style(g):
    """Game length by style, and the decomposition that explains its shape."""
    done = g[g.outcome.isin(["win", "loss"])]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3))
    bins = np.arange(0.5, done.game_length.max() + 1.5, 1)
    for i, style in enumerate(STYLE_ORDER):
        sub = done[done.board_style == style]
        axes[0].hist(sub.game_length, bins=bins, histtype="step", lw=1.9,
                     color=STYLE_RAMP[i], density=True, zorder=3,
                     label=f"{style} — {board_note(sub)}")
    axes[0].set_xlabel("rounds played", fontsize=9)
    axes[0].set_ylabel("share of games", fontsize=9)
    axes[0].set_title("All games, by board style", fontsize=10, color=INK, loc="left", pad=8)
    axes[0].legend(frameon=False, fontsize=7.6, labelcolor=INK_2)
    pct_axis(axes[0])
    tidy(axes[0])

    for label, frame, color in [("wins", done[done.is_win == 1], SERIES[0]),
                                ("losses", done[done.is_win == 0], SERIES[1])]:
        axes[1].hist(frame.game_length, bins=bins, histtype="step", lw=1.9, color=color,
                     density=True, zorder=3, label=f"{label} ({len(frame):,} games)")
    axes[1].set_xlabel("rounds played", fontsize=9)
    axes[1].set_ylabel("share of games", fontsize=9)
    axes[1].set_title("The same games, split by outcome", fontsize=10, color=INK,
                      loc="left", pad=8)
    axes[1].legend(frameon=False, fontsize=8, labelcolor=INK_2)
    pct_axis(axes[1])
    tidy(axes[1])
    top = titles(fig, "How long a game lasts",
                 "Left: the three board styles sit almost on top of each other. Right: the "
                 "same games split into wins and losses — the spike at the short end is "
                 "entirely losses, and the hump is entirely wins.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def _first_guess_panels(g, r, models, title, subtitle):
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.4), sharey=True)
    done = g[g.outcome.isin(["win", "loss"])]
    for j, style in enumerate(STYLE_ORDER):
        ax = axes[j]
        rs = r[r.board_style == style]
        x = np.arange(len(models))
        w = 0.36
        hits = [rs[rs.cm == m].first_guess_hit.mean() for m in models]
        base = [rs[rs.cm == m].first_guess_baseline.mean() for m in models]
        ax.bar(x - w / 2, hits, width=w * 0.9,
               color=[model_colors(models)[m] for m in models], zorder=3)
        ax.bar(x + w / 2, base, width=w * 0.9, color=BASELINE, zorder=3)
        for xi, (h, b) in enumerate(zip(hits, base)):
            ax.text(xi - w / 2, h + 0.012, f"{h:.2f}", ha="center", va="bottom",
                    fontsize=7.6, color=INK)
            ax.text(xi + w / 2, b + 0.012, f"{b:.2f}", ha="center", va="bottom",
                    fontsize=7.6, color=INK_2)
            ax.text(xi, max(h, b) + 0.085, f"+{h - b:.2f}", ha="center", va="bottom",
                    fontsize=8.6, color=INK, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace("-instruct", "") for m in models], fontsize=7.6,
                           color=INK_2, rotation=20, ha="right")
        ax.set_title(f"{STYLE_LABEL[style].splitlines()[0]}\n"
                     f"{board_note(done[done.board_style == style])}",
                     fontsize=9.5, color=INK, pad=8)
        ax.set_ylim(0, 0.86)
        tidy(ax)
    axes[0].set_ylabel("share of first guesses on a target", fontsize=9)
    # The coloured bars carry model identity, so the legend has to name the
    # models — a single "observed" swatch would assert a colour no bar uses.
    cols = model_colors(models)
    handles = [Patch(facecolor=cols[m], label=f"{m} — observed") for m in models]
    handles.append(Patch(facecolor=BASELINE, label="chance, given the pool at that moment"))
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), frameon=False,
               fontsize=8.5, labelcolor=INK_2, bbox_to_anchor=(0.5, -0.02))
    top = titles(fig, title, subtitle)
    fig.tight_layout(rect=(0, 0.07, 1, top))
    return fig


def fig_first_guess_labeled(g, r):
    return _first_guess_panels(
        g, r, MODEL_ORDER,
        "First guess against chance, by codemaster and board style",
        "Coloured bar: how often the round's first guess landed on a target. Grey bar: the "
        "chance of that, given the words still standing. The bold number is the gap.")


def fig_first_guess_subset(g, r):
    gs = two_model_subset(g)
    keys = ["run_id", "model", "guesser_model", "method", "count_constraint",
            "board_style", "board_seed", "trial"]
    rs = r.merge(gs[keys].drop_duplicates(), on=keys, how="inner")
    return _first_guess_panels(
        gs, rs, SUBSET_MODELS,
        "First guess against chance — the two-model grid on all 450 boards",
        "gemini-2.5-flash and gpt-4o-mini in both roles, pooled over the factorial's 30 "
        "boards per style and the top-up's 120, so each column rests on 150 boards.")


def fig_ambition_free(g, r):
    """Clue ambition over the course of a game, free-choice arm only."""
    free = r[r.count_constraint == "free"]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    cols = model_colors(MODEL_ORDER)
    for m in MODEL_ORDER:
        s = free[free.cm == m]
        by_round = s.groupby("round")["count"].agg(["mean", "size"])
        by_round = by_round[(by_round["size"] >= 30) & (by_round.index <= 16)]
        ax.plot(by_round.index, by_round["mean"], lw=2, color=cols[m], label=m, zorder=3,
                marker="o", markersize=3.4)
    ax.set_xlabel("round", fontsize=9)
    ax.set_ylabel("mean clue number", fontsize=9)
    ax.set_xticks(range(2, 17, 2))
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK_2)
    tidy(ax)
    done = g[g.outcome.isin(["win", "loss"])]
    top = titles(fig, "Clue ambition falls as the board empties",
                 "Free-choice arm only, so nothing here is imposed by a floor. Points rest on "
                 f"at least 30 rounds. {done.board_seed.nunique() * 3} boards across the three "
                 "styles.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def fig_outcome_mix_subset(g):
    gs = two_model_subset(g)
    classes = ["win", "loss_assassin", "loss_opponent", "incomplete"]
    colors = dict(zip(classes, SERIES))
    fig, axes = plt.subplots(1, 3, figsize=(11.6, 4.4), sharey=True)
    for j, style in enumerate(STYLE_ORDER):
        ax = axes[j]
        sub = gs[gs.board_style == style]
        x = np.arange(len(SUBSET_MODELS))
        bottom = np.zeros(len(SUBSET_MODELS))
        for c in classes:
            vals = np.array([(sub[sub.gs == m].outcome_class == c).mean()
                             for m in SUBSET_MODELS])
            ax.bar(x, vals, bottom=bottom, width=0.5, color=colors[c], zorder=3,
                   edgecolor=SURFACE, linewidth=2, label=OUTCOME_LABEL[c] if j == 0 else None)
            for xi, (b, v) in enumerate(zip(bottom, vals)):
                if v > 0.05:
                    ax.text(xi, b + v / 2, f"{v:.0%}", ha="center", va="center",
                            fontsize=8, color="white")
            bottom += vals
        ax.set_xticks(x)
        ax.set_xticklabels(SUBSET_MODELS, fontsize=8.2, color=INK_2)
        ax.set_title(f"{STYLE_LABEL[style].splitlines()[0]}\n{board_note(sub)}",
                     fontsize=9.5, color=INK, pad=8)
        ax.set_ylim(0, 1)
        pct_axis(ax)
        tidy(ax)
    axes[0].set_ylabel("share of games", fontsize=9)
    axes[0].set_xlabel("guesser", fontsize=9)
    fig.legend(loc="lower center", ncol=4, frameon=False, fontsize=8.5, labelcolor=INK_2,
               bbox_to_anchor=(0.5, -0.02))
    top = titles(fig, "How games end — the two-model grid on all 450 boards",
                 "gemini-2.5-flash and gpt-4o-mini in both roles, pooled over both runs. "
                 "Columns are board style; bars are the guesser.")
    fig.tight_layout(rect=(0, 0.07, 1, top))
    return fig



# The six ambiguous words the report walks through. Each has two unrelated
# readings of one unvocalized written form, which is the phenomenon the whole
# project is about.
GLOSS_WORDS = ["מטר", "מלח", "כבד", "קל", "אלים", "אלה"]


def english_pair_frame(g, r):
    """The pair table in the column order of Table I of the English benchmark."""
    raw = pair_table(g, r).copy()
    raw["cm"] = raw["model"].map(short)
    raw["gs"] = raw["guesser_model"].map(short)
    raw["_c"] = raw["cm"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    raw["_g"] = raw["gs"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    raw = raw.sort_values(["_c", "_g"], ignore_index=True)

    def pair(m, s, fmt="{:.2f}"):
        return [f"{fmt.format(a)} ({fmt.format(b)})" for a, b in zip(raw[m], raw[s])]

    out = pd.DataFrame({
        "Model pair (codemaster – guesser)": raw["cm"] + " – " + raw["gs"],
        "Games": [f"{n:,}" for n in raw["games"]],
        "Mean": [f"{v:.2f}" for v in raw["length_mean"]],
        "Median": [f"{v:.0f}" for v in raw["length_median"]],
        "Min": [f"{v:.0f}" for v in raw["length_min"]],
        "Std Dev": [f"{v:.2f}" for v in raw["length_sd"]],
        "Loss": [f"{v:.0%}" for v in raw["loss_rate"]],
        "Mean (without loss)": [f"{v:.2f}" for v in raw["length_mean_wins"]],
        "Opponent avg(sd)": pair("opponent_mean", "opponent_sd"),
        "Civilian avg(sd)": pair("civilian_mean", "civilian_sd"),
        "Clues avg(sd)": pair("clue_count_mean", "clue_count_sd"),
        "Guesses avg(sd)": pair("guesses_mean", "guesses_sd"),
        "Stop Early": [f"{v:.1%}" for v in raw["stop_early_rate"]],
        "Stop Late": [f"{v:.1%}" for v in raw["stop_late_rate"]],
    })
    return out


def fig_pair_table_english(g, r):
    out = english_pair_frame(g, r)
    fig, ax = plt.subplots(figsize=(15.4, 5.6))
    ax.axis("off")
    # The pair name needs roughly twice a data column; equal widths truncate it.
    n_data = len(out.columns) - 1
    widths = [0.175] + [(1 - 0.175) / n_data] * n_data
    tbl = ax.table(cellText=out.values.tolist(), colLabels=list(out.columns),
                   loc="center", cellLoc="center", colWidths=widths)
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.4)
    tbl.scale(1, 1.5)
    for (rr, cc), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_linewidth(0.6)
        if rr == 0:
            cell.set_facecolor("#f0efec")
            cell.set_text_props(color=INK, fontweight="bold")
        else:
            # A rule between codemaster blocks, as the paper prints it.
            cell.set_facecolor(SURFACE if ((rr - 1) // 4) % 2 == 0 else "#f7f6f3")
            cell.set_text_props(color=INK_2)
        if cc == 0:
            cell.set_text_props(ha="left")
    top = titles(fig, "Agent results for the single-team Hebrew version",
                 "One row per codemaster–guesser pair, in the column order of Table I of the "
                 "English benchmark, ordered by codemaster then guesser. Length columns are "
                 "rounds; Opponent and Civilian are words revealed per game; Stop Early and "
                 "Stop Late are over eligible rounds.")
    fig.tight_layout(rect=(0, 0, 1, top))
    return fig


def fig_gloss(g, r):
    """Which English sense each codemaster reaches for, for six ambiguous words."""
    counts = gloss_counts([f"results/{FACTORIAL}"], words=GLOSS_WORDS)
    shares = sense_shares(counts)
    models = [m for m in sorted(shares.model.unique(),
                                key=lambda x: MODEL_ORDER.index(short(x)))]
    rounds = int(shares["rounds"].sum())
    unrel = float((shares["share_unrelated"] * shares["rounds"]).sum() / rounds)
    fig = plots.gloss_sense_split(
        shares, GLOSS_WORDS, models,
        title="Which English sense does each codemaster reach for?",
        subtitle=f"English-Pivot rounds on the factorial — {rounds:,} board-word glosses. "
                 f"Grey = the model named both senses; a bar short of full width means it "
                 f"named neither ({unrel:.0%} overall).",
    )
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
    # The selected set.
    "fig21_factors_separately": ("factorial", lambda g, r: fig_factors_separately(g)),
    "fig22_board_variance": ("pooled", lambda g, r: fig_board_variance(g)),
    "fig23_first_guess_labeled": ("factorial", fig_first_guess_labeled),
    "fig24_ambition_free": ("factorial", fig_ambition_free),
    "fig25_factors_subset": ("pooled", lambda g, r: fig_factors_separately(
        two_model_subset(g), SUBSET_MODELS,
        title="The two designed factors — the two-model grid on all 450 boards",
        subtitle="The same two panels as Figure 4, for gemini-2.5-flash and gpt-4o-mini "
                 "in both roles, pooled over both runs. Five times the boards behind each "
                 "ambiguity bar.")),
    "fig26_first_guess_subset": ("pooled", fig_first_guess_subset),
    "fig27_pair_table_english": ("factorial", fig_pair_table_english),
    "fig28_gloss_sense_split": ("factorial", fig_gloss),
}


# The run-report figures (`codenames_heb.plots`) that earn a place in the paper.
# Each is a stratified grid — it shows an effect *inside* every cell of the
# design rather than averaged over it, which is exactly what the pooled figures
# above cannot show. The ones left out duplicate a pooled figure.
RUN_FIGURES = {
    "fig12_win_rate_full_grid": "04_win_rate_by_guesser",
    "fig13_win_rate_by_floor": "03_win_rate_by_floor",
    "fig14_outcome_mix_by_guesser": "06_outcome_mix_by_guesser",
    "fig15_length_distribution": "02_game_length",
    "fig16_first_guess_vs_chance": "09_first_guess_vs_chance",
    "fig17_ambition_by_round": "11_count_by_round",
    "fig18_self_consistency": "12_self_consistency",
    "fig19_cross_model_agreement": "13_cross_model_agreement",
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

    # The stratified grids, rendered off the factorial run for the same
    # balance reason the pooled figures use it.
    factorial = load_runs([RUNS[0]])
    for name, key in RUN_FIGURES.items():
        fig = plots.FIGURES[key](factorial)
        if fig is None:
            print("skipped", name)
            continue
        path = out / f"{name}.png"
        fig.savefig(path, dpi=170, bbox_inches="tight")
        plt.close(fig)
        print("wrote", path)


if __name__ == "__main__":
    main(*sys.argv[1:])
