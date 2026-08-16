"""Turn `results/<run_id>/raw.jsonl` into tidy tables and summary statistics.

`metrics.csv` only carries game-level fields, so every round-level question
(clue ambition, stop behaviour, intended-vs-hit overlap) has to come from the
raw JSONL. This module owns those derivations so notebooks and the report
script share one implementation.

Two tables come out of a run:

- `games`  — one row per game, the unit for outcome and length statistics
- `rounds` — one row per clue, the unit for stop behaviour and overlap

The derivation that matters most is `classify_stop`: the logged
`turn_outcome == "stopped_early"` conflates stopping *short of* the
codemaster's count with stopping *at* it after declining the bonus guess. Only
the first is an early stop; on the 2026-08-16 run the logged field would
overstate the early-stop rate by ~3.6x.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
import yaml

from codenames_heb.board import BOARD_SIZE, BOARD_STYLES, ROLE_COUNTS

# Normal quantiles, hardcoded so the analysis layer needs no scipy: two-sided
# 95% confidence, and 80% power.
Z_95 = 1.959963984540054
Z_POWER_80 = 0.8416212335729143

TARGETS_PER_BOARD = ROLE_COUNTS["target"]

# Only these end with a played-out board. `codemaster_failure`, `stalled`,
# `max_rounds_reached` and harness errors are reported as a separate
# completion rate rather than scored as game-playing skill.
COMPLETED_OUTCOMES = frozenset({"win", "loss"})

# Board style is the designed independent variable; this is its plotting and
# table order. Runs predating board styles get "unspecified".
UNSPECIFIED_STYLE = "unspecified"
BOARD_STYLE_ORDER = (*BOARD_STYLES, UNSPECIFIED_STYLE)

STOP_CLASSES = (
    "miss_before_quota",
    "miss_on_bonus_guess",
    "stopped_at_quota",
    "early_stop_true",
    "bonus_taken_correct",
    "game_won_midround",
    "guesser_failure",
    "no_quota",
)

_MISS_OUTCOMES = frozenset({"hit_opponent", "hit_civilian", "hit_assassin"})

GAME_KEY = ["run_id", "model", "method", "guesser_model", "board_style", "board_seed", "trial"]

_COMPLIANCE_COLUMNS = [
    "codemaster_attempts",
    "codemaster_rejected",
    "codemaster_compliance_rate",
    "codemaster_call_failures",
    "guesser_attempts",
    "guesser_rejected",
    "guesser_compliance_rate",
    "guesser_call_failures",
]


# --- derivations ---------------------------------------------------------


def classify_stop(
    turn_outcome: str, n_correct: int, count: int, game_won_this_round: bool
) -> str:
    """Name what actually ended a round.

    `turn_outcome` alone cannot answer this. Both of these log as
    `stopped_early`:

        count=2, n_correct=1  -> the guesser gave up a guess it was owed
        count=1, n_correct=1  -> the guesser took its one guess and correctly
                                 declined the bonus

    and both of these log as `all_correct`:

        n_correct == count+1  -> the guesser took the bonus guess and was right
        the 9th target fell   -> the round ended because the game did

    Only `early_stop_true` is an early stop in the sense the experiment cares
    about: stopping before reaching the number the codemaster named.
    """
    if game_won_this_round:
        return "game_won_midround"
    if turn_outcome == "guesser_failure":
        return "guesser_failure"
    # count=0 means the guesser had an unbounded budget, so "before"/"after the
    # quota" is undefined. Kept out of every stop-rate denominator.
    if count <= 0:
        return "no_quota"
    if turn_outcome == "all_correct":
        return "bonus_taken_correct"
    if turn_outcome == "stopped_early":
        return "early_stop_true" if n_correct < count else "stopped_at_quota"
    return "miss_on_bonus_guess" if n_correct >= count else "miss_before_quota"


def intended_overlap(intended: Sequence[str], hit: Sequence[str]) -> dict:
    """Compare the words the codemaster aimed at with the ones actually found.

    `n_lucky` counts target words the guesser found that the codemaster was
    *not* aiming at. They win the game just the same, so leaving them
    unmeasured credits the codemaster for the guesser's luck.
    """
    intended_set = set(intended)
    hit_set = set(hit)
    recovered = intended_set & hit_set

    return {
        "n_intended": len(intended_set),
        "n_intended_recovered": len(recovered),
        "n_lucky": len(hit_set - intended_set),
        "intended_recall": len(recovered) / len(intended_set) if intended_set else None,
        "intended_precision": len(recovered) / len(hit_set) if hit_set else None,
        "intended_jaccard": (
            len(recovered) / len(intended_set | hit_set) if intended_set else None
        ),
    }


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple:
    """Wilson score interval for a proportion.

    Reported alongside the Wald SE because at 5 games per cell a run of 5 wins
    gives a Wald SE of exactly 0, which reads as certainty. Wilson stays inside
    [0, 1] and keeps width at the boundaries.
    """
    if n <= 0:
        return (None, None)
    denominator = n + z**2
    center = (successes + z**2 / 2) / denominator
    halfwidth = (z / denominator) * math.sqrt(
        successes * (n - successes) / n + z**2 / 4
    )
    return (max(0.0, center - halfwidth), min(1.0, center + halfwidth))


# --- aggregation ---------------------------------------------------------


def summarize(
    df: pd.DataFrame,
    group_cols: Sequence[str],
    metrics: Sequence[str],
    proportions: Sequence[str] = (),
) -> pd.DataFrame:
    """Mean, SE and n per group, one column block per metric.

    SE is the simple `sd / sqrt(n)` at the natural unit of the frame passed in
    — games for `games`, rounds for `rounds`. Nulls are skipped and n is
    counted per metric, because round metrics are deliberately NaN when the
    round was not eligible (e.g. early-stop rate on a count=1 round, where
    stopping early is impossible).

    Caveat worth repeating wherever these numbers are printed: on the rounds
    table this treats rounds within a game as independent. They are not, so
    round-level SEs are optimistic.
    """
    group_cols = list(group_cols)
    frame = df.copy()
    if not group_cols:
        frame["_all"] = "all"
        keys = ["_all"]
    else:
        keys = group_cols

    grouped = frame.groupby(keys, dropna=False, observed=True)
    out = pd.DataFrame(index=grouped.size().index)
    out["n"] = grouped.size()

    for metric in metrics:
        if metric not in frame.columns:
            continue
        series = grouped[metric]
        n = series.count()
        out[f"{metric}_mean"] = series.mean()
        out[f"{metric}_se"] = series.std(ddof=1) / n.pow(0.5)
        out[f"{metric}_n"] = n

    for metric in proportions:
        if metric not in frame.columns:
            continue
        bounds = grouped[metric].apply(
            lambda s: wilson_interval(int(round(s.sum())), int(s.count()))
        )
        out[f"{metric}_lo"] = [b[0] for b in bounds]
        out[f"{metric}_hi"] = [b[1] for b in bounds]

    out = out.reset_index()
    return out.drop(columns=["_all"]) if not group_cols else out


# Outcome variables a run can be sized against, mapped to their column label.
# Which one you pick changes the answer by a large factor: first-guess lift
# separates the models by roughly 8 SE on the 2026-08-16 run where win rate
# separates them by about one, so a run sized to resolve win rate is far larger
# than one sized to resolve lift. Both are reported so the choice is explicit.
POWER_METRICS = {
    "is_win": "win_rate",
    "first_guess_lift": "first_guess_lift",
    "game_length": "game_length",
}


def scaling_projection(
    games: pd.DataFrame,
    candidate_ns: Sequence[int] = (5, 10, 20, 40),
    cell_cols: Sequence[str] = ("model", "method", "board_style"),
) -> pd.DataFrame:
    """What each candidate run size buys, in precision and in API calls.

    Uses the pilot's own within-cell variance, so the projection is anchored to
    observed behaviour rather than an assumed effect size. `mdd_*` is the
    smallest difference between two cells that a run of this size would detect
    at alpha=0.05 with 80% power.
    """
    completed = games[games["completed"]]
    cell_cols = [c for c in cell_cols if c in completed.columns]
    cells = completed.groupby(cell_cols, dropna=False, observed=True)
    n_cells = cells.ngroups

    variances = {
        label: _pooled_variance(cells[metric])
        for metric, label in POWER_METRICS.items()
        if metric in completed.columns
    }
    calls_per_game = completed["total_api_calls"].mean()

    detect = Z_95 + Z_POWER_80
    rows = []
    for n in candidate_ns:
        row = {"games_per_cell": n, "n_cells": n_cells, "games_total": n * n_cells}
        for label, var in variances.items():
            row[f"{label}_ci_halfwidth"] = Z_95 * math.sqrt(var / n)
            row[f"mdd_{label}"] = detect * math.sqrt(2 * var / n)
        row["api_calls_total"] = n * n_cells * calls_per_game
        rows.append(row)
    return pd.DataFrame(rows)


def comparison_power(
    games: pd.DataFrame,
    candidate_ns: Sequence[int] = (5, 10, 20, 40),
    design_cols: Sequence[str] = ("model", "method", "board_style"),
    comparisons: Sequence[str] = ("model", "method", "board_style"),
) -> pd.DataFrame:
    """Detectable difference for the comparisons that are actually of interest.

    `scaling_projection` sizes a single design cell, which is the most
    pessimistic possible view: a cell holds model, method and board style all
    fixed. The comparisons the project cares about each collapse over the other
    two factors, which multiplies the games behind each arm and shrinks the
    detectable difference accordingly. This is the table to size a run from.
    """
    completed = games[games["completed"]]
    design_cols = [c for c in design_cols if c in completed.columns]
    n_cells = completed.groupby(design_cols, dropna=False, observed=True).ngroups

    cells = completed.groupby(design_cols, dropna=False, observed=True)
    variances = {
        label: _pooled_variance(cells[metric])
        for metric, label in POWER_METRICS.items()
        if metric in completed.columns
    }
    detect = Z_95 + Z_POWER_80

    rows = []
    for column in comparisons:
        if column not in completed.columns:
            continue
        n_levels = completed[column].nunique(dropna=False)
        if n_levels < 2:
            continue
        cells_per_arm = n_cells / n_levels
        for n in candidate_ns:
            per_arm = n * cells_per_arm
            rows.append(
                {
                    "comparison": f"{column} (collapsing the other factors)",
                    "levels": n_levels,
                    "games_per_cell": n,
                    "games_per_arm": per_arm,
                    **{
                        f"mdd_{label}": detect * math.sqrt(2 * var / per_arm)
                        for label, var in variances.items()
                    },
                }
            )
    return pd.DataFrame(rows)


def _pooled_variance(grouped) -> float:
    """Within-cell variance pooled across cells, so between-cell effects don't
    inflate the noise estimate the projection is built on."""
    counts = grouped.count()
    variances = grouped.var(ddof=1)
    weights = (counts - 1).clip(lower=0)
    usable = weights > 0
    if not usable.any():
        return float("nan")
    return float((variances[usable] * weights[usable]).sum() / weights[usable].sum())


# --- loading -------------------------------------------------------------


@dataclass(frozen=True)
class RunData:
    games: pd.DataFrame
    rounds: pd.DataFrame
    boards: dict
    configs: dict
    run_ids: tuple
    # {run_id: run_meta.json}. Holds `max_workers`, without which `duration_s`
    # cannot be read: a game is slow because the provider throttled it or
    # because 4 other games were competing for bandwidth, and only the worker
    # count distinguishes those. Empty for runs written before the parallel
    # runner existed.
    meta: dict = field(default_factory=dict)


def load_run(run_dir) -> RunData:
    run_dir = Path(run_dir)
    run_id = run_dir.name
    rows = _read_jsonl(run_dir / "raw.jsonl")

    if not rows:
        raise ValueError(f"Run {run_id}: raw.jsonl is empty")
    missing_rounds = sum(1 for row in rows if "rounds" not in row)
    if missing_rounds:
        raise ValueError(
            f"Run {run_id} uses the pre-multi-round schema "
            f"({missing_rounds}/{len(rows)} rows have no 'rounds' key). Runs before "
            "2026-08-15 logged one flat one-shot trial per row and are not "
            "comparable with multi-round games."
        )

    boards = _load_boards(run_dir / "boards.json")
    config = _load_config(run_dir / "config.yaml")
    meta = _load_meta(run_dir / "run_meta.json")

    game_records = []
    round_records = []
    for row in rows:
        game, rounds = _build_game(row, run_id, boards, config)
        game_records.append(game)
        round_records.extend(rounds)

    # Under `max_workers > 1` raw.jsonl is written in completion order, which
    # is non-deterministic. Sorting here keeps every table and report stable
    # across reruns of the same experiment.
    games = _sort_by_game(pd.DataFrame(game_records))
    rounds = _sort_by_game(pd.DataFrame(round_records), extra=["round"])
    return RunData(
        games=games,
        rounds=rounds,
        boards={run_id: boards},
        configs={run_id: config},
        run_ids=(run_id,),
        meta={run_id: meta},
    )


def load_runs(run_dirs: Iterable) -> RunData:
    """Concatenate several runs. Each keeps its `run_id`, so a run can always
    be sliced back out — runs differ in guesser model and board styles and are
    not automatically poolable."""
    loaded = [load_run(d) for d in run_dirs]
    if not loaded:
        raise ValueError("load_runs called with no run directories")

    boards: dict = {}
    configs: dict = {}
    for data in loaded:
        boards.update(data.boards)
        configs.update(data.configs)

    meta: dict = {}
    for data in loaded:
        meta.update(data.meta)

    return RunData(
        games=pd.concat([d.games for d in loaded], ignore_index=True),
        rounds=pd.concat([d.rounds for d in loaded], ignore_index=True),
        boards=boards,
        configs=configs,
        run_ids=tuple(rid for d in loaded for rid in d.run_ids),
        meta=meta,
    )


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        raise FileNotFoundError(f"No raw.jsonl at {path}")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_boards(path: Path) -> dict:
    """Key boards by (style, seed). Pre-style runs wrote neither `style` nor
    `is_dual`, so those boards key on the unspecified style and contribute no
    ambiguity data."""
    if not path.exists():
        return {}
    boards = json.loads(path.read_text(encoding="utf-8"))
    return {
        (board.get("style") or UNSPECIFIED_STYLE, board["seed"]): board
        for board in boards
    }


def _sort_by_game(frame: pd.DataFrame, extra: list | None = None) -> pd.DataFrame:
    if frame.empty:
        return frame
    keys = [c for c in GAME_KEY + (extra or []) if c in frame.columns]
    return frame.sort_values(keys, kind="stable").reset_index(drop=True)


def _load_meta(path: Path) -> dict:
    """`run_meta.json`, written only by the parallel runner."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _build_game(row: dict, run_id: str, boards: dict, config: dict):
    style = row.get("board_style") or UNSPECIFIED_STYLE
    seed = row.get("board_seed")
    board = boards.get((style, seed), {})
    is_dual = board.get("is_dual") or {}

    key = {
        "run_id": run_id,
        "model": row.get("model"),
        "method": row.get("method"),
        # Older runs did not record the guesser per row; the run config knows it.
        "guesser_model": row.get("guesser_model") or config.get("guesser_model"),
        "board_style": style,
        "board_seed": seed,
        "trial": row.get("trial"),
    }

    rounds = _build_rounds(row.get("rounds") or [], key, is_dual)
    outcome = row.get("outcome")
    completed = outcome in COMPLETED_OUTCOMES

    game = {
        **key,
        "status": row.get("status"),
        "outcome": outcome,
        "completed": completed,
        # NaN rather than 0 on a failed game: an unplayed game is missing data,
        # not a loss, and summarize() skips nulls.
        "is_win": float(outcome == "win") if completed else None,
        "is_loss": float(outcome == "loss") if completed else None,
        "game_length": row.get("game_length"),
        "n_rounds": len(rounds),
        "targets_found": row.get("targets_found"),
        "target_recovery_rate": row.get("target_recovery_rate"),
        "assassin_hit": row.get("assassin_hit"),
        "terminal_error": row.get("terminal_error") or row.get("error"),
        # Written only by the parallel runner; absent on earlier runs.
        "started_at": row.get("started_at"),
        "duration_s": row.get("duration_s"),
        **{col: row.get(col) for col in _COMPLIANCE_COLUMNS},
        "total_api_calls": (row.get("codemaster_attempts") or 0)
        + (row.get("guesser_attempts") or 0),
        "rejection_reasons": row.get("rejection_reasons") or {},
    }
    game.update(_game_level_round_means(rounds))
    return game, rounds


