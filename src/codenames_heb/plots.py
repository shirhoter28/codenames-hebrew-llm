"""Figures for a run, all stratified by board style.

Board style is the experiment's designed independent variable, so it is a
facet in every figure rather than the subject of one plot. `facet_by_style`
imposes a single layout — one column per style, shared y-axis, models on the
x-axis — so the figures can be read against each other without re-learning the
axes each time.

Every figure prints n **per bar**, not per facet: a bar is what anyone reads
off the chart, and a panel-level n overstates the evidence behind each column
by the number of bars in it. In the 2026-08-16 run a model x method x style bar
rests on 5 games. At this scale the figures show direction;
`analysis.scaling_projection` says what n makes them conclusive.
"""

from __future__ import annotations

from typing import Callable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from codenames_heb.analysis import (  # noqa: E402
    STOP_CLASSES,
    dual_miss_lift,
    style_order,
    summarize,
)

FACET_WIDTH = 4.3
FACET_HEIGHT = 3.7

# Fixed colours so a model keeps its colour across every figure.
_MODEL_COLORS = plt.get_cmap("tab10").colors
_OUTCOME_COLORS = {"win": "#2e7d32", "loss": "#c62828", "failed": "#9e9e9e"}
_METHOD_HATCH = {"strong_hebrew": "", "translate_pipeline": "//"}

# Ordered so the stack reads worst-to-best from the bottom.
_STOP_COLORS = {
    "miss_before_quota": "#c62828",
    "miss_on_bonus_guess": "#ef6c00",
    "early_stop_true": "#fbc02d",
    "stopped_at_quota": "#2e7d32",
    "bonus_taken_correct": "#1565c0",
    "game_won_midround": "#7b1fa2",
    "guesser_failure": "#616161",
    "no_quota": "#bdbdbd",
}


def short_model(name) -> str:
    """`meta-llama/llama-3.3-70b-instruct` -> `llama-3.3-70b-instruct`."""
    if not isinstance(name, str):
        return str(name)
    return name.split("/")[-1].replace(":free", "")


def _model_order(df: pd.DataFrame) -> list:
    return sorted(df["model"].dropna().unique())


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
    return {m: _MODEL_COLORS[i % len(_MODEL_COLORS)] for i, m in enumerate(models)}


def annotate_n(ax, positions, counts, *, y, fontsize: int = 7):
    """Print the n behind each bar/box, next to that bar.

    The facet as a whole is not the unit anyone reads off these charts — a bar
    is. Labelling the panel instead of the bar overstates the evidence behind
    each column by the number of bars in it.
    """
    for x, n in zip(positions, counts):
        if n is None or (isinstance(n, float) and pd.isna(n)):
            continue
        ax.annotate(
            f"{int(n)}", (x, y), ha="center", va="bottom",
            fontsize=fontsize, color="#555555", clip_on=False,
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
    **kwargs,
):
    """One column per board style, shared axes, uniform titles.

    Applied to every figure so board style is always visible as a dimension
    and never silently collapsed away. The facet title carries the style only:
    the n that matters is printed per bar by `plot_fn`, because that is the
    number each comparison actually rests on.
    """
    styles = style_order(df["board_style"].dropna().unique())
    if not styles:
        styles = ["unspecified"]

    fig, axes = plt.subplots(
        1,
        len(styles),
        figsize=(FACET_WIDTH * len(styles), FACET_HEIGHT),
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
    # tight_layout is unaware of figure-level text placed above y=1, so the
    # titles go on afterwards; saving with bbox_inches="tight" (and the inline
    # backend's equivalent default) grows the canvas to include them.
    fig.tight_layout()
    if subtitle:
        fig.suptitle(title, fontsize=12, y=1.13)
        fig.text(0.5, 1.045, subtitle, ha="center", fontsize=8.5, color="#555555")
    else:
        fig.suptitle(title, fontsize=12, y=1.05)
    if legend_handles:
        fig.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=min(len(legend_handles), 6),
            frameon=False,
            fontsize=9,
        )
    return fig


def _grouped_bars(ax, categories, series, colors, errors=None, hatches=None):
    """Bars grouped by `categories`, one bar per entry in `series`."""
    n = len(series)
    width = 0.8 / max(n, 1)
    positions = range(len(categories))
    for i, (name, values) in enumerate(series.items()):
        offsets = [p - 0.4 + width * (i + 0.5) for p in positions]
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


