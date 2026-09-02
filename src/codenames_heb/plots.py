"""Figures for a run, all stratified by board style.

Board style is the experiment's designed independent variable, so it is a
facet in every figure rather than the subject of one plot. `facet_by_style`
imposes a single layout — one column per style, shared y-axis, codemasters on
the x-axis — so the figures can be read against each other without re-learning
the axes each time. `facet_grid` extends that to two dimensions: the same
columns, with one *row* per level of a second assigned factor (the clue-count
floor, or the guesser). A grid is the only honest way to show a factor the
design crosses — collapsing it averages over a treatment that was deliberately
varied, and an effect that reverses across the rows disappears entirely.

Every figure prints n **per bar**, not per facet: a bar is what anyone reads
off the chart, and a panel-level n overstates the evidence behind each column
by the number of bars in it. In the 2026-08-16 run a model x method x style bar
rests on 5 games; on M4 the same bar rests on ~360, and a bar of the 3x3 floor
grid on ~120. At the small end the figures show direction only;
`analysis.scaling_projection` says what n makes them conclusive.
"""

from __future__ import annotations

from typing import Callable, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from codenames_heb import agreement as _agreement  # noqa: E402
from codenames_heb.analysis import (  # noqa: E402
    style_order,
    summarize,
)

FACET_WIDTH = 4.3
FACET_HEIGHT = 3.7
# Grid rows are shorter than a standalone facet row: a 3x3 or 3x4 grid at the
# full height is taller than it is wide, which no page wants.
GRID_ROW_HEIGHT = 3.1

# Fixed colours so a model keeps its colour across every figure — and across
# every figure in the *paper*, which is why the mapping lives in `palette`
# rather than here.
from codenames_heb.palette import colors_for as _palette_colors_for  # noqa: E402
_OUTCOME_COLORS = {"win": "#2e7d32", "loss": "#c62828", "failed": "#9e9e9e"}
_METHOD_HATCH = {"strong_hebrew": "", "translate_pipeline": "//"}


def short_model(name) -> str:
    """`meta-llama/llama-3.3-70b-instruct` -> `llama-3.3-70b-instruct`."""
    if not isinstance(name, str):
        return str(name)
    return name.split("/")[-1].replace(":free", "")


def _model_order(df: pd.DataFrame) -> list:
    return sorted(df["model"].dropna().unique())


def _method_order(df: pd.DataFrame) -> list:
    return sorted(df["method"].dropna().unique()) or ["-"]


def _level_order(df: pd.DataFrame, column: str) -> list:
    return sorted(df[column].dropna().unique())


def _varies(df: pd.DataFrame, column: str) -> bool:
    return column in df.columns and df[column].nunique(dropna=False) > 1


def _actor_column(df: pd.DataFrame) -> str:
    """Which model a guesser-side figure should be grouped by.

    Stops, misses and bonus guesses are the guesser's decisions, so a crossed
    run attributes them to the guesser. A fixed-guesser run has only one, and
    grouping by it would collapse the figure to a single bar — there the
    codemaster is the only thing varying.
    """
    return "guesser_model" if _varies(df, "guesser_model") else "model"


def _colors_for(models: Sequence) -> dict:
    return _palette_colors_for(models)


def annotate_n(ax, positions, counts, *, y, fontsize: int = 7, color: str = "#555555"):
    """Print the n behind each bar/box, next to that bar.

    The facet as a whole is not the unit anyone reads off these charts — a bar
    is. Labelling the panel instead of the bar overstates the evidence behind
    each column by the number of bars in it.

    `color` exists for the figures that stack several n rows under one panel:
    three grey rows of numbers say nothing about which row belongs to which
    line, so there the row takes its line's colour.
    """
    for x, n in zip(positions, counts):
        if n is None or (isinstance(n, float) and pd.isna(n)):
            continue
        ax.annotate(
            f"{int(n)}", (x, y), ha="center", va="bottom",
            fontsize=fontsize, color=color, clip_on=False,
        )


# --- the clue-count floor ladder -----------------------------------------
#
# Declared before the facet helpers because `facet_grid` has to order a row of
# floors, and string order draws that ladder wrong.

# The floors are a designed ladder, so they get a ramp rather than the
# categorical model palette: free is neutral, and the numeric floors darken as
# they tighten.
_FREE_COLOR = "#90a4ae"
_FLOOR_RAMP = ("#4db6ac", "#00897b", "#00695c", "#004d40")

# A point on the clue-count-by-round figure needs this many rounds behind it to
# be drawn. Late rounds only exist in the games that ran long, so without a
# floor every panel ends on a tail traced by one or two games.
MIN_ROUNDS_PER_POINT = 5


def count_floor_order(values: Iterable) -> list:
    """`free` first, then the numeric floors in numeric order.

    Plain `sorted()` is string order, which puts `min10` between `free` and
    `min2` and draws the ladder out of sequence. Unrecognised labels sort last
    rather than raising, so an older run with a hand-edited arm still plots.
    """
    def key(label):
        text = str(label)
        if text == "free":
            return (0, 0, "")
        if text.startswith("min") and text[3:].isdigit():
            return (1, int(text[3:]), "")
        return (2, 0, text)

    return sorted({str(v) for v in values}, key=key)


def _floor_levels(df: pd.DataFrame) -> list:
    """The clue-count floors this frame can actually contrast."""
    if "count_constraint" not in df.columns:
        return []
    return count_floor_order(df["count_constraint"].dropna().unique())


def _floor_colors(floors: Sequence) -> dict:
    numeric = [f for f in floors if f != "free"]
    colors = {"free": _FREE_COLOR}
    for i, floor in enumerate(numeric):
        colors[floor] = _FLOOR_RAMP[i % len(_FLOOR_RAMP)]
    return colors


# --- layout --------------------------------------------------------------

# What a row of a grid is called, and how its levels are ordered. Anything not
# listed falls back to plain sorted order.
_ROW_LABELS = {
    "count_constraint": "clue-count floor",
    "guesser_model": "guesser",
    "method": "prompt method",
    "model": "codemaster",
}


def _row_levels(df: pd.DataFrame, column: str) -> list:
    """The levels a grid row factor takes, in the order they should be read."""
    if column not in df.columns:
        return []
    values = df[column].dropna().unique()
    if column == "count_constraint":
        return count_floor_order(values)
    return sorted(values)


def _style_levels(df: pd.DataFrame) -> list:
    return style_order(df["board_style"].dropna().unique()) or ["unspecified"]


def _figure_titles(fig, title: str, subtitle: str, *, y: float, gap: float):
    """Suptitle plus an optional grey subtitle above it.

    tight_layout is unaware of figure-level text placed above y=1, so the
    titles go on afterwards; saving with bbox_inches="tight" (and the inline
    backend's equivalent default) grows the canvas to include them.
    """
    if subtitle:
        fig.suptitle(title, fontsize=12, y=y + gap)
        fig.text(0.5, y, subtitle, ha="center", fontsize=8.5, color="#555555")
    else:
        fig.suptitle(title, fontsize=12, y=y)