def _build_rounds(raw_rounds: list, key: dict, is_dual: dict) -> list:
    """Derive the round table for one game.

    `game_won_this_round` is reconstructed by replaying cumulative target
    reveals: the round in which the 9th target falls ended because the game
    ended, and the guesser's behaviour in it is not a stop decision.
    """
    records = []
    targets_found = 0
    words_revealed = 0
    for raw in raw_rounds:
        sequence = raw.get("guess_sequence") or []
        hit = [g["word"] for g in sequence if g["role"] == "target"]
        misses = [g for g in sequence if g["role"] != "target"]
        count = raw.get("count") or 0

        first_guess = _first_guess_lift(sequence, targets_found, words_revealed)

        targets_found += len(hit)
        words_revealed += len(sequence)
        game_won = targets_found >= TARGETS_PER_BOARD

        overlap = intended_overlap(raw.get("intended_targets") or [], hit)
        stop_class = classify_stop(raw.get("turn_outcome"), len(hit), count, game_won)

        first_miss = misses[0] if misses else None
        records.append(
            {
                **key,
                "round": raw.get("round"),
                "clue": raw.get("clue"),
                "en_clue": raw.get("en_clue"),
                "intended_targets": raw.get("intended_targets") or [],
                # Ambition: how many words the codemaster commits one clue to.
                "count": count,
                # Yield: how many targets that clue actually bought.
                "n_correct": len(hit),
                "n_guesses": len(sequence),
                "yield_ratio": len(hit) / count if count > 0 else None,
                "turn_outcome": raw.get("turn_outcome"),
                "stop_class": stop_class,
                "game_won_this_round": game_won,
                **overlap,
                **first_guess,
                "first_miss_role": first_miss["role"] if first_miss else None,
                "first_miss_is_dual": _dual_flag(first_miss, is_dual),
                **_stop_indicators(stop_class, count, len(hit)),
            }
        )
    return records