def _legend(labels_colors, hatch=None):
    from matplotlib.patches import Patch

    return [
        Patch(facecolor=color, label=label, hatch=(hatch or {}).get(label, ""))
        for label, color in labels_colors.items()
    ]


# --- 1. outcome composition ---------------------------------------------


def fig_outcome_composition(games: pd.DataFrame):
    """Win / loss / failure mix, model x method, faceted by style.

    Failures are kept visible rather than dropped: a model that cannot emit a
    legal clue is failing in a different way than one that hits the assassin,
    and collapsing the two flatters it.
    """
    frame = games.copy()
    frame["outcome_group"] = frame["outcome"].where(
        frame["outcome"].isin(["win", "loss"]), "failed"
    )

    def draw(ax, subset):
        models = _model_order(games)
        methods = sorted(subset["method"].dropna().unique()) or ["-"]
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
        ax.set_ylim(0, 1.14)
        annotate_n(ax, positions, counts, y=1.02)

    handles = _legend(_OUTCOME_COLORS)
    handles += _legend({m: "#ffffff" for m in _METHOD_HATCH}, hatch=_METHOD_HATCH)
    return facet_by_style(
        frame,
        draw,
        title="Game outcome by model and prompt method (hatched = translate_pipeline)",
        ylabel="share of games",
        subtitle="number above each bar = games behind that bar",
        legend_handles=handles,
    )


# --- 2. game length ------------------------------------------------------


def fig_game_length(games: pd.DataFrame):
    """Length split by outcome, because the two are confounded: a game ends
    either when all 9 targets are found or when the assassin is hit, so a
    short game is an efficient win *or* an early death."""
    completed = games[games["completed"]]

    top = completed["game_length"].max()

    def draw(ax, subset):
        models = _model_order(completed)
        positions, counts = [], []
        for xi, model in enumerate(models):
            for oi, (outcome, color) in enumerate(
                (("win", _OUTCOME_COLORS["win"]), ("loss", _OUTCOME_COLORS["loss"]))
            ):
                values = subset[
                    (subset["model"] == model) & (subset["outcome"] == outcome)
                ]["game_length"].dropna()
                position = xi - 0.18 + 0.36 * oi
                positions.append(position)
                counts.append(len(values))
                if values.empty:
                    continue
                box = ax.boxplot(
                    values, positions=[position], widths=0.3, patch_artist=True,
                    medianprops={"color": "black", "linewidth": 1.2},
                    flierprops={"markersize": 3, "alpha": 0.5},
                )
                for patch in box["boxes"]:
                    patch.set_facecolor(color)
                    patch.set_alpha(0.65)
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels([short_model(m) for m in models])
        ax.set_xlim(-0.6, len(models) - 0.4)
        ax.set_ylim(0, top * 1.16)
        # Wins and losses split the 10 games behind each model unevenly, so
        # every box needs its own n.
        annotate_n(ax, positions, counts, y=top * 1.04)

    return facet_by_style(
        completed,
        draw,
        title="Game length (rounds) by outcome — completed games only",
        ylabel="rounds",
        subtitle="number above each box = games in that box",
        legend_handles=_legend({k: v for k, v in _OUTCOME_COLORS.items() if k != "failed"}),
    )


# --- 3. ambiguity ladder -------------------------------------------------


