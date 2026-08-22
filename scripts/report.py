"""Render a markdown report + figures for one or more runs.

    python scripts/report.py results/20260816T035609664719Z

Writes `report.md` and `figures/*.png` into the run directory (or into
`--out` when several runs are combined). Everything it prints comes from
`codenames_heb.analysis`; this script only formats.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd  # noqa: E402

from codenames_heb import plots  # noqa: E402
from codenames_heb.analysis import (  # noqa: E402
    comparison_power,
    compliance_table,
    dual_miss_lift,
    game_summary,
    load_runs,
    round_summary,
    scaling_projection,
    stop_class_table,
    style_order,
)

# Every table is emitted collapsed *and* stratified by board style: style is
# the designed independent variable, and an effect that reverses direction
# across the ladder disappears when it is collapsed away.
_CANDIDATE_STRATA = (
    ["model"],
    ["guesser_model"],
    ["model", "guesser_model"],
    ["model", "method"],
    ["board_style"],
    ["model", "board_style"],
    ["guesser_model", "board_style"],
    ["model", "guesser_model", "board_style"],
    ["model", "method", "board_style"],
)

# "model" alone stopped being self-explanatory once guessers are models too.
_FACTOR_LABELS = {
    "model": "codemaster",
    "guesser_model": "guesser",
    "method": "prompt method",
    "board_style": "board style",
}


def _strata(games: pd.DataFrame) -> dict:
    """The stratifications this run can actually support.

    A factor with a single level carries no comparison, and nesting it produces
    a table identical to the one without it under a heading that implies a
    contrast the run cannot make — a fixed-guesser run must not advertise a
    "by guesser" table, and a single-method run must not repeat "by codemaster"
    four times. Degenerate factors are dropped and the survivors de-duplicated.
    """
    varying = {
        column
        for column in _FACTOR_LABELS
        if column in games.columns and games[column].nunique(dropna=False) > 1
    }

    strata: dict = {}
    seen: set = set()
    for columns in _CANDIDATE_STRATA:
        kept = [c for c in columns if c in varying]
        if not kept or tuple(kept) in seen:
            continue
        seen.add(tuple(kept))
        strata["by " + " x ".join(_FACTOR_LABELS[c] for c in kept)] = kept
    return strata


def _design_cols(games: pd.DataFrame) -> tuple:
    """The factors this run actually varies.

    Sizing must be told the real design. A factor left out of `cell_cols` has
    its effect absorbed into within-cell variance, which inflates every
    detectable difference and over-buys the next run; a factor with one level
    left *in* splits the data for nothing.
    """
    return tuple(
        column
        for column in ("model", "guesser_model", "method", "board_style")
        if column in games.columns and games[column].nunique(dropna=False) > 1
    )


def _comparisons(games: pd.DataFrame) -> list:
    """Main effects, plus the codemaster x guesser cell when the grid is crossed."""
    comparisons: list = list(_design_cols(games))
    if "model" in comparisons and "guesser_model" in comparisons:
        comparisons.append(("model", "guesser_model"))
    return comparisons


def _varies(frame: pd.DataFrame, column: str) -> bool:
    return column in frame.columns and frame[column].nunique(dropna=False) > 1


def _actor(frame: pd.DataFrame) -> str:
    """Whose behaviour a guesser-side table should be attributed to.

    Stopping early, taking the bonus guess and missing are the guesser's
    decisions, so a crossed run groups them by guesser. A fixed-guesser run has
    only one, and grouping by it would collapse the table to a single row —
    there the codemaster is the only thing that varies, and its clue counts
    still shape what the guesser could do.
    """
    return "guesser_model" if _varies(frame, "guesser_model") else "model"


def _stop_group(rounds: pd.DataFrame) -> list:
    return [_actor(rounds), "board_style"]


def _miss_group(rounds: pd.DataFrame) -> str:
    return _actor(rounds)


def _role_compliance(games: pd.DataFrame, group_col: str, role: str) -> pd.DataFrame:
    """One role's compliance columns, grouped by the model that played it."""
    table = compliance_table(games, [group_col])
    other = "guesser" if role == "codemaster" else "codemaster"
    return table.drop(columns=[c for c in table.columns if c.startswith(other)])