def _first_guess_lift(sequence: list, targets_found: int, words_revealed: int) -> dict:
    """Did the round's first guess beat blind chance, and by how much?

    This is the sharpest signal of codemaster skill in the data: the first
    guess of a round is the one the clue is most responsible for, before the
    guesser has any feedback to work from. On the 2026-08-16 run it separates
    the models by roughly 8 SE end to end, where win rate separates them by
    about one.

    The baseline must come from the pool as it stands *at the start of this
    round*, not from the board's opening 9/25 = 0.360. Targets are found faster
    than non-targets, so the pool sours as a game goes on — the measured mean
    baseline across this run's rounds is 0.284. Scoring late rounds against
    0.360 would understate every model, and understate the models that survive
    longest the most.
    """
    remaining = BOARD_SIZE - words_revealed
    baseline = (TARGETS_PER_BOARD - targets_found) / remaining if remaining > 0 else None
    # A round the guesser failed out of has no first guess to score.
    hit = float(sequence[0]["role"] == "target") if sequence else None
    return {
        "first_guess_hit": hit,
        "first_guess_baseline": baseline,
        "first_guess_lift": (
            hit - baseline if hit is not None and baseline is not None else None
        ),
    }


def _dual_flag(first_miss, is_dual: dict):
    if first_miss is None or not is_dual:
        return None
    return float(bool(is_dual.get(first_miss["word"])))