def _figure_legend(fig, legend_handles, *, y: float = -0.02):
    if not legend_handles:
        return
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, y),
        ncol=min(len(legend_handles), 6),
        frameon=False,
        fontsize=9,
    )


def facet_by_style(
    df: pd.DataFrame,
    plot_fn: Callable,
    *,
    title: str,
    ylabel: str,
    sharey: bool = True,
    legend_handles: Sequence | None = None,
    subtitle: str = "",
    panel_width: float = FACET_WIDTH,
    **kwargs,
):
    """One column per board style, shared axes, uniform titles.

    Applied to every figure so board style is always visible as a dimension
    and never silently collapsed away. The facet title carries the style only:
    the n that matters is printed per bar by `plot_fn`, because that is the
    number each comparison actually rests on.
    """
    styles = _style_levels(df)

    fig, axes = plt.subplots(
        1,
        len(styles),
        figsize=(panel_width * len(styles), FACET_HEIGHT),
        sharey=sharey,
        squeeze=False,
    )
    for ax, style in zip(axes[0], styles):
        subset = df[df["board_style"] == style]
        plot_fn(ax, subset, **kwargs)
        ax.set_title(style, fontsize=10)
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        for label in ax.get_xticklabels():
            label.set_ha("right")

    axes[0][0].set_ylabel(ylabel)
    fig.tight_layout()
    _figure_titles(fig, title, subtitle, y=1.045 if subtitle else 1.05, gap=0.085)
    _figure_legend(fig, legend_handles)
    return fig


def facet_grid(
    df: pd.DataFrame,
    plot_fn: Callable,
    *,
    row_col: str,
    title: str,
    ylabel: str,
    sharey: bool = True,
    legend_handles: Sequence | None = None,
    subtitle: str = "",
    panel_width: float = FACET_WIDTH,
    row_height: float = GRID_ROW_HEIGHT,
    **kwargs,
):
    """`facet_by_style`, plus one row per level of `row_col`.

    Returns None when `row_col` has fewer than two levels: a one-row "grid" is
    the plain faceted figure under a heading that promises a contrast the run
    cannot make.

    The x tick labels are drawn on the bottom row only. Every panel shares the
    same categories by construction, so repeating four rotated model names
    under all nine or twelve panels spends a third of the canvas restating the
    axis. The row's own level is named down the right-hand edge instead of in
    each panel title, which keeps the column titles reading as board styles all
    the way across.
    """
    rows = _row_levels(df, row_col)
    if len(rows) < 2:
        return None
    styles = _style_levels(df)

    fig, axes = plt.subplots(
        len(rows),
        len(styles),
        figsize=(panel_width * len(styles), row_height * len(rows)),
        sharey=sharey,
        sharex=True,
        squeeze=False,
    )
    for ri, row in enumerate(rows):
        for ci, style in enumerate(styles):
            ax = axes[ri][ci]
            subset = df[(df["board_style"] == style) & (df[row_col].astype(str) == str(row))]
            plot_fn(ax, subset, **kwargs)
            if ri == 0:
                ax.set_title(style, fontsize=10)
            if ri == len(rows) - 1:
                ax.tick_params(axis="x", labelrotation=45, labelsize=8)
                for label in ax.get_xticklabels():
                    label.set_ha("right")
            else:
                ax.tick_params(axis="x", labelbottom=False)
        axes[ri][0].set_ylabel(ylabel)
        axes[ri][-1].annotate(
            short_model(row),
            xy=(1.015, 0.5), xycoords="axes fraction",
            rotation=-90, ha="left", va="center", fontsize=10, color="#333333",
        )

    fig.tight_layout()
    row_note = f"rows = {_ROW_LABELS.get(row_col, row_col)}; columns = board style"
    _figure_titles(
        fig,
        title,
        f"{row_note}. {subtitle}" if subtitle else row_note,
        # The taller the figure, the smaller a fixed fraction of it a title
        # band is; scaling keeps the gap looking the same on a 3-row and a
        # 4-row grid.
        y=1 + 0.055 * 3 / len(rows),
        gap=0.045 * 3 / len(rows),
    )
    _figure_legend(fig, legend_handles, y=-0.012 * 3 / len(rows))
    return fig


def _grouped_bars(ax, categories, series, colors, errors=None, hatches=None) -> dict:
    """Bars grouped by `categories`, one bar per entry in `series`.

    Returns {series name: x positions}. Where the n behind each bar differs
    within a group — one model may have played fewer games under one clue-count
    floor than another — the caller needs the bar's own x to label it, and
    recomputing this offset arithmetic at the call site would let the two
    drift apart.
    """
    n = len(series)
    width = 0.8 / max(n, 1)
    positions = range(len(categories))
    placed = {}
    for i, (name, values) in enumerate(series.items()):
        offsets = [p - 0.4 + width * (i + 0.5) for p in positions]
        placed[name] = offsets
        ax.bar(
            offsets,
            values,
            width=width,
            label=name,
            color=colors.get(name, "#888888"),
            yerr=errors.get(name) if errors else None,
            capsize=2,
            hatch=hatches.get(name, "") if hatches else "",
            edgecolor="white",
            linewidth=0.4,
        )
    ax.set_xticks(list(positions))
    ax.set_xticklabels([short_model(c) for c in categories])
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    return placed


def _legend(labels_colors, hatch=None):
    from matplotlib.patches import Patch

    return [
        Patch(facecolor=color, label=label, hatch=(hatch or {}).get(label, ""))
        for label, color in labels_colors.items()
    ]


def _method_legend(methods: Sequence) -> list:
    return _legend({m: "#ffffff" for m in methods}, hatch=_METHOD_HATCH)


# --- panel painters ------------------------------------------------------
#
# One painter per panel *kind*, shared by the plain faceted figure and its
# grid. The levels are passed in from the whole frame rather than read off the
# panel's own subset: a grid cell that happens to hold no games for one model
# must still leave that model's slot empty, or the panels stop lining up and
# the grid can no longer be read down a column.


def _paint_outcome_stack(ax, subset, *, models, methods):
    """Win / loss / failure shares, one stack per codemaster x method."""
    width = 0.8 / len(methods)
    positions, counts = [], []
    for mi, method in enumerate(methods):
        for xi, model in enumerate(models):
            cell = subset[(subset["model"] == model) & (subset["method"] == method)]
            total = len(cell) or 1
            bottom = 0.0
            x = xi - 0.4 + width * (mi + 0.5)
            for group in ("win", "loss", "failed"):
                share = (cell["outcome_group"] == group).sum() / total
                ax.bar(x, share, width=width * 0.92, bottom=bottom,
                       color=_OUTCOME_COLORS[group], edgecolor="white", linewidth=0.4,
                       hatch=_METHOD_HATCH.get(method, ""))
                bottom += share
            positions.append(x)
            counts.append(len(cell))
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([short_model(m) for m in models])
    ax.set_xlim(-0.6, len(models) - 0.4)
    ax.set_ylim(0, 1.14)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    annotate_n(ax, positions, counts, y=1.02, fontsize=6.5)