def _cell(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, dict):
        # Already ordered commonest-first by the caller; keep that order.
        return ", ".join(f"{k}: {v}" for k, v in value.items()) or "—"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) or "—"
    return str(value)


def _to_markdown(df: pd.DataFrame) -> str:
    """Small markdown table writer, so the report needs no `tabulate` install."""
    if df.empty:
        return "_(no rows)_"
    header = list(df.columns)
    rows = [[_cell(v) for v in record] for record in df.itertuples(index=False)]
    widths = [
        max(len(str(header[i])), *(len(row[i]) for row in rows)) for i in range(len(header))
    ]
    def line(cells):
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    return "\n".join(
        [line(header), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
        + [line(row) for row in rows]
    )


def _fmt(df: pd.DataFrame, drop: list | None = None) -> str:
    out = df.copy()
    for column in drop or []:
        if column in out.columns:
            out = out.drop(columns=[column])
    if "board_style" in out.columns:
        order = style_order(out["board_style"].dropna().unique())
        out["board_style"] = pd.Categorical(out["board_style"], categories=order, ordered=True)
    # Sorting must not depend on a board_style column being present, or a
    # "by codemaster x guesser" table comes out in groupby order.
    sort_by = [
        c
        for c in ("model", "guesser_model", "method", "board_style")
        if c in out.columns
    ]
    if sort_by:
        out = out.sort_values(sort_by)
    return _to_markdown(out)


def _section(title: str, body: str, note: str = "") -> str:
    parts = [f"## {title}", ""]
    if note:
        parts += [note, ""]
    return "\n".join(parts + [body, ""])


def build_report(data, figure_paths: dict, run_label: str) -> str:
    games, rounds = data.games, data.rounds
    n_failed = int((~games["completed"]).sum())

    lines = [
        f"# Codenames-Hebrew results — {run_label}",
        "",
        f"- Games: **{len(games)}** ({len(games) - n_failed} completed, {n_failed} "
        "not completed)",
        f"- Rounds: **{len(rounds)}**",
        f"- Models: {', '.join(sorted(games['model'].dropna().unique()))}",
        f"- Prompt methods: {', '.join(sorted(games['method'].dropna().unique()))}",
        f"- Guesser: {', '.join(sorted(games['guesser_model'].dropna().astype(str).unique()))}",
        f"- Board styles: {', '.join(style_order(games['board_style'].dropna().unique()))}",
        "",
        "### How to read these numbers",
        "",
        "- Win/loss rates and game length cover **completed games only**. Games that "
        "ended because a model could not produce a legal clue are reported separately "
        "as a completion rate; scoring them as losses would confuse a formatting "
        "failure with a bad clue.",
        "- Games end by finding all 9 targets (win), by hitting the assassin, or by "
        "revealing all 8 opponent words \u2014 the opposing team then has all of its "
        "own and wins. `assassin_share_of_losses` splits the two loss kinds; its "
        "denominator is the losses in that group, not the games.",
        "- `%loss` is close to `1 - %win`, and **game length is confounded with "
        "outcome** \u2014 a short game is an efficient win or an early death. Length is "
        "therefore also reported separately for wins and for losses, and "
        "`targets_per_round` carries the same confound.",
        "- Games from runs played before 2026-08-22 are re-scored against the "
        "opponent-words rule from their own logs, and the rounds that could not have "
        "been played under it are dropped. Those games are flagged `rescored`; the "
        "players were never told the rule, so their play is unaffected by it.",
        "- SE is `sd / sqrt(n)` at the natural unit (games for game metrics, rounds "
        "for round metrics). Proportions also carry a Wilson 95% interval, because "
        "at small n a Wald SE of 0 at p=0 or p=1 reads as false certainty.",
        "- Round-level SEs treat rounds within a game as independent. They are not, "
        "so those SEs are optimistic.",
        "",
        "### Stop taxonomy",
        "",
        "The logged `turn_outcome` cannot answer the early-stop question: it records "
        "both *stopping short of* the codemaster's count and *stopping at* it after "
        "declining the bonus guess as `stopped_early`. Only the first is an early "
        "stop. Rounds are therefore reclassified as:",
        "",
        "| class | meaning |",
        "|---|---|",
        "| `early_stop_true` | stopped before reaching the count — **the early stop** |",
        "| `stopped_at_quota` | reached the count and declined the bonus guess (correct play) |",
        "| `miss_before_quota` | guessed wrong before reaching the count |",
        "| `miss_on_bonus_guess` | reached the count, took the bonus guess, got it wrong |",
        "| `bonus_taken_correct` | reached the count, took the bonus guess, got it right |",
        "| `game_won_midround` | round ended because the 9th target fell — not a choice |",
        "| `guesser_failure` / `no_quota` | guesser exhausted retries / clue had count 0 |",
        "",
        "Rates are computed over eligible rounds only. A guesser may not stop before "
        "its first correct guess, so an early stop is impossible when `count = 1`; "
        "including those rounds in the denominator would deflate the rate for "
        "reasons unrelated to the guesser's judgement.",
        "",
    ]

    strata = _strata(games)

    for label, group in strata.items():
        lines.append(
            _section(
                f"Game outcomes — {label}",
                _fmt(game_summary(games, group)),
                "`loss_rate` and `length_*` cover completed games; `completion_rate` "
                "is the share of games that played out at all. `win_rate` is "
                "`1 - loss_rate` by construction, so only the loss rate carries an "
                "SE and a Wilson interval (`loss_lo` / `loss_hi`).",
            )
        )

    for label, group in strata.items():
        lines.append(
            _section(
                f"Round metrics — {label}",
                _fmt(round_summary(rounds, group)),
                "`ambition` = words the codemaster commits one clue to (`count`); "
                "`yield` = targets that clue actually bought; `yield_ratio` = "
                "yield / ambition. `intended_*` compare the words aimed at with the "
                "words hit; `n_lucky_mean` counts targets found that were *not* "
                "aimed at. `early_stop_rate` and `bonus_take_rate` are over their "
                "eligible rounds only — `n_*_eligible` gives those denominators.",
            )
        )

    lines.append(
        _section(
            "Ambition vs recovery — by clue count",
            # `ambition` *is* the group key here, so its column is a constant.
            _fmt(round_summary(rounds, ["count"]), drop=["ambition_mean", "ambition_se"]),
            "Grouped by the codemaster's own `count`, this is the answer to "
            "\"should the codemaster be asking for more words?\" Read "
            "`intended_recall` (share of the aimed-at words the guesser actually "
            "found) against `yield_mean` (targets that clue bought). If recall "
            "falls faster than yield rises, larger clues buy misses rather than "
            "speed and the small counts are correct play, not timidity. "
            "**Observational**: `count` is chosen by the model, not assigned, so "
            "harder boards and weaker links select into the higher counts. Only a "
            "forced-count run (M4) separates the two.",
        )
    )
    lines.append(
        _section(
            "Stop behaviour — counts and shares",
            _fmt(stop_class_table(rounds, _stop_group(rounds))),
            "Grouped by *guesser*: stopping early, taking the bonus guess and "
            "missing before quota are all decisions the guesser makes, so "
            "grouping them by codemaster attributes them to the wrong player."
            if _varies(rounds, "guesser_model")
            else "Grouped by codemaster: this run held the guesser fixed, so the "
            "codemaster's clue counts are the only thing shaping these rounds.",
        )
    )
    lines.append(
        _section(
            "Codemaster compliance and retries",
            _fmt(_role_compliance(games, "model", "codemaster")),
            "Per-*call* compliance. A model that only produces a legal clue after "
            "several corrective retries is less reliable than one that gets it right "
            "first time, even at an equal win rate.",
        )
    )
    lines.append(
        _section(
            "Guesser compliance and retries",
            _fmt(_role_compliance(games, "guesser_model", "guesser")),
            "Grouped by guesser, which is one row when the guesser is fixed. "
            "Compliance is a property of the model doing the calling, so "
            "grouping the guesser's by *codemaster* would average over whichever "
            "guessers that codemaster happened to be paired with.",
        )
    )

    boards = {k: v for board in data.boards.values() for k, v in board.items()}
    lift = dual_miss_lift(rounds, boards, ["board_style", _miss_group(rounds)])
    if not lift.empty:
        lines.append(
            _section(
                "Does ambiguity actually bite?",
                _fmt(lift),
                "`observed` = share of first misses landing on a dual-list word; "
                "`expected` = that board's own dual fraction. `lift` near 1 means "
                "ambiguous words are missed at exactly their base rate, i.e. lexical "
                "ambiguity is not the mechanism driving errors.",
            )
        )

    lines.append(
        _section(
            "How large should the next run be? — per design cell",
            _fmt(scaling_projection(games, cell_cols=_design_cols(games))),
            "Projected from this run's own within-cell variance. "
            "`games_per_cell` = `n_boards x n_trials` for each "
            "(model, method, board_style) cell. `*_ci_halfwidth` is the 95% "
            "interval half-width; `mdd_*` is the smallest cell-to-cell difference "
            "detectable at alpha=0.05 with 80% power; `api_calls_total` prices the "
            "whole run. This is the **most pessimistic** view — a cell holds model, "
            "method and board style all fixed, so it is answering 'can I compare two "
            "single cells?', which is rarely the question.",
        )
    )
    lines.append(
        _section(
            "How large should the next run be? — per comparison",
            _fmt(comparison_power(games, design_cols=_design_cols(games), comparisons=_comparisons(games))),
            "The same projection for the comparisons actually of interest, each of "
            "which collapses over the other two factors and so pools far more games "
            "per arm. Size the run from this table: pick the comparison that has to "
            "come out conclusive, find the smallest `games_per_cell` whose `mdd_*` "
            "is below the effect you care about, then read the cost off the per-cell "
            "table above.\n\n"
            "**Which outcome variable you size against changes the answer by a large "
            "factor.** `mdd_win_rate` and `mdd_first_guess_lift` are both reported "
            "because first-guess lift separates the models far more sharply than "
            "win rate does, so a run sized to resolve win rate is several times "
            "larger than one sized to resolve lift. Compare each `mdd_*` against the "
            "observed spread in that same metric from the tables above, not across "
            "metrics.",
        )
    )

    if figure_paths:
        lines.append("## Figures\n")
        for name, path in sorted(figure_paths.items()):
            lines.append(f"### {name.split('_', 1)[1].replace('_', ' ')}\n")
            lines.append(f"![{name}](figures/{path.name})\n")

    return "\n".join(lines)


def main(argv=None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path, help="results/<run_id> directories")
    parser.add_argument("--out", type=Path, default=None,
                        help="output directory (defaults to the single run's directory)")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_runs(args.run_dirs)
    except (ValueError, FileNotFoundError) as exc:
        # Pointing the report at a pre-2026-08-15 run is an ordinary mistake,
        # not a bug — say what is wrong without a traceback.
        parser.exit(2, f"error: {exc}\n")

    out_dir = args.out or (args.run_dirs[0] if len(args.run_dirs) == 1 else PROJECT_ROOT / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    figure_paths = {} if args.no_figures else plots.save_all(data, out_dir / "figures")

    run_label = ", ".join(data.run_ids)
    report_path = out_dir / "report.md"
    report_path.write_text(build_report(data, figure_paths, run_label), encoding="utf-8")

    print(f"Report written to {report_path}")
    if figure_paths:
        print(f"{len(figure_paths)} figures written to {out_dir / 'figures'}")
    return report_path


if __name__ == "__main__":
    main()