def _stop_indicators(stop_class: str, count: int, n_correct: int) -> dict:
    """Eligibility-aware indicators, NaN where the guesser had no such choice.

    A guesser may not stop before its first correct guess (`LLMGuesser` rejects
    it), so an early stop is only possible once it has at least one correct
    guess and the count is at least 2. Including count=1 rounds in the
    denominator — 385 of 1,358 rounds on the 2026-08-16 run — would deflate the
    early-stop rate toward zero for reasons that have nothing to do with the
    guesser's judgement.
    """
    early_eligible = (
        count >= 2
        and n_correct >= 1
        and stop_class in {"early_stop_true", "stopped_at_quota",
                           "miss_before_quota", "miss_on_bonus_guess",
                           "bonus_taken_correct"}
    )
    bonus_eligible = stop_class in {
        "stopped_at_quota",
        "bonus_taken_correct",
        "miss_on_bonus_guess",
    }
    return {
        "early_stop_eligible": early_eligible,
        "is_early_stop": float(stop_class == "early_stop_true") if early_eligible else None,
        "bonus_eligible": bonus_eligible,
        "is_bonus_taken": (
            float(stop_class in {"bonus_taken_correct", "miss_on_bonus_guess"})
            if bonus_eligible
            else None
        ),
    }


def _game_level_round_means(rounds: list) -> dict:
    """Collapse a game's rounds so game-level tables can carry round metrics
    without re-deriving them."""
    if not rounds:
        return {
            "mean_clue_count": None, "mean_recovered": None, "mean_jaccard": None,
            "early_stop_rate": None, "bonus_take_rate": None, "n_lucky_total": 0,
            "first_guess_lift": None,
        }
    frame = pd.DataFrame(rounds)
    return {
        "mean_clue_count": frame["count"].replace(0, pd.NA).mean(),
        "mean_recovered": frame["n_correct"].mean(),
        "mean_jaccard": frame["intended_jaccard"].mean(),
        "early_stop_rate": frame["is_early_stop"].mean(),
        "bonus_take_rate": frame["is_bonus_taken"].mean(),
        "n_lucky_total": int(frame["n_lucky"].sum()),
        # Averaged within the game first, so a 13-round game does not outweigh
        # a 5-round one 2.6x when games are later averaged together. Rounds
        # share a board and a revealed set, so they are not independent draws.
        "first_guess_lift": frame["first_guess_lift"].mean(),
    }