def _paint_win_rate(ax, subset, *, models, methods, colors):
    """Win rate with a Wilson 95% interval, one bar per codemaster x method.

    Wilson rather than Wald: a cell that went 4-for-4 has a Wald SE of exactly
    0, which draws as certainty. The bar keeps its *model's* colour and takes
    the method's hatch, so the same model is the same colour in this figure as
    in every other one and the method is still separable within the group.
    """
    width = 0.8 / len(methods)
    if subset.empty:
        stats = None
    else:
        stats = summarize(
            subset, ["model", "method"], ["is_win"], proportions=["is_win"]
        ).set_index(["model", "method"])

    for mi, method in enumerate(methods):
        offsets = [xi - 0.4 + width * (mi + 0.5) for xi in range(len(models))]
        if stats is None:
            rows = pd.DataFrame(
                index=range(len(models)),
                columns=["n", "is_win_mean", "is_win_lo", "is_win_hi"],
                dtype="float64",
            )
        else:
            rows = stats.reindex([(model, method) for model in models])
        mean = rows["is_win_mean"].astype("float64")
        lo = (mean - rows["is_win_lo"].astype("float64").fillna(mean)).clip(lower=0)
        hi = (rows["is_win_hi"].astype("float64").fillna(mean) - mean).clip(lower=0)
        ax.bar(
            offsets,
            mean.fillna(0.0).to_numpy(),
            width=width * 0.92,
            color=[colors[model] for model in models],
            hatch=_METHOD_HATCH.get(method, ""),
            yerr=[lo.fillna(0.0).to_numpy(), hi.fillna(0.0).to_numpy()],
            capsize=2,
            edgecolor="white",
            linewidth=0.4,
        )
        annotate_n(ax, offsets, rows["n"].fillna(0).to_numpy(), y=1.02, fontsize=6.5)

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([short_model(m) for m in models])
    ax.set_xlim(-0.6, len(models) - 0.4)
    ax.set_ylim(0, 1.14)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)


def _paint_length_boxes(ax, subset, *, models, methods, top):
    """Game length, one box per codemaster x method x outcome.

    Outcome stays split for the reason `fig_game_length` gives: a game ends
    either when all 9 targets are found or when the assassin is hit, so a
    pooled box cannot tell an efficient win from an early death. Colour carries
    the outcome and hatch the method, the same code as everywhere else.
    """
    series = [(method, outcome) for method in methods for outcome in ("win", "loss")]
    width = 0.8 / len(series)
    positions, counts = [], []
    for si, (method, outcome) in enumerate(series):
        for xi, model in enumerate(models):
            values = subset[
                (subset["model"] == model)
                & (subset["method"] == method)
                & (subset["outcome"] == outcome)
            ]["game_length"].dropna()
            position = xi - 0.4 + width * (si + 0.5)
            positions.append(position)
            counts.append(len(values))
            if values.empty:
                continue
            box = ax.boxplot(
                values, positions=[position], widths=width * 0.8, patch_artist=True,
                medianprops={"color": "black", "linewidth": 1.0},
                flierprops={"markersize": 2.5, "alpha": 0.4},
            )
            for patch in box["boxes"]:
                patch.set_facecolor(_OUTCOME_COLORS[outcome])
                patch.set_alpha(0.65)
                patch.set_hatch(_METHOD_HATCH.get(method, ""))
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([short_model(m) for m in models])
    ax.set_xlim(-0.6, len(models) - 0.4)
    ax.set_ylim(0, top * 1.16)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    # Wins and losses split a cell unevenly, so every box needs its own n.
    annotate_n(ax, positions, counts, y=top * 1.03, fontsize=6)


# --- 1-2. the two headline figures, and their grids ----------------------


def _with_outcome_group(games: pd.DataFrame) -> pd.DataFrame:
    """`win` / `loss` / `failed`, keeping failures visible.

    A model that cannot emit a legal clue is failing in a different way than
    one that hits the assassin, and collapsing the two flatters it.
    """
    frame = games.copy()
    frame["outcome_group"] = frame["outcome"].where(
        frame["outcome"].isin(["win", "loss"]), "failed"
    )
    return frame


def _outcome_legend(methods: Sequence) -> list:
    return _legend(_OUTCOME_COLORS) + _method_legend(methods)


def fig_outcome_composition(games: pd.DataFrame):
    """Win / loss / failure mix, codemaster x method, faceted by style."""
    frame = _with_outcome_group(games)
    models, methods = _model_order(games), _method_order(games)
    return facet_by_style(
        frame,
        _paint_outcome_stack,
        models=models,
        methods=methods,
        title="Game outcome by codemaster and prompt method (hatched = translate_pipeline)",
        ylabel="share of games",
        subtitle="number above each bar = games behind that bar",
        legend_handles=_outcome_legend(methods),
    )


def fig_outcome_grid(games: pd.DataFrame, row_col: str):
    """`fig_outcome_composition`, split a second way.

    The same nine or twelve panels the report's tables cover, drawn: the
    columns are still board style, and the rows are the factor named by
    `row_col` — the clue-count floor, or the guesser. Both are assigned
    treatments the design crosses, so averaging over either is averaging over
    something the experiment deliberately varied.
    """
    frame = _with_outcome_group(games)
    models, methods = _model_order(games), _method_order(games)
    label = _ROW_LABELS.get(row_col, row_col)
    return facet_grid(
        frame,
        _paint_outcome_stack,
        row_col=row_col,
        models=models,
        methods=methods,
        title=f"Game outcome by codemaster, prompt method, board style and {label}",
        ylabel="share of games",
        subtitle="hatched = translate_pipeline; number above each bar = games behind it",
        legend_handles=_outcome_legend(methods),
        panel_width=FACET_WIDTH * 1.05,
    )


def fig_win_rate_grid(games: pd.DataFrame, row_col: str):
    """Win rate alone, on the same grid as `fig_outcome_grid`.

    The stacked figure answers "what happened"; this one answers "how often did
    they win, and how sure are we". Dropping the loss/failure split buys the
    room for an interval, and a bar whose height starts at a common zero is a
    far easier comparison across nine or twelve panels than the middle band of
    a stack.
    """
    completed = games[games["completed"]]
    if completed.empty:
        return None
    models, methods = _model_order(completed), _method_order(completed)
    colors = _colors_for(models)
    label = _ROW_LABELS.get(row_col, row_col)
    return facet_grid(
        completed,
        _paint_win_rate,
        row_col=row_col,
        models=models,
        methods=methods,
        colors=colors,
        title=f"Win rate by codemaster, prompt method, board style and {label}",
        ylabel="win rate",
        subtitle="Wilson 95% bars, completed games only; hatched = "
                 "translate_pipeline; number above each bar = games behind it",
        legend_handles=_legend({short_model(m): colors[m] for m in models})
        + _method_legend(methods),
        panel_width=FACET_WIDTH * 1.05,
    )