def fig_ambiguity_ladder(games: pd.DataFrame):
    """The one figure where style is the x-axis rather than the facet: win
    rate across the dual_0 -> dual_100 ladder, one line per model, split into
    a panel per prompt method."""
    completed = games[games["completed"]]
    styles = style_order(completed["board_style"].dropna().unique())
    methods = sorted(completed["method"].dropna().unique())
    models = _model_order(completed)
    colors = _colors_for(models)

    fig, axes = plt.subplots(
        1, len(methods) or 1,
        figsize=(FACET_WIDTH * max(len(methods), 1) * 1.15, FACET_HEIGHT),
        sharey=True, squeeze=False,
    )
    stats = summarize(completed, ["method", "board_style", "model"], ["is_win"])

    # Models frequently land on identical win rates at n=5 (0.6 and 0.6 draw
    # exactly on top of each other), so each series is nudged sideways.
    dodge = 0.07
    for ax, method in zip(axes[0], methods):
        for mi, model in enumerate(models):
            line = stats[(stats["method"] == method) & (stats["model"] == model)]
            line = line.set_index("board_style").reindex(styles)
            offset = (mi - (len(models) - 1) / 2) * dodge
            ax.errorbar(
                [x + offset for x in range(len(styles))],
                line["is_win_mean"],
                yerr=line["is_win_se"],
                marker="o", capsize=3, linewidth=1.6, markersize=5,
                color=colors[model], label=short_model(model),
            )
        ax.set_xticks(range(len(styles)))
        ax.set_xticklabels(styles, rotation=45, ha="right", fontsize=8)
        ax.set_title(method, fontsize=10)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(axis="y", alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)

    axes[0][0].set_ylabel("win rate")
    # n is the same at every point here (one model x method x style cell), so
    # it is stated once rather than printed 16 times.
    per_point = sorted(stats["is_win_n"].dropna().unique())
    n_note = (
        f"n = {int(per_point[0])} completed games per point"
        if len(per_point) == 1
        else f"n = {int(min(per_point))}–{int(max(per_point))} completed games per point"
    )
    fig.suptitle("Ambiguity ladder: win rate vs board style (SE bars)", fontsize=12, y=1.09)
    fig.text(0.5, 1.02, n_note, ha="center", fontsize=8.5, color="#555555")
    fig.legend(
        handles=_legend({short_model(m): colors[m] for m in models}),
        loc="upper center", bbox_to_anchor=(0.5, -0.02),
        ncol=min(len(models), 4), frameon=False, fontsize=9,
    )
    fig.tight_layout()
    return fig


# --- 4. stop behaviour ---------------------------------------------------


def fig_stop_behaviour(rounds: pd.DataFrame):
    """How each round ended, as within-model shares.

    Grouped by whoever is varying in the *guesser* seat: stopping early,
    taking the bonus guess and missing before quota are all the guesser's
    decisions, so a crossed run attributes them to the guesser rather than to
    the codemaster whose clue prompted them.

    Methods are collapsed here: eight stacked bars per facet is unreadable,
    and the method breakdown is available numerically in the round summary
    table.
    """
    present = [c for c in STOP_CLASSES if (rounds["stop_class"] == c).any()]
    actor = _actor_column(rounds)

    def draw(ax, subset):
        models = _level_order(rounds, actor)
        counts = []
        for xi, model in enumerate(models):
            cell = subset[subset[actor] == model]
            total = len(cell) or 1
            bottom = 0.0
            for cls in present:
                share = (cell["stop_class"] == cls).sum() / total
                ax.bar(xi, share, width=0.65, bottom=bottom, color=_STOP_COLORS[cls],
                       edgecolor="white", linewidth=0.4)
                bottom += share
            counts.append(len(cell))
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels([short_model(m) for m in models])
        ax.set_ylim(0, 1.14)
        annotate_n(ax, range(len(models)), counts, y=1.02)

    role = "guesser" if actor == "guesser_model" else "codemaster"
    return facet_by_style(
        rounds,
        draw,
        title=f"How rounds ended (stop taxonomy) by {role}",
        ylabel="share of rounds",
        subtitle="number above each bar = rounds behind that bar",
        legend_handles=_legend({c: _STOP_COLORS[c] for c in present}),
    )


# --- 5. intended-vs-hit overlap -----------------------------------------


def fig_intended_overlap(rounds: pd.DataFrame):
    """Agreement between the words the codemaster aimed at and the ones the
    guesser found."""
    metrics = {
        "intended_recall": "#1565c0",
        "intended_precision": "#2e7d32",
        "intended_jaccard": "#6a1b9a",
    }

    def draw(ax, subset):
        models = _model_order(rounds)
        stats = summarize(subset, ["model"], list(metrics)).set_index("model").reindex(models)
        _grouped_bars(
            ax,
            models,
            {m: stats[f"{m}_mean"].to_numpy() for m in metrics},
            {m: c for m, c in metrics.items()},
            errors={m: stats[f"{m}_se"].to_numpy() for m in metrics},
        )
        ax.set_ylim(0, 1.14)
        annotate_n(ax, range(len(models)), stats["n"].to_numpy(), y=1.02)

    return facet_by_style(
        rounds,
        draw,
        title="Intended targets vs targets actually hit (SE bars)",
        ylabel="rate",
        subtitle="number above each group = rounds behind that group "
        "(both prompt methods pooled, i.e. 10 games)",
        legend_handles=_legend(metrics),
    )