# --- report views --------------------------------------------------------

GAME_METRICS = [
    "game_length", "is_win", "is_loss", "targets_found", "target_recovery_rate",
    # Per-game mean of the round-level lift; see `_first_guess_lift`.
    "first_guess_lift",
]
ROUND_METRICS = [
    "count",
    "n_correct",
    "first_guess_hit",
    "first_guess_baseline",
    "first_guess_lift",
    "yield_ratio",
    "intended_recall",
    "intended_precision",
    "intended_jaccard",
    "n_lucky",
    "is_early_stop",
    "is_bonus_taken",
]


def game_summary(games: pd.DataFrame, group_cols: Sequence[str]) -> pd.DataFrame:
    """Outcome and length over completed games, plus the completion rate.

    Length is reported three ways because it is confounded with outcome: games
    end only by winning (all 9 targets) or by hitting the assassin, so a short
    game is either an efficient win or an early death.

    Columns are curated rather than dumped — win rate is `1 - loss_rate` over
    completed games, so only one of them carries an SE and interval.
    """
    group_cols = list(group_cols)
    completed = games[games["completed"]]

    out = summarize(completed, group_cols, GAME_METRICS, proportions=["is_loss"])
    out = out.rename(
        columns={
            "n": "n_completed",
            "is_win_mean": "win_rate",
            "is_loss_mean": "loss_rate",
            "is_loss_se": "loss_se",
            "is_loss_lo": "loss_lo",
            "is_loss_hi": "loss_hi",
            "game_length_mean": "length_mean",
            "game_length_se": "length_se",
            "targets_found_mean": "targets_found_mean",
            "targets_found_se": "targets_found_se",
        }
    )

    for label, subset in (
        ("win", completed[completed["is_win"] == 1.0]),
        ("loss", completed[completed["is_loss"] == 1.0]),
    ):
        part = summarize(subset, group_cols, ["game_length"])
        part = part.rename(
            columns={
                "game_length_mean": f"length_{label}_mean",
                "game_length_se": f"length_{label}_se",
                "n": f"n_{label}",
            }
        )[group_cols + [f"length_{label}_mean", f"length_{label}_se", f"n_{label}"]]
        out = out.merge(part, on=group_cols, how="left") if group_cols else _hstack(out, part)

    completion = summarize(
        games.assign(is_completed=games["completed"].astype(float)),
        group_cols,
        ["is_completed"],
    ).rename(columns={"n": "n_games", "is_completed_mean": "completion_rate"})[
        group_cols + ["n_games", "completion_rate"]
    ]
    out = out.merge(completion, on=group_cols, how="left") if group_cols else _hstack(out, completion)

    keep = group_cols + [
        "n_games", "n_completed", "completion_rate",
        "win_rate", "loss_rate", "loss_se", "loss_lo", "loss_hi",
        "length_mean", "length_se",
        "length_win_mean", "length_win_se", "n_win",
        "length_loss_mean", "length_loss_se", "n_loss",
        "targets_found_mean", "targets_found_se",
        "first_guess_lift_mean", "first_guess_lift_se",
    ]
    return out[[c for c in keep if c in out.columns]]