def fig_game_length(games: pd.DataFrame):
    """Length split by outcome and prompt method.

    Outcome and length are confounded: a game ends either when all 9 targets
    are found or when the assassin is hit, so a short game is an efficient win
    *or* an early death. Method is split out too, because it is the other
    thing the codemaster side of the design varies and pooling it here would
    make this the one game-level figure that hides it.
    """
    completed = games[games["completed"]]
    models, methods = _model_order(completed), _method_order(completed)
    top = completed["game_length"].max()
    return facet_by_style(
        completed,
        _paint_length_boxes,
        models=models,
        methods=methods,
        top=top,
        title="Game length (rounds) by outcome and prompt method — completed games only",
        ylabel="rounds",
        subtitle="hatched = translate_pipeline; number above each box = games in that box",
        legend_handles=_legend({k: v for k, v in _OUTCOME_COLORS.items() if k != "failed"})
        + _method_legend(methods),
        panel_width=FACET_WIDTH * 1.5,
    )


def fig_game_length_grid(games: pd.DataFrame, row_col: str):
    """`fig_game_length`, split a second way — the length companion to
    `fig_win_rate_grid`.

    Sixteen boxes to a panel is a lot, and the alternative was worse: pooling
    the outcomes to halve them would hide whether a floor that shortens games
    is winning faster or dying sooner, which is the whole question length is
    asked to answer.
    """
    completed = games[games["completed"]]
    if completed.empty:
        return None
    models, methods = _model_order(completed), _method_order(completed)
    label = _ROW_LABELS.get(row_col, row_col)
    return facet_grid(
        completed,
        _paint_length_boxes,
        row_col=row_col,
        models=models,
        methods=methods,
        # From the whole frame, so every panel of the grid is on one scale.
        top=completed["game_length"].max(),
        title=f"Game length (rounds) by codemaster, prompt method, board style and {label}",
        ylabel="rounds",
        subtitle="completed games only; colour = outcome, hatch = prompt method; "
                 "number above each box = games in it",
        legend_handles=_legend({k: v for k, v in _OUTCOME_COLORS.items() if k != "failed"})
        + _method_legend(methods),
        panel_width=FACET_WIDTH * 1.55,
        row_height=GRID_ROW_HEIGHT * 1.05,
    )


# --- 9. first guess against chance ---------------------------------------


_FIRST_GUESS_COLORS = {
    "observed first guess on a target": "#1565c0",
    "chance, given the pool at that point": "#b0bec5",
}


def fig_first_guess_vs_chance(games: pd.DataFrame):
    """The sharpest codemaster signal in the data, drawn against its baseline.

    The first guess of a round is the one the clue is most responsible for,
    before the guesser has any feedback to work from — and it separates the
    models several times more sharply than win rate does.

    It is shown as observed *next to* chance rather than as the difference,
    because the difference alone is unreadable without knowing what it is a
    difference from: the baseline is not the board's opening 9/25, it is the
    pool as it stood when that round began, and it moves with board style and
    with how long the game ran. Both bars are per-game means first, so a
    13-round game does not outweigh a 5-round one; the gap between them is the
    lift, printed above each pair.
    """
    completed = games[games["completed"]]
    metrics = list(_FIRST_GUESS_COLORS)
    columns = {"first_guess_hit": metrics[0], "first_guess_baseline": metrics[1]}
    if completed.empty or not set(columns) <= set(completed.columns):
        return None

    models = _model_order(completed)

    def draw(ax, subset):
        stats = (
            summarize(subset, ["model"], list(columns))
            .set_index("model")
            .reindex(models)
        )
        placed = _grouped_bars(
            ax,
            models,
            {label: stats[f"{column}_mean"].to_numpy() for column, label in columns.items()},
            _FIRST_GUESS_COLORS,
            errors={
                label: stats[f"{column}_se"].to_numpy() for column, label in columns.items()
            },
        )
        # Both bars are proportions, so the axis runs to 1 — but nothing here
        # gets near it, and a panel that is half empty air makes a 0.35 gap
        # look smaller than it is. Cropped to just above the n row instead.
        ax.set_ylim(0, 1.08)
        annotate_n(ax, range(len(models)), stats["first_guess_hit_n"].to_numpy(), y=0.98)
        # The lift is the gap, and a gap is hard to measure by eye across three
        # panels — so it is also stated, over the pair it belongs to.
        hit = stats["first_guess_hit_mean"]
        chance = stats["first_guess_baseline_mean"]
        for xi, model in enumerate(models):
            lift = hit.get(model)
            if lift is None or pd.isna(lift) or pd.isna(chance.get(model)):
                continue
            gap = lift - chance[model]
            ax.annotate(
                f"{gap:+.2f}",
                (sum(xs[xi] for xs in placed.values()) / len(placed), max(lift, chance[model]) + 0.04),
                ha="center", va="bottom", fontsize=7.5, color="#1565c0",
            )

    return facet_by_style(
        completed,
        draw,
        title="First guess of a round vs the chance of guessing right (SE bars)",
        ylabel="share of first guesses on a target",
        subtitle="per-game means; blue number = lift over chance; "
                 "grey number above each pair = completed games behind it",
        legend_handles=_legend(_FIRST_GUESS_COLORS),
        panel_width=FACET_WIDTH * 1.15,
    )


# --- 10. the codemaster x guesser grid ----------------------------------


_PAIR_METRICS = (
    ("first_guess_lift", "first-guess lift", "viridis"),
    ("is_win", "win rate", "magma"),
)


def fig_pair_matrix(games: pd.DataFrame):
    """Every codemaster against every guesser, one cell per pair.

    The only figure that shows an *interaction*, which is the whole reason for
    crossing the guesser: reading down a column asks whether one guesser
    flatters every codemaster equally, and reading across a row asks whether a
    codemaster's skill survives a change of partner. The leading diagonal is
    self-play and is outlined, because "did the model do better with itself"
    is a different question from the rest of the grid and should not have to be
    found by counting.

    Cells are noisy by construction — a 4x4 grid splits a run sixteen ways, so
    each cell holds a sixteenth of the games. The margins are the numbers to
    read; an individual cell running hot or cold is usually not evidence. Both
    are drawn: the margin means come from the underlying games, not from
    averaging the four cell means, so an unbalanced run (M4 pooled with M5,
    where only two of the four models play) still reports each model's true
    mean rather than one that silently reweights its partners.
    """
    completed = games[games["completed"]]
    if completed.empty or not _varies(completed, "guesser_model"):
        return None

    metrics = [m for m in _PAIR_METRICS if m[0] in completed.columns]
    if not metrics:
        return None

    codemasters = _level_order(completed, "model")
    guessers = _level_order(completed, "guesser_model")
    margin = len(guessers), len(codemasters)  # x, y of the margin strip

    fig, axes = plt.subplots(
        1,
        len(metrics),
        figsize=(FACET_WIDTH * 1.7 * len(metrics), FACET_HEIGHT * 1.45),
        squeeze=False,
    )
    for ax, (metric, label, cmap) in zip(axes[0], metrics):
        cell = completed.pivot_table(
            index="model", columns="guesser_model", values=metric, aggfunc="mean"
        ).reindex(index=codemasters, columns=guessers)
        counts = completed.pivot_table(
            index="model", columns="guesser_model", values=metric, aggfunc="count"
        ).reindex(index=codemasters, columns=guessers)

        image = ax.imshow(cell.to_numpy(), cmap=cmap, aspect="auto")
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.12)

        for r in range(len(codemasters)):
            for c in range(len(guessers)):
                value = cell.to_numpy()[r, c]
                if pd.isna(value):
                    continue
                n = counts.to_numpy()[r, c]
                # Label colour flips with cell darkness so it stays readable.
                norm = image.norm(value)
                ax.text(
                    c, r, f"{value:.2f}\nn={int(n)}",
                    ha="center", va="center", fontsize=7.5,
                    color="white" if norm < 0.55 else "black",
                )

        _draw_pair_margins(ax, completed, metric, codemasters, guessers, margin)

        ax.set_xticks(list(range(len(guessers))) + [margin[0]])
        ax.set_xticklabels(
            [short_model(g) for g in guessers] + ["all guessers"],
            rotation=30, ha="right", fontsize=8,
        )
        ax.set_yticks(list(range(len(codemasters))) + [margin[1]])
        ax.set_yticklabels(
            [short_model(m) for m in codemasters] + ["all codemasters"], fontsize=8
        )
        ax.set_xlabel("guesser")
        ax.set_ylabel("codemaster")
        ax.set_title(f"mean {label} per pair", fontsize=11)

    fig.suptitle(
        "Codemaster x Guesser — does the ranking survive a change of partner?",
        fontsize=12, y=1.03,
    )
    fig.text(
        0.5, 0.985,
        "outlined = self-play; the margin strip is each model's mean over all "
        "its partners, taken from the games rather than from the cell means",
        ha="center", fontsize=8.5, color="#555555",
    )
    fig.tight_layout()
    return fig