# --- 6. ambition vs yield ------------------------------------------------


def fig_ambition_vs_yield(rounds: pd.DataFrame):
    """Words the codemaster commits a clue to (`count`) against the targets
    that clue actually buys (`n_correct`). The gap is what a harder board
    costs, and whether a model shrinks its ambition to compensate."""
    metrics = {"count": "#455a64", "n_correct": "#00897b"}
    labels = {"count": "clue count (ambition)", "n_correct": "targets recovered (yield)"}

    top = summarize(rounds, ["model", "board_style"], ["count"])
    ceiling = float((top["count_mean"] + top["count_se"]).max()) * 1.08

    def draw(ax, subset):
        models = _model_order(rounds)
        stats = summarize(subset, ["model"], list(metrics)).set_index("model").reindex(models)
        _grouped_bars(
            ax,
            models,
            {labels[m]: stats[f"{m}_mean"].to_numpy() for m in metrics},
            {labels[m]: c for m, c in metrics.items()},
            errors={labels[m]: stats[f"{m}_se"].to_numpy() for m in metrics},
        )
        ax.set_ylim(0, ceiling * 1.06)
        annotate_n(ax, range(len(models)), stats["n"].to_numpy(), y=ceiling)

    return facet_by_style(
        rounds,
        draw,
        title="Clue ambition vs yield, per round (SE bars)",
        ylabel="words per round",
        subtitle="number above each group = rounds behind that group "
        "(both prompt methods pooled, i.e. 10 games)",
        legend_handles=_legend({labels[m]: c for m, c in metrics.items()}),
    )


# --- 7. dual-word miss lift ---------------------------------------------


def fig_dual_miss_lift(rounds: pd.DataFrame, boards: dict):
    """Does ambiguity actually pull the guesser off target?

    Observed share of first misses landing on a dual-list word against the
    board's own dual fraction. A lift of 1 means ambiguous words are hit at
    exactly their base rate — i.e. ambiguity is not the mechanism.
    """
    actor = _actor_column(rounds)
    lift = dual_miss_lift(rounds, boards, ["board_style", actor])
    lift = lift[lift["expected"] > 0]
    if lift.empty:
        return None

    styles = style_order(lift["board_style"].unique())
    models = sorted(lift[actor].unique())
    colors = _colors_for(models)

    fig, ax = plt.subplots(figsize=(FACET_WIDTH * 1.9, FACET_HEIGHT))
    width = 0.8 / max(len(models), 1)
    for mi, model in enumerate(models):
        rows = lift[lift[actor] == model].set_index("board_style").reindex(styles)
        offsets = [i - 0.4 + width * (mi + 0.5) for i in range(len(styles))]
        ax.bar(offsets, rows["observed"], width=width * 0.9, color=colors[model],
               label=short_model(model), edgecolor="white", linewidth=0.4)
        annotate_n(ax, offsets, rows["n_misses"].to_numpy(), y=1.01, fontsize=6.5)

    for i, style in enumerate(styles):
        expected = lift[lift["board_style"] == style]["expected"].iloc[0]
        ax.plot([i - 0.45, i + 0.45], [expected, expected], color="black",
                linestyle="--", linewidth=1.4,
                label="board dual fraction (chance)" if i == 0 else None)

    ax.set_xticks(range(len(styles)))
    ax.set_xticklabels(styles)
    ax.set_ylabel("share of first misses on a dual word")
    ax.set_ylim(0, 1.09)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Do misses prefer ambiguous words? Observed vs chance", fontsize=12, pad=18)
    ax.text(0.5, 1.02, "number above each bar = first misses behind that bar",
            transform=ax.transAxes, ha="center", fontsize=8.5, color="#555555")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1),
              ncol=min(len(models) + 1, 3), frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