# Round metrics that get a per-metric n printed, because their denominator is
# an eligible subset rather than every round in the group.
_ELIGIBILITY_METRICS = ("is_early_stop", "is_bonus_taken")


def round_summary(rounds: pd.DataFrame, group_cols: Sequence[str]) -> pd.DataFrame:
    """Clue ambition, yield, intended-overlap and stop rates per group."""
    group_cols = list(group_cols)
    out = summarize(
        rounds,
        group_cols,
        ROUND_METRICS,
        proportions=["is_early_stop", "is_bonus_taken"],
    )
    out = out.rename(
        columns={
            "n": "n_rounds",
            "count_mean": "ambition_mean", "count_se": "ambition_se",
            "n_correct_mean": "yield_mean", "n_correct_se": "yield_se",
            "is_early_stop_mean": "early_stop_rate",
            "is_early_stop_se": "early_stop_se",
            "is_early_stop_n": "n_early_stop_eligible",
            "is_bonus_taken_mean": "bonus_take_rate",
            "is_bonus_taken_se": "bonus_take_se",
            "is_bonus_taken_n": "n_bonus_eligible",
        }
    )
    keep = group_cols + [
        "n_rounds",
        "first_guess_hit_mean", "first_guess_baseline_mean",
        "first_guess_lift_mean", "first_guess_lift_se",
        "ambition_mean", "ambition_se", "yield_mean", "yield_se",
        "yield_ratio_mean", "yield_ratio_se",
        "intended_recall_mean", "intended_recall_se",
        "intended_precision_mean", "intended_precision_se",
        "intended_jaccard_mean", "intended_jaccard_se",
        "n_lucky_mean",
        "early_stop_rate", "early_stop_se", "n_early_stop_eligible",
        "bonus_take_rate", "bonus_take_se", "n_bonus_eligible",
    ]
    return out[[c for c in keep if c in out.columns]]