def _draw_pair_margins(ax, completed, metric, codemasters, guessers, margin):
    """The row and column means, in a strip outside the grid.

    Taken by grouping the games, not by averaging the row of cell means: those
    two agree only when every cell holds the same number of games, and a pooled
    or partially-run design breaks that. The strip is drawn as plain text on a
    neutral background rather than as more heatmap, so it cannot be misread as
    another pair.
    """
    from matplotlib.patches import Rectangle

    margin_x, margin_y = margin
    ax.set_xlim(-0.5, margin_x + 0.5)
    ax.set_ylim(margin_y + 0.5, -0.5)

    rows = completed.groupby("model")[metric].agg(["mean", "count"]).reindex(codemasters)
    cols = completed.groupby("guesser_model")[metric].agg(["mean", "count"]).reindex(guessers)
    overall = completed[metric].agg(["mean", "count"])

    def strip(x, y, stat):
        ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor="#eceff1",
                               edgecolor="white", linewidth=1.0, zorder=2))
        if pd.isna(stat["mean"]):
            return
        ax.text(x, y, f"{stat['mean']:.2f}\nn={int(stat['count'])}",
                ha="center", va="center", fontsize=7.5, color="#263238", zorder=3)

    for r, model in enumerate(codemasters):
        strip(margin_x, r, rows.loc[model])
    for c, guesser in enumerate(guessers):
        strip(c, margin_y, cols.loc[guesser])
    strip(margin_x, margin_y, overall)

    # Self-play: the same model in both seats. Outlined rather than coloured so
    # it does not compete with the metric the colour is carrying.
    for r, model in enumerate(codemasters):
        if model in guessers:
            ax.add_patch(Rectangle(
                (guessers.index(model) - 0.5, r - 0.5), 1, 1,
                fill=False, edgecolor="white", linewidth=2.2, zorder=4,
            ))


# --- 11. clue count over the course of a game ----------------------------


def fig_count_by_round(rounds: pd.DataFrame):
    """Clue ambition against turn number, one line per floor, one panel per
    codemaster.

    The question the floors were introduced to answer is whether they keep
    biting. The dashed companion line is the mean `required_count` — the floor
    actually in force after it is capped to the targets still hidden — so a
    solid line tracking its own dashed line means the model is being held at
    the floor, and the dashed line falling away late is the endgame cap, not
    the model losing nerve.

    Board style is collapsed here. Every style plays every floor, so the
    contrast this figure draws survives the pooling; keeping style as a facet
    as well would put twelve panels on one row.

    Unlike the floor *grids*, this figure draws on a single-arm run too. The
    grids exist to contrast the floors and collapse to a bar when there is only
    one; this one's subject is how ambition decays over a game, and a run that
    fixed the floor still has that shape to show — it just shows it as one line
    per panel. A run predating the floors gets a single unlabelled line.
    """
    if rounds.empty:
        return None
    floors = _floor_levels(rounds)
    if floors:
        frame = rounds
    else:
        # Pre-M4: no arm was assigned, so there is one implicit line to draw.
        frame, floors = rounds.assign(count_constraint="all"), ["all"]

    models = _model_order(frame)
    colors = _floor_colors(floors)
    stats = summarize(
        frame, ["model", "count_constraint", "round"], ["count", "required_count"]
    )
    stats = stats[stats["count_n"] >= MIN_ROUNDS_PER_POINT]
    if stats.empty:
        return None

    se = stats["count_se"].fillna(0)
    top = float((stats["count_mean"] + se).max()) * 1.15

    # One tick ladder for every panel. Panels are read against each other, and
    # left to itself matplotlib ticks a 14-round panel every 2 rounds, a
    # 19-round one every 2.5 and a 20-round one every 5 — so the same
    # horizontal distance would mean a different number of rounds in each.
    last_round = int(stats["round"].max())
    step = next(s for s in (1, 2, 5, 10, 20, 50, 100) if last_round / s <= 10)
    ticks = list(range(step, last_round + 1, step))
    # A band below the axis for the per-point n, one row per floor — the same
    # idea as the numbers-at-risk table under a survival curve. Stacking the
    # rows inside the panel would put them through the lines.
    band = top * 0.09 * (len(floors) + 0.6)

    fig, axes = plt.subplots(
        1, max(len(models), 1),
        figsize=(FACET_WIDTH * max(len(models), 1) * 1.05, FACET_HEIGHT * 1.15),
        sharey=True, sharex=True, squeeze=False,
    )
    for ax, model in zip(axes[0], models):
        for fi, floor in enumerate(floors):
            line = stats[
                (stats["model"] == model) & (stats["count_constraint"] == floor)
            ].sort_values("round")
            if line.empty:
                continue
            xs = line["round"].to_numpy()
            mean = line["count_mean"].to_numpy()
            spread = line["count_se"].fillna(0).to_numpy()
            ax.plot(xs, mean, marker="o", linestyle="-", linewidth=1.7,
                    markersize=4.5, color=colors[floor], label=floor)
            ax.fill_between(xs, mean - spread, mean + spread,
                            color=colors[floor], alpha=0.15, linewidth=0)
            if "required_count_mean" in line.columns:
                floor_line = line.dropna(subset=["required_count_mean"])
                if not floor_line.empty:
                    ax.plot(floor_line["round"].to_numpy(),
                            floor_line["required_count_mean"].to_numpy(),
                            linestyle="--", linewidth=1.2, color=colors[floor])
            # Only at the ticks: a 20-round panel a few inches wide cannot fit
            # twenty three-digit labels in a row, and printing them all turns
            # the row into an unreadable smear.
            shown = line[line["round"].isin(ticks)]
            annotate_n(ax, shown["round"].to_numpy(), shown["count_n"].to_numpy(),
                       y=-top * 0.09 * (fi + 1.1), fontsize=6.5, color=colors[floor])

        ax.set_title(short_model(model), fontsize=10)
        ax.set_ylim(-band, top)
        ax.set_yticks([t for t in ax.get_yticks() if t >= 0])
        ax.set_xticks(ticks)
        ax.set_xlim(0.3, last_round + 0.7)
        ax.hlines(0, *ax.get_xlim(), color="#bdbdbd", linewidth=0.8)
        ax.grid(axis="y", alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_xlabel("round", fontsize=9)

    axes[0][0].set_ylabel("clue count (ambition)")
    ladder = len(floors) > 1
    fig.suptitle(
        "Clue ambition by turn number and clue-count floor (SE band)"
        if ladder
        else "Clue ambition by turn number (SE band)",
        fontsize=12, y=1.10,
    )
    fig.text(
        0.5, 1.025,
        "dashed = the floor actually in force after the endgame cap; numbers "
        f"under each panel = rounds behind the ticked points (points below "
        f"{MIN_ROUNDS_PER_POINT} rounds dropped)",
        ha="center", fontsize=8.5, color="#555555",
    )
    # One line needs no key telling the reader which line it is — unless the
    # run named its single arm, in which case the name is worth carrying.
    if floors != ["all"]:
        fig.legend(
            handles=_legend({floor: colors[floor] for floor in floors}),
            loc="upper center", bbox_to_anchor=(0.5, -0.02),
            ncol=min(len(floors), 4), frameon=False, fontsize=9,
        )
    fig.tight_layout()
    return fig


# --- 12-13. round-1 agreement -------------------------------------------

# The self_jaccard marker rides on top of the unanimity bar, so it needs to
# read against every model colour rather than belong to one.
_JACCARD_MARKER = "#212121"


def _paint_self_consistency(ax, subset, *, models, methods, colors):
    """Unanimity as the bar, target-set agreement as the marker above it.

    Both are needed. The bar answers "did it give the same clue"; the marker
    answers "did it aim at the same words". A low bar under a high marker is a
    model rewording one stable idea, which is a different failure from a model
    that cannot decide what to point at.
    """
    width = 0.8 / len(methods)
    stats = (
        None if subset.empty
        else summarize(
            subset, ["model", "method"], ["is_unanimous", "self_jaccard"],
            proportions=["is_unanimous"],
        ).set_index(["model", "method"])
    )

    for mi, method in enumerate(methods):
        offsets = [xi - 0.4 + width * (mi + 0.5) for xi in range(len(models))]
        if stats is None:
            rows = pd.DataFrame(
                index=range(len(models)),
                columns=["n", "is_unanimous_mean", "self_jaccard_mean"],
                dtype="float64",
            )
        else:
            rows = stats.reindex([(model, method) for model in models])
        ax.bar(
            offsets,
            rows["is_unanimous_mean"].astype("float64").fillna(0.0).to_numpy(),
            width=width * 0.92,
            color=[colors[model] for model in models],
            hatch=_METHOD_HATCH.get(method, ""),
            edgecolor="white",
            linewidth=0.4,
        )
        ax.plot(
            offsets,
            rows["self_jaccard_mean"].astype("float64").to_numpy(),
            linestyle="None", marker="D", markersize=4,
            color=_JACCARD_MARKER,
        )
        annotate_n(ax, offsets, rows["n"].fillna(0).to_numpy(), y=1.02, fontsize=6.5)

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([short_model(m) for m in models])
    ax.set_xlim(-0.6, len(models) - 0.4)
    ax.set_ylim(0, 1.14)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)