def fig_first_guess_lift(games: pd.DataFrame):
    """How far the first guess of a round beats blind chance, per model.

    The per-model lines are drawn against the pooled average deliberately:
    pooling flattens this metric almost completely, because the models move in
    opposite directions across the ladder. Reading only the pooled line would
    say ambiguity does nothing, when what is actually happening is that the
    strongest model degrades and the weakest improves.
    """
    completed = games[games["completed"]]
    if "first_guess_lift" not in completed.columns:
        return None

    styles = style_order(completed["board_style"].dropna().unique())
    models = _model_order(completed)
    colors = _colors_for(models)
    stats = summarize(completed, ["board_style", "model"], ["first_guess_lift"])
    pooled = summarize(completed, ["board_style"], ["first_guess_lift"])

    fig, ax = plt.subplots(figsize=(FACET_WIDTH * 2.0, FACET_HEIGHT))
    # Wide enough that the per-point n labels underneath do not run together.
    dodge = 0.14
    for mi, model in enumerate(models):
        line = stats[stats["model"] == model].set_index("board_style").reindex(styles)
        offset = (mi - (len(models) - 1) / 2) * dodge
        ax.errorbar(
            [x + offset for x in range(len(styles))],
            line["first_guess_lift_mean"],
            yerr=line["first_guess_lift_se"],
            marker="o", capsize=3, linewidth=1.6, markersize=5,
            color=colors[model], label=short_model(model),
        )
        annotate_n(
            ax,
            [x + offset for x in range(len(styles))],
            line["first_guess_lift_n"].to_numpy(),
            y=-0.075,
            fontsize=6.5,
        )

    pooled_line = pooled.set_index("board_style").reindex(styles)
    ax.plot(range(len(styles)), pooled_line["first_guess_lift_mean"],
            color="black", linestyle="--", linewidth=1.8, marker="s", markersize=4,
            label="pooled (hides the cancellation)")
    ax.axhline(0, color="#999999", linewidth=1, zorder=0)

    ax.set_xticks(range(len(styles)))
    ax.set_xticklabels(styles)
    ax.set_ylabel("first-guess lift over chance")
    ax.set_ylim(-0.1, 0.7)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title(
        "First guess vs blind chance, per game then averaged (SE bars)",
        fontsize=12, pad=18,
    )
    ax.text(0.5, 1.02, "number under each point = completed games behind it",
            transform=ax.transAxes, ha="center", fontsize=8.5, color="#555555")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
              ncol=min(len(models) + 1, 3), frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


# --- 9. winning game length across the ladder ---------------------------