def stop_class_table(
    rounds: pd.DataFrame, group_cols: Sequence[str], shares_only: bool = False
) -> pd.DataFrame:
    """Within-group composition of `stop_class`.

    Classes that never occur in the data are dropped rather than printed as
    columns of zeros.
    """
    group_cols = list(group_cols)
    if not group_cols:
        frame = rounds.assign(_all="all")
        keys = ["_all"]
    else:
        frame, keys = rounds, group_cols

    counts = (
        frame.groupby(keys + ["stop_class"], dropna=False, observed=True)
        .size()
        .unstack("stop_class", fill_value=0)
        .reset_index()
    )
    present = [c for c in STOP_CLASSES if c in counts.columns and counts[c].sum() > 0]

    totals = counts[present].sum(axis=1)
    shares = counts[present].div(totals.replace(0, pd.NA), axis=0).add_suffix("_share")
    blocks = [counts[keys], pd.DataFrame({"n_rounds": totals})]
    if not shares_only:
        blocks.append(counts[present])
    blocks.append(shares)

    out = pd.concat(blocks, axis=1)
    return out.drop(columns=["_all"]) if not group_cols else out


def compliance_table(games: pd.DataFrame, group_cols: Sequence[str]) -> pd.DataFrame:
    """Per-call compliance and the rejection-reason breakdown.

    A model that only produces a legal clue after five corrective retries is
    not as reliable as one that gets it right first time, even if both end up
    with the same win rate.
    """
    group_cols = list(group_cols)
    out = summarize(
        games,
        group_cols,
        ["codemaster_compliance_rate", "guesser_compliance_rate",
         "codemaster_call_failures", "total_api_calls", "duration_s"],
    ).rename(columns={"n": "n_games"})

    keep = group_cols + [
        "n_games",
        "codemaster_compliance_rate_mean", "codemaster_compliance_rate_se",
        "guesser_compliance_rate_mean", "guesser_compliance_rate_se",
        "codemaster_call_failures_mean", "total_api_calls_mean",
        "duration_s_mean", "duration_s_se",
    ]
    out = out[[c for c in keep if c in out.columns]]

    if not group_cols:
        return out.assign(rejection_reasons=[_merge_reasons(games["rejection_reasons"])])

    # Built row by row rather than with groupby.apply: returning a dict from
    # apply makes pandas expand it into one row per key.
    records = []
    for keys, subset in games.groupby(group_cols, dropna=False, observed=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        records.append(
            {**dict(zip(group_cols, keys)),
             "rejection_reasons": _merge_reasons(subset["rejection_reasons"])}
        )
    return out.merge(pd.DataFrame(records), on=group_cols, how="left")


def _merge_reasons(column) -> dict:
    """Sum the per-game rejection-reason counters, commonest reason first."""
    merged = sum((Counter(d) for d in column if d), Counter())
    return dict(merged.most_common())


def dual_miss_lift(rounds: pd.DataFrame, boards: dict, group_cols: Sequence[str]) -> pd.DataFrame:
    """Do misses land on ambiguous words more often than chance?

    `observed` is the share of first misses that hit a dual-list word;
    `expected` is that board's own dual fraction. A lift above 1 means
    ambiguity is actually pulling the guesser off target — which, on the
    2026-08-16 run, it is not.
    """
    group_cols = list(group_cols)
    expected = _expected_dual_share(boards)

    scored = rounds[rounds["first_miss_is_dual"].notna()].copy()
    if scored.empty:
        return pd.DataFrame(columns=group_cols + ["observed", "expected", "lift", "n_misses"])

    scored["expected_dual"] = scored["board_style"].map(expected)
    out = summarize(scored, group_cols, ["first_miss_is_dual", "expected_dual"],
                    proportions=["first_miss_is_dual"])
    out = out.rename(
        columns={
            "first_miss_is_dual_mean": "observed",
            "first_miss_is_dual_lo": "observed_lo",
            "first_miss_is_dual_hi": "observed_hi",
            "expected_dual_mean": "expected",
            "n": "n_misses",
        }
    )
    # dual_0 boards contain no ambiguous words, so the lift is undefined rather
    # than zero — there is nothing there to be drawn to.
    out["lift"] = out["observed"] / out["expected"].replace(0, float("nan"))
    keep = group_cols + ["n_misses", "observed", "observed_lo", "observed_hi",
                         "expected", "lift"]
    return out[[c for c in keep if c in out.columns]]


def _expected_dual_share(boards: dict) -> dict:
    """Dual-word fraction per style, measured from the boards actually used
    rather than from the nominal style percentage."""
    totals: dict = {}
    for (style, _seed), board in boards.items():
        is_dual = board.get("is_dual")
        if not is_dual:
            continue
        dual, total = totals.get(style, (0, 0))
        totals[style] = (dual + sum(bool(v) for v in is_dual.values()), total + len(is_dual))
    return {style: dual / total for style, (dual, total) in totals.items() if total}


def _hstack(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    """Join two single-row summaries that share no grouping key."""
    duplicated = [c for c in right.columns if c in left.columns]
    return pd.concat([left, right.drop(columns=duplicated)], axis=1)


def style_order(values: Iterable) -> list:
    """Board styles in ladder order, for stable table rows and plot facets."""
    present = set(values)
    return [s for s in BOARD_STYLE_ORDER if s in present]