def fig_self_consistency_grid(rounds: pd.DataFrame, row_col: str):
    """Does a codemaster reproduce its own round-1 clue from an identical prompt?

    Round 1 is the only controlled point in the run: `revealed` is empty, so the
    prompt is fixed by (board, model, method, floor) and the guesser cannot have
    influenced it. The four guesser-runs of a cell are four draws from one
    byte-identical prompt.
    """
    cells = _agreement.self_consistency(rounds)
    # A cell with fewer than 2 draws cannot score as unanimous or not, so a
    # grid built entirely from such cells would show scores with no evidence
    # behind them.
    if cells.empty or cells["n_draws"].max() < 2:
        return None
    models, methods = _model_order(cells), _method_order(cells)
    colors = _colors_for(models)
    label = _ROW_LABELS.get(row_col, row_col)
    return facet_grid(
        cells,
        _paint_self_consistency,
        row_col=row_col,
        models=models,
        methods=methods,
        colors=colors,
        title=f"Round-1 self-consistency by codemaster, board style and {label}",
        ylabel="share / Jaccard",
        subtitle="bar = share of cells giving one clue every time; diamond = mean "
                 "target-set Jaccard; hatched = translate_pipeline; number above "
                 "each bar = replicate cells behind it",
        legend_handles=(
            _legend({short_model(m): colors[m] for m in models})
            + _method_legend(methods)
        ),
        panel_width=FACET_WIDTH * 1.05,
    )


_AGREEMENT_METRICS = {
    "clue agreement": ("pairwise_clue_agreement", "#00695c"),
    "target Jaccard": ("pairwise_target_jaccard", "#7b1fa2"),
}


def _paint_cross_model_agreement(ax, subset, *, methods):
    """Cross-codemaster agreement, one bar pair per prompt method.

    There is no per-model value to plot: agreement is a property of the panel,
    not of one codemaster. Prompt method takes the x-axis instead.
    """
    width = 0.8 / len(_AGREEMENT_METRICS)
    stats = (
        None if subset.empty
        else summarize(
            subset, ["method"],
            [column for column, _ in _AGREEMENT_METRICS.values()],
        ).set_index("method")
    )

    for mi, (label, (column, color)) in enumerate(_AGREEMENT_METRICS.items()):
        offsets = [xi - 0.4 + width * (mi + 0.5) for xi in range(len(methods))]
        if stats is None:
            values = [float("nan")] * len(methods)
            counts = [0] * len(methods)
        else:
            rows = stats.reindex(methods)
            values = rows[f"{column}_mean"].astype("float64").fillna(0.0).to_numpy()
            counts = rows["n"].fillna(0).to_numpy()
        ax.bar(offsets, values, width=width * 0.92, color=color,
               edgecolor="white", linewidth=0.4)
        annotate_n(ax, offsets, counts, y=1.02, fontsize=6.5)

    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(list(methods))
    ax.set_xlim(-0.6, len(methods) - 0.4)
    ax.set_ylim(0, 1.14)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)


def fig_cross_model_agreement_grid(rounds: pd.DataFrame, row_col: str):
    """Do the codemasters converge on the same round-1 clue?

    Pairs are cross-codemaster only, so a model's own repeats cannot inflate
    the number.
    """
    panels = _agreement.panel_agreement(rounds)
    if panels.empty:
        return None
    methods = _method_order(panels)
    label = _ROW_LABELS.get(row_col, row_col)
    return facet_grid(
        panels,
        _paint_cross_model_agreement,
        row_col=row_col,
        methods=methods,
        title=f"Round-1 agreement across codemasters, by board style and {label}",
        ylabel="cross-codemaster agreement",
        subtitle="pairs from different codemasters only; number above each bar "
                 "= board panels behind it",
        legend_handles=_legend(
            {label: color for label, (_, color) in _AGREEMENT_METRICS.items()}
        ),
        panel_width=FACET_WIDTH * 1.05,
    )