def fig_win_length_ladder(games: pd.DataFrame):
    """Rounds needed to win, across the dual_0 -> dual_100 ladder.

    The companion to `fig_ambiguity_ladder`, on the same axes: win rate says
    how often the pair finds all nine targets, this says how dearly. Losses
    are excluded rather than faceted because they end the moment the assassin
    is hit, so a lost game is short for the opposite reason a won game is —
    mixing the two makes ambiguity look free (see `fig_game_length`).

    n moves a lot from point to point here, since a cell contributes only its
    wins and a model can win nothing at all on a hard style, so every point
    carries its own n instead of the single figure-level note fig 3 can use.
    """
    completed = games[games["completed"]]
    wins = completed[completed["is_win"] == 1.0]
    if wins.empty:
        return None

    styles = style_order(completed["board_style"].dropna().unique())
    methods = sorted(completed["method"].dropna().unique())
    # Models come from the completed games, not the wins, so a model that
    # never won still gets its colour slot and shows up as an explicit 0.
    models = _model_order(completed)
    colors = _colors_for(models)

    stats = summarize(wins, ["method", "board_style", "model"], ["game_length"])
    se = stats["game_length_se"].fillna(0)
    # Zero-based like `fig_game_length`: rounds are a magnitude, and cropping
    # the axis to the data would inflate gaps of a round or two into cliffs.
    top = float((stats["game_length_mean"] + se).max()) * 1.12

    fig, axes = plt.subplots(
        1, len(methods) or 1,
        figsize=(FACET_WIDTH * max(len(methods), 1) * 1.15, FACET_HEIGHT),
        sharey=True, squeeze=False,
    )
    # Wider than fig 3's dodge: the per-point n labels underneath need the room.
    dodge = 0.13
    for ax, method in zip(axes[0], methods):
        for mi, model in enumerate(models):
            line = stats[(stats["method"] == method) & (stats["model"] == model)]
            line = line.set_index("board_style").reindex(styles)
            offset = (mi - (len(models) - 1) / 2) * dodge
            xs = [x + offset for x in range(len(styles))]
            ax.errorbar(
                xs,
                line["game_length_mean"],
                yerr=line["game_length_se"],
                marker="o", capsize=3, linewidth=1.6, markersize=5,
                color=colors[model], label=short_model(model),
            )
            annotate_n(
                ax,
                xs,
                line["game_length_n"].fillna(0).to_numpy(),
                y=top * 0.015,
                fontsize=6.5,
            )
        ax.set_xticks(range(len(styles)))
        ax.set_xticklabels(styles, rotation=45, ha="right", fontsize=8)
        ax.set_title(method, fontsize=10)
        ax.set_ylim(0, top)
        ax.set_xlim(-0.5, len(styles) - 0.5)
        ax.grid(axis="y", alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)

    axes[0][0].set_ylabel("rounds to win")
    fig.suptitle(
        "Ambiguity ladder: rounds per win vs board style (SE bars) — won games only",
        fontsize=12, y=1.09,
    )
    fig.text(0.5, 1.02, "number under each point = won games behind it",
             ha="center", fontsize=8.5, color="#555555")
    fig.legend(
        handles=_legend({short_model(m): colors[m] for m in models}),
        loc="upper center", bbox_to_anchor=(0.5, -0.02),
        ncol=min(len(models), 4), frameon=False, fontsize=9,
    )
    fig.tight_layout()
    return fig


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
    self-play.

    Cells are noisy by construction — a 4x4 grid splits a run sixteen ways, so
    each cell holds a sixteenth of the games and resolves only large gaps. The
    row and column means in the margins are the numbers to read; an individual
    cell running hot or cold is usually not evidence. Every cell prints its own
    n so that is visible rather than implied.
    """
    completed = games[games["completed"]]
    if completed.empty or not _varies(completed, "guesser_model"):
        return None

    metrics = [m for m in _PAIR_METRICS if m[0] in completed.columns]
    if not metrics:
        return None

    codemasters = _level_order(completed, "model")
    guessers = _level_order(completed, "guesser_model")

    fig, axes = plt.subplots(
        1,
        len(metrics),
        figsize=(FACET_WIDTH * 1.5 * len(metrics), FACET_HEIGHT * 1.25),
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
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

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

        ax.set_xticks(range(len(guessers)))
        ax.set_xticklabels([short_model(g) for g in guessers], rotation=30, ha="right",
                           fontsize=8)
        ax.set_yticks(range(len(codemasters)))
        ax.set_yticklabels([short_model(m) for m in codemasters], fontsize=8)
        ax.set_xlabel("guesser")
        ax.set_ylabel("codemaster")
        ax.set_title(f"mean {label} per pair", fontsize=11)

    fig.suptitle(
        "Codemaster x Guesser — does the ranking survive a change of partner?",
        fontsize=12,
    )
    fig.tight_layout()
    return fig


FIGURES = {
    "01_outcome_composition": lambda data: fig_outcome_composition(data.games),
    "02_game_length": lambda data: fig_game_length(data.games),
    "03_ambiguity_ladder": lambda data: fig_ambiguity_ladder(data.games),
    "04_stop_behaviour": lambda data: fig_stop_behaviour(data.rounds),
    "05_intended_overlap": lambda data: fig_intended_overlap(data.rounds),
    "06_ambition_vs_yield": lambda data: fig_ambition_vs_yield(data.rounds),
    "07_dual_miss_lift": lambda data: fig_dual_miss_lift(
        data.rounds, {k: v for board in data.boards.values() for k, v in board.items()}
    ),
    "08_first_guess_lift": lambda data: fig_first_guess_lift(data.games),
    "09_win_length_ladder": lambda data: fig_win_length_ladder(data.games),
    "10_pair_matrix": lambda data: fig_pair_matrix(data.games),
}


def save_all(data, out_dir, dpi: int = 150) -> dict:
    """Render every figure into `out_dir`, returning {name: path}."""
    from pathlib import Path

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = {}
    for name, build in FIGURES.items():
        fig = build(data)
        if fig is None:  # e.g. no ambiguity data on a pre-style run
            continue
        path = out_dir / f"{name}.png"
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        saved[name] = path
    return saved