# The registry, in reading order. Figures that a run cannot support return
# None and are skipped: the guesser grids need a crossed run, the floor grids
# need more than one arm, and the pair matrix needs both.
FIGURES = {
    "01_outcome_composition": lambda data: fig_outcome_composition(data.games),
    "02_game_length": lambda data: fig_game_length(data.games),
    "03_win_rate_by_floor": lambda data: fig_win_rate_grid(data.games, "count_constraint"),
    "04_win_rate_by_guesser": lambda data: fig_win_rate_grid(data.games, "guesser_model"),
    "05_outcome_mix_by_floor": lambda data: fig_outcome_grid(data.games, "count_constraint"),
    "06_outcome_mix_by_guesser": lambda data: fig_outcome_grid(data.games, "guesser_model"),
    "07_game_length_by_floor": lambda data: fig_game_length_grid(
        data.games, "count_constraint"
    ),
    "08_game_length_by_guesser": lambda data: fig_game_length_grid(
        data.games, "guesser_model"
    ),
    "09_first_guess_vs_chance": lambda data: fig_first_guess_vs_chance(data.games),
    "10_pair_matrix": lambda data: fig_pair_matrix(data.games),
    "11_count_by_round": lambda data: fig_count_by_round(data.rounds),
    "12_self_consistency": lambda data: fig_self_consistency_grid(
        data.rounds, "count_constraint"
    ),
    "13_cross_model_agreement": lambda data: fig_cross_model_agreement_grid(
        data.rounds, "count_constraint"
    ),
}


def save_all(data, out_dir, dpi: int = 150) -> dict:
    """Render every figure into `out_dir`, returning {name: path}."""
    from pathlib import Path

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = {}
    for name, build in FIGURES.items():
        fig = build(data)
        if fig is None:  # e.g. a fixed-guesser run has no pair grid to draw
            continue
        path = out_dir / f"{name}.png"
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        saved[name] = path
    return saved


# --- Gloss figures -------------------------------------------------------
#
# These two answer one question — which English sense does each model default
# to for an ambiguous Hebrew word — and they are a pair on purpose: the chart
# shows the lean, the table shows the words behind it. The chart is a diverging
# stacked bar because the reader's job is polarity (which side of the sense
# boundary a model sits on), and diverging is the form for polarity.
#
# Palette: the diverging blue<->red pair, validated (worst adjacent CVD ΔE 21.6
# protan on the light surface). The neutral midpoint is stepped from the
# documented `#f0efec` to the neutral-family `#c3c2b7`: "both senses named" is a
# fifth of gemini's mass, and at #f0efec on a near-white surface that segment is
# invisible. Same family, still unmistakably not-a-hue, so it still reads as the
# midpoint.

GLOSS_SENSE_A = "#2a78d6"
GLOSS_SENSE_B = "#e34948"
GLOSS_BOTH = "#c3c2b7"
GLOSS_SURFACE = "#fcfcfb"
GLOSS_INK = "#0b0b0b"
GLOSS_INK_2 = "#52514e"
GLOSS_MUTED = "#898781"
GLOSS_RULE = "#e4e3de"


def _renderable(gloss: str) -> str:
    """Glosses are drawn in DejaVu Sans, which covers Latin and Hebrew but no
    CJK. A model that answered in another script is a real observation, so say
    so instead of drawing an empty box."""
    return gloss if all(ord(ch) < 0x0590 for ch in gloss) else "(non-Latin script)"
# The surface gap between touching stacked segments, in share units.
_GAP = 0.004


def _sense_frame(shares, words, models):
    order = {w: i for i, w in enumerate(words)}
    frame = shares[shares["word"].isin(order)].copy()
    frame["_w"] = frame["word"].map(order)
    frame["_m"] = frame["model"].map({m: i for i, m in enumerate(models)})
    return frame.sort_values(["_w", "_m"], ignore_index=True)


def gloss_sense_split(shares, words, models, *, title=None, subtitle=None,
                      font_scale: float = 1.0, ncols: int = 3):
    """Diverging stacked bars: which sense each model defaults to, per word.

    One panel per word, one bar per model. The bar is centred on the midpoint of
    the "both senses named" segment, so the two arms are comparable across
    models even when the hedge width differs. Segments are shares of *all*
    rounds and are deliberately not renormalised — where a model glossed the
    word as neither sense the bar is simply short, and that missing length is
    labelled rather than hidden.
    """
    frame = _sense_frame(shares, words, models)

    def fs(size: float) -> float:
        """A point size, scaled for the caller's output size."""
        return size * font_scale

    ncols = max(1, min(ncols, len(words)))
    nrows = -(-len(words) // ncols)
    # Row height follows the type: at font_scale 2 a two-line model label is
    # twice as tall, and a fixed 0.42in row runs the labels together.
    row_h = 0.42 * max(1.0, font_scale * 0.8)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(4.6 * ncols, row_h * len(models) * nrows + 1.15 * nrows),
        squeeze=False,
    )
    fig.patch.set_facecolor(GLOSS_SURFACE)

    for idx, word in enumerate(words):
        ax = axes[idx // ncols][idx % ncols]
        ax.set_facecolor(GLOSS_SURFACE)
        rows = frame[frame["word"] == word]
        if rows.empty:
            ax.axis("off")
            continue
        a_label = rows["sense_a"].iloc[0]
        b_label = rows["sense_b"].iloc[0]
        tick_labels = []
        for j, model in enumerate(models):
            row = rows[rows["model"] == model]
            if row.empty:
                tick_labels.append(short_model(model))
                continue
            row = row.iloc[0]
            y = -j
            half = row["share_both"] / 2
            # Left arm runs out from the midpoint of `both`, right arm from the
            # same point, so the two arms stay comparable however wide the hedge.
            if row["share_a"] > 0:
                ax.barh(y, row["share_a"] - _GAP, left=-half - row["share_a"], height=0.62,
                        color=GLOSS_SENSE_A, zorder=3)
            if half > 0:
                ax.barh(y, half - _GAP / 2, left=-half, height=0.62, color=GLOSS_BOTH,
                        zorder=3)
                ax.barh(y, half - _GAP / 2, left=_GAP / 2, height=0.62, color=GLOSS_BOTH,
                        zorder=3)
            if row["share_b"] > 0:
                ax.barh(y, row["share_b"] - _GAP, left=half + _GAP, height=0.62,
                        color=GLOSS_SENSE_B, zorder=3)
            # The unrelated share is the bar's missing length. Naming it on the
            # model label keeps it off the plot area, where it collided with the
            # very bars whose shortness it explains.
            label = short_model(model)
            if row["share_unrelated"] >= 0.02:
                label += f"\n{row['share_unrelated']:.0%} neither sense"
            tick_labels.append(label)
        ax.axvline(0, color=GLOSS_INK_2, lw=0.9, zorder=4)
        ax.set_xlim(-1.02, 1.02)
        ax.set_ylim(-len(models) + 0.45, 0.55)
        ax.set_yticks([-j for j in range(len(models))])
        ax.set_yticklabels(tick_labels, fontsize=fs(7.4), color=GLOSS_INK_2)
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        # Only the ends are labelled. The axis is symmetric about the midpoint
        # and the inner marks sit close enough to collide once the type is
        # scaled for print; the gridlines still carry the 50% positions.
        ax.set_xticklabels(["100%", "", "", "", "100%"], fontsize=fs(6.4),
                           color=GLOSS_MUTED)
        ax.set_title(f"{word}      {a_label} ‹ › {b_label}", fontsize=fs(9.5), color=GLOSS_INK,
                     pad=6)
        ax.tick_params(length=0)
        for side in ("top", "right", "left", "bottom"):
            ax.spines[side].set_visible(False)
        ax.grid(axis="x", color=GLOSS_RULE, lw=0.7, zorder=0)
        ax.set_axisbelow(True)

    for idx in range(len(words), nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=GLOSS_SENSE_A),
        plt.Rectangle((0, 0), 1, 1, color=GLOSS_BOTH),
        plt.Rectangle((0, 0), 1, 1, color=GLOSS_SENSE_B),
    ]
    fig.legend(handles, ["first sense (left label)", "both named — the model hedged",
                         "second sense (right label)"],
               loc="lower center", ncol=3, frameon=False, fontsize=fs(8.5),
               bbox_to_anchor=(0.5, 0.002))
    # Title block placed in inches, not figure fractions: a two-row grid is
    # about half the height of a four-row one, and a fixed fraction puts the
    # subtitle through the title on the short one.
    height = fig.get_figheight()
    top = 1.0
    if title:
        fig.text(0.5, 1 - 0.24 / height, title, ha="center", va="top", fontsize=fs(13),
                 color=GLOSS_INK)
        top = 1 - 0.46 / height
    if subtitle:
        y = 1 - (0.52 if title else 0.24) / height
        fig.text(0.5, y, subtitle, ha="center", va="top", fontsize=fs(8.5),
                 color=GLOSS_INK_2, wrap=True)
        top = 1 - ((0.94 if title else 0.62) / height)
    # Reserve the legend's height in inches, not as a fraction: a one-row grid
    # is little more than half the height of a two-row one, and a fixed 0.045
    # leaves the legend sitting on top of the axis labels.
    fig.tight_layout(rect=(0, 0.52 / height, 1, top))
    return fig


def gloss_table(counts, words, models, *, k=3, title=None, subtitle=None):
    """The same data as a table figure: top glosses per model, per word.

    The chart collapses each cell to a sense lean; this keeps the actual English
    strings, which is what makes the finding checkable. A small square carries
    sense identity beside each gloss — colour on the mark, never on the text.
    """
    from codenames_heb.glosses import BOTH, SENSES, UNRELATED, classify, top_glosses

    tops = top_glosses(counts, k=k)
    lookup = {(r["model"], r["word"]): r for _, r in tops.iterrows()}

    row_h, head_h = 0.86, 0.62
    col_w = 2.62
    label_w = 1.05
    # Deep enough that the subtitle clears the column headers below it.
    title_band = 1.02 if title else 0.16
    fig_w = label_w + col_w * len(models)
    fig_h = title_band + head_h + row_h * len(words) + 0.55
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(GLOSS_SURFACE)
    ax.set_facecolor(GLOSS_SURFACE)
    # The axes fill the figure and carry inch-for-inch coordinates, so every
    # row lands where the layout arithmetic above puts it. tight_layout would
    # rescale that and reopen the gap under the title.
    ax.set_position((0, 0, 1, 1))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    if title:
        ax.text(fig_w / 2, fig_h - 0.24, title, fontsize=13, color=GLOSS_INK,
                ha="center", va="center")
    if subtitle:
        ax.text(fig_w / 2, fig_h - 0.5, subtitle, fontsize=8.5, color=GLOSS_INK_2,
                ha="center", va="center")

    top = fig_h - title_band
    for j, model in enumerate(models):
        ax.text(label_w + col_w * j + 0.06, top + 0.1, short_model(model),
                fontsize=9, color=GLOSS_INK, fontweight="semibold")
    ax.plot([0.04, fig_w - 0.04], [top - 0.06, top - 0.06], color=GLOSS_INK_2, lw=1.0)

    for i, word in enumerate(words):
        y = top - head_h - row_h * i
        if i % 2 == 1:
            ax.add_patch(plt.Rectangle((0.04, y - row_h + 0.24), fig_w - 0.08, row_h,
                                       color="#f6f5f2", zorder=0))
        (a_label, _), (b_label, _) = SENSES[word]
        ax.text(0.1, y, word, fontsize=12, color=GLOSS_INK, va="top")
        ax.text(0.1, y - 0.3, f"{a_label} / {b_label}", fontsize=6.6,
                color=GLOSS_MUTED, va="top")
        for j, model in enumerate(models):
            rec = lookup.get((model, word))
            x = label_w + col_w * j + 0.06
            if rec is None:
                ax.text(x, y, "—", fontsize=8, color=GLOSS_MUTED, va="top")
                continue
            ax.text(x, y, f"{rec['n_glosses']} distinct", fontsize=7,
                    color=GLOSS_INK_2, va="top")
            for line, (gloss, _, share) in enumerate(rec["top"]):
                gy = y - 0.235 - 0.185 * line
                sense = classify(word, gloss)
                color = {a_label: GLOSS_SENSE_A, b_label: GLOSS_SENSE_B,
                         BOTH: GLOSS_BOTH, UNRELATED: GLOSS_MUTED}[sense]
                ax.add_patch(plt.Rectangle((x, gy - 0.045), 0.075, 0.075, color=color,
                                           zorder=3))
                shown = _renderable(gloss)
                shown = shown if len(shown) <= 22 else shown[:21] + "…"
                ax.text(x + 0.115, gy, shown, fontsize=7.2, color=GLOSS_INK, va="center")
                # A real but rare gloss must not print as a flat 0%.
                pct = f"{share:.0%}" if round(share * 100) >= 1 else "<1%"
                ax.text(x + col_w - 0.16, gy, pct, fontsize=7.2,
                        color=GLOSS_INK_2, va="center", ha="right")
        ax.plot([0.04, fig_w - 0.04], [y - row_h + 0.22, y - row_h + 0.22],
                color=GLOSS_RULE, lw=0.6, zorder=1)

    keys = [("first sense", GLOSS_SENSE_A), ("second sense", GLOSS_SENSE_B),
            ("both named", GLOSS_BOTH), ("neither sense", GLOSS_MUTED)]
    x = 0.1
    for label, color in keys:
        ax.add_patch(plt.Rectangle((x, 0.2), 0.085, 0.085, color=color, zorder=3))
        ax.text(x + 0.13, 0.243, label, fontsize=7.4, color=GLOSS_INK_2, va="center")
        x += 0.13 + 0.115 * len(label)
    return fig
