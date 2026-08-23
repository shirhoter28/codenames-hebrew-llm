import csv
import json
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import zip_longest
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from codenames_heb.board import (
    BOARD_STYLES,
    RETIRED_BOARD_STYLES,
    Board,
    generate_board,
)
from codenames_heb.compliance import classify_error
from codenames_heb.llm_client import FormatFailure
from codenames_heb.metrics import compute_round_metrics
from codenames_heb.prompts.codemaster import (
    PROMPT_METHODS,
    build_correction_note as build_codemaster_correction,
    parse_codemaster_response,
    validate_clue_legality,
)
from codenames_heb.prompts.guesser import (
    build_correction_note as build_guesser_correction,
    build_single_guess_prompt,
    parse_single_guess_response,
)
from codenames_heb.roles import Codemaster, Guesser
from codenames_heb.words import WordLists

_OUTCOME_BY_ROLE = {
    "opponent": "hit_opponent",
    "civilian": "hit_civilian",
    "assassin": "hit_assassin",
}

# How many consecutive rounds that reveal nothing (i.e. the guesser failed to
# produce any usable guess) before the game is abandoned as stalled.
_MAX_CONSECUTIVE_STALLS = 2

# `guesser_model: same_as_codemaster` runs self-play — each Codemaster model
# guesses its own clues. Removes the home-field advantage a fixed guesser gives
# to the model it shares a family with, at the cost of no longer isolating
# Codemaster skill from Guesser skill (a weak pair could fail at either end).
SAME_AS_CODEMASTER = "same_as_codemaster"


def count_constraint_label(count_floor: int | None) -> str:
    """Name the arm a game belongs to: "free", "min2", "min3", ...

    A string rather than a nullable int because the column is sorted and grouped
    downstream, and a column mixing None with int raises inside pandas'
    sort_values — the same reason older runs need a stable value to backfill.
    """
    return "free" if count_floor is None else f"min{count_floor}"


def _compliance_summary(stats: Counter) -> dict:
    """Per-call compliance, plus the reason breakdown, for one game.

    Rates are per *attempt*, not per game: a model whose games run twice as
    long makes twice as many calls and would otherwise look twice as
    non-compliant for identical behaviour.
    """
    summary: dict = {}
    for role in ("codemaster", "guesser"):
        attempts = stats.get(f"{role}_attempts", 0)
        rejected = stats.get(f"{role}_rejected", 0)
        summary[f"{role}_attempts"] = attempts
        summary[f"{role}_rejected"] = rejected
        summary[f"{role}_call_failures"] = stats.get(f"{role}_call_failures", 0)
        summary[f"{role}_compliance_rate"] = (
            (attempts - rejected) / attempts if attempts else None
        )
    summary["rejection_reasons"] = {
        key.removeprefix("reason:"): value
        for key, value in sorted(stats.items())
        if key.startswith("reason:")
    }
    return summary


@dataclass
class LLMCodemaster:
    client: Any
    model: str
    method: str
    max_retries: int = 6

    def give_clue(
        self,
        board: Board,
        required_count: int | None = None,
        revealed: dict[str, str] | None = None,
        stats: Counter | None = None,
    ) -> dict:
        revealed = revealed or {}
        build_prompt = PROMPT_METHODS[self.method]
        system, base_user = build_prompt(board, required_count, revealed)
        user = base_user
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            if stats is not None:
                stats["codemaster_attempts"] += 1
            try:
                data = self.client.complete_json(self.model, system, user, max_retries=1)
                response = parse_codemaster_response(data)
                validate_clue_legality(response.clue, board)
                # intended_targets must be words the model was actually shown as
                # YOUR_WORDS — otherwise intended_recall/precision are corrupted.
                # Already-revealed targets are excluded: they've been found and
                # can't be re-targeted.
                target_words = [
                    w for w in board.words_with_role("target") if w not in revealed
                ]
                invalid = [w for w in response.intended_targets if w not in target_words]
                if invalid:
                    raise ValueError(f"intended_targets not on board: {invalid}")
                # A duplicate entry silently halves intended_recall for that
                # trial even though the model only meant to name one word.
                if len(set(response.intended_targets)) != len(response.intended_targets):
                    raise ValueError(f"duplicate intended_targets: {response.intended_targets}")
                # count must describe exactly the words intended_targets names —
                # otherwise the guesser's budget (count + 1) doesn't match what
                # the codemaster actually meant, and metrics using `count` (e.g.
                # target_recovery_rate) are computed against the wrong number.
                if response.count != len(response.intended_targets):
                    raise ValueError(
                        f"count {response.count} != len(intended_targets) "
                        f"{len(response.intended_targets)}"
                    )
                # The count constraint is a floor, so anything at or above it
                # passes. count 0 never does: it means an unlimited-guess clue,
                # not an ambitious one, and would otherwise slip under by being
                # numerically small.
                if required_count is not None and response.count < required_count:
                    raise ValueError(
                        f"count {response.count} is below the required floor "
                        f"of {required_count}"
                    )
                # Record the order the model actually emitted, not our
                # dataclass's field order. `translate_pipeline` asks for the
                # translation before the clue, and whether a model honours that
                # is the whole claim of the method — `asdict()` alone would
                # discard the only evidence of it.
                payload = asdict(response)
                ordered = {key: payload[key] for key in data if key in payload}
                ordered.update({k: v for k, v in payload.items() if k not in ordered})
                return ordered
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                if stats is not None:
                    stats["codemaster_rejected"] += 1
                    stats[f"reason:{classify_error(str(exc))}"] += 1
                # Tell the model what it got wrong; re-sending the identical
                # prompt just reproduces the same rejection.
                user = base_user + build_codemaster_correction(
                    str(exc), board, revealed, required_count
                )
                continue
        if stats is not None:
            stats["codemaster_call_failures"] += 1
        raise FormatFailure(
            f"Codemaster {self.model}/{self.method} failed after "
            f"{self.max_retries} attempts: {last_error}",
            raw_response=getattr(last_error, "raw_response", None),
        )


@dataclass
class LLMGuesser:
    client: Any
    model: str
    max_retries: int = 6

    def guess_one(
        self,
        words: list[str],
        clue: str,
        count: int,
        correct_so_far: list[str],
        revealed: dict[str, str] | None = None,
        stats: Counter | None = None,
    ) -> str | None:
        can_stop = len(correct_so_far) >= 1
        system, base_user = build_single_guess_prompt(
            words, clue, count, correct_so_far, can_stop, revealed
        )
        user = base_user
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            if stats is not None:
                stats["guesser_attempts"] += 1
            try:
                data = self.client.complete_json(self.model, system, user, max_retries=1)
                guess = parse_single_guess_response(data)
                if guess is None:
                    if not can_stop:
                        raise ValueError("cannot stop before guessing at least once")
                    return None
                if guess not in words:
                    raise ValueError(f"guess '{guess}' not among currently guessable words")
                return guess
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                if stats is not None:
                    stats["guesser_rejected"] += 1
                    stats[f"reason:{classify_error(str(exc))}"] += 1
                # Tell the model what it got wrong; re-sending the identical
                # prompt just reproduces the same rejection.
                user = base_user + build_guesser_correction(str(exc), words, can_stop)
                continue
        if stats is not None:
            stats["guesser_call_failures"] += 1
        raise FormatFailure(
            f"Guesser {self.model} failed after {self.max_retries} attempts: {last_error}",
            raw_response=getattr(last_error, "raw_response", None),
        )


@dataclass(frozen=True)
class ExperimentConfig:
    models: list[str]
    codemaster_prompt_methods: list[str]
    # The Guesser axis. A run crosses every codemaster with every entry here, so
    # a one-element list is the old fixed-guesser design and a four-element list
    # is the M3 grid. `guesser_model:` (scalar) in YAML still works and lands
    # here as a single-element list.
    guesser_models: list[str]
    board_styles: list[str]
    n_boards: int
    n_trials: int
    # Clue-count floors crossed by the run. `None` is free choice; an int N
    # requires every clue to point at N or more words. Defaults to free choice
    # alone, so every config written before M4 loads unchanged.
    count_constraints: list[int | None] = field(default_factory=lambda: [None])
    # First board seed to generate. Boards are deterministic from (style, seed),
    # so a later run can cover seeds 40-99 and pool with an earlier one that
    # covered 0-39 without replaying a single game. `--resume` cannot do this:
    # `_check_resume_matches` refuses any config change, n_boards included.
    board_seed_offset: int = 0
    # Concurrent games. Defaults to 1 so a run is only ever parallel by explicit
    # choice. Capped at len(models), which bounds concurrent *codemaster* calls
    # per provider to one. The guesser side is bounded by ceil(max_workers /
    # len(guesser_models)) instead: a single fixed guesser absorbs every worker
    # (as Haiku did on 2026-08-17), while a full grid halves that to one call
    # per provider per role. The cap deliberately stays on the codemaster axis
    # so crossing the guesser can only improve spread, never forbid a config
    # that already runs.
    max_workers: int = 1


_REQUIRED_CONFIG_KEYS = (
    "models",
    "codemaster_prompt_methods",
    "board_styles",
    "n_boards",
    "n_trials",
)

_GUESSER_KEY = "guesser_model"
_GUESSER_AXIS_KEY = "guesser_models"
_COUNT_AXIS_KEY = "count_constraints"


def load_config(path) -> ExperimentConfig:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must contain a YAML mapping, got {type(data).__name__}")

    missing = [key for key in _REQUIRED_CONFIG_KEYS if key not in data]
    if _GUESSER_KEY not in data and _GUESSER_AXIS_KEY not in data:
        missing.append(_GUESSER_KEY)
    if missing:
        raise ValueError(f"Config {path} is missing required key(s): {', '.join(missing)}")

    methods = data["codemaster_prompt_methods"]
    if not isinstance(methods, list) or not methods:
        raise ValueError(
            f"Config {path}: codemaster_prompt_methods must be a non-empty list, "
            f"got {methods!r}"
        )
    unknown = [m for m in methods if m not in PROMPT_METHODS]
    if unknown:
        raise ValueError(
            f"Config {path}: unknown codemaster_prompt_methods {unknown}; "
            f"valid options are {sorted(PROMPT_METHODS)}"
        )

    styles = data["board_styles"]
    if not isinstance(styles, list) or not styles:
        raise ValueError(
            f"Config {path}: board_styles must be a non-empty list, got {styles!r}"
        )
    # Only the active ladder may be designed into a new run. Retired styles stay
    # loadable in `board.py` so past runs regenerate and re-analyse, but naming
    # one here would silently produce a level the current design doesn't have.
    unknown_styles = [s for s in styles if s not in BOARD_STYLES]
    if unknown_styles:
        retired = sorted(set(unknown_styles) & set(RETIRED_BOARD_STYLES))
        detail = f"; {retired} are retired and can no longer be run" if retired else ""
        raise ValueError(
            f"Config {path}: unknown board_styles {unknown_styles}; "
            f"valid options are {sorted(BOARD_STYLES)}{detail}"
        )

    if _GUESSER_KEY in data and _GUESSER_AXIS_KEY in data:
        raise ValueError(
            f"Config {path}: name either {_GUESSER_KEY} (one fixed guesser) or "
            f"{_GUESSER_AXIS_KEY} (a guesser axis), not both — they would "
            f"silently disagree about how many guessers the run crosses."
        )

    if _GUESSER_AXIS_KEY in data:
        guessers = data[_GUESSER_AXIS_KEY]
        if not isinstance(guessers, list) or not guessers:
            raise ValueError(
                f"Config {path}: {_GUESSER_AXIS_KEY} must be a non-empty list, got {guessers!r}"
            )
    else:
        guessers = [data[_GUESSER_KEY]]

    for guesser in guessers:
        if not isinstance(guesser, str) or not guesser.strip():
            raise ValueError(
                f"Config {path}: every guesser must be a model id or "
                f"{SAME_AS_CODEMASTER!r}, got {guesser!r}"
            )
        # A near-miss on the sentinel used to pass validation and then be sent
        # to OpenRouter as a literal model id, failing every call at runtime.
        folded = guesser.strip().lower()
        if folded != SAME_AS_CODEMASTER and SAME_AS_CODEMASTER in folded.replace("-", "_"):
            raise ValueError(
                f"Config {path}: {guesser!r} looks like a misspelling of the "
                f"self-play sentinel {SAME_AS_CODEMASTER!r}"
            )

    duplicates = sorted({g for g in guessers if guessers.count(g) > 1})
    if duplicates:
        raise ValueError(
            f"Config {path}: {_GUESSER_AXIS_KEY} repeats {', '.join(duplicates)}; "
            f"a repeated guesser doubles that column's games and unbalances the grid"
        )

    constraints = data.get(_COUNT_AXIS_KEY, [None])
    if not isinstance(constraints, list) or not constraints:
        raise ValueError(
            f"Config {path}: {_COUNT_AXIS_KEY} must be a non-empty list, got {constraints!r}"
        )
    for value in constraints:
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(
                f"Config {path}: every entry in {_COUNT_AXIS_KEY} must be null "
                f"(free choice) or a positive integer, got {value!r}"
            )
    repeated = sorted({str(c) for c in constraints if constraints.count(c) > 1})
    if repeated:
        raise ValueError(
            f"Config {path}: {_COUNT_AXIS_KEY} repeats {', '.join(repeated)}; "
            f"a repeated level doubles that arm's games and unbalances the design"
        )

    for key in ("n_boards", "n_trials"):
        value = data[key]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"Config {path}: {key} must be a positive integer, got {value!r}")

    seed_offset = data.get("board_seed_offset", 0)
    if not isinstance(seed_offset, int) or isinstance(seed_offset, bool) or seed_offset < 0:
        raise ValueError(
            f"Config {path}: board_seed_offset must be a non-negative integer, "
            f"got {seed_offset!r}"
        )

    max_workers = data.get("max_workers", 1)
    if not isinstance(max_workers, int) or isinstance(max_workers, bool) or max_workers <= 0:
        raise ValueError(
            f"Config {path}: max_workers must be a positive integer, got {max_workers!r}"
        )
    if max_workers > len(data["models"]):
        raise ValueError(
            f"Config {path}: max_workers ({max_workers}) exceeds the number of models "
            f"({len(data['models'])}). Work is interleaved by model so that concurrent "
            f"games hit different providers; more workers than models puts several on "
            f"the same provider, which is what triggers rate limiting."
        )

    return ExperimentConfig(
        models=data["models"],
        codemaster_prompt_methods=methods,
        guesser_models=guessers,
        board_styles=styles,
        n_boards=data["n_boards"],
        n_trials=data["n_trials"],
        count_constraints=constraints,
        board_seed_offset=seed_offset,
        max_workers=max_workers,
    )


def _play_round(
    guesser: Guesser,
    board: Board,
    clue: str,
    count: int,
    revealed: dict[str, str],
    call_delay: float,
    stats: Counter,
) -> tuple[list[str], list[dict], str, str | None]:
    """Run the interactive guess-by-guess loop for one clue.

    Mutates `revealed` in place as words are guessed. Returns
    (correct, guess_sequence, outcome, error).

    A guesser that exhausts its retries ends the round (like a voluntary
    stop) rather than aborting the whole game — a single bad call must not
    discard the rounds already played, which are expensive and valid data.
    """
    max_guesses = None if count == 0 else count + 1
    target_words = board.words_with_role("target")
    correct: list[str] = []
    guess_sequence: list[dict] = []

    while True:
        # The game is won the moment the last TARGET is revealed. `run_game`
        # only tests that between rounds, so without this check a guesser
        # that finds the last target mid-round keeps being asked to guess
        # with nothing but non-targets (the assassin included) left to hit.
        if all(w in revealed for w in target_words):
            return correct, guess_sequence, "all_correct", None

        if max_guesses is not None and len(correct) >= max_guesses:
            return correct, guess_sequence, "all_correct", None

        remaining = [w for w in board.words if w not in revealed]
        if not remaining:
            outcome = "all_correct" if correct else "stopped_early"
            return correct, guess_sequence, outcome, None

        try:
            guess = guesser.guess_one(
                remaining, clue, count, correct, revealed=dict(revealed), stats=stats
            )
        except FormatFailure as exc:
            return correct, guess_sequence, "guesser_failure", str(exc)
        finally:
            if call_delay:
                time.sleep(call_delay)

        if guess is None:
            return correct, guess_sequence, "stopped_early", None

        role = board.role_of(guess)
        revealed[guess] = role
        guess_sequence.append({"word": guess, "role": role})
        if role == "target":
            correct.append(guess)
            continue
        return correct, guess_sequence, _OUTCOME_BY_ROLE[role], None


def run_game(
    codemaster: Codemaster,
    guesser: Guesser,
    board: Board,
    model: str,
    method: str,
    trial: int,
    call_delay: float = 0.0,
    max_rounds: int | None = None,
    guesser_model: str | None = None,
    count_floor: int | None = None,
) -> dict:
    """Play one game, timing it.

    Timing is attached here rather than inside `_play_game` so that every
    exit path carries it, including the error returns. Once games run
    concurrently, wall-clock/n_games no longer gives per-game duration, and
    `duration_s` is the only way to tell provider throttling (one model's
    games slow down, rejections stay flat) from genuine non-compliance.
    """
    started_at = datetime.now(timezone.utc)
    t0 = time.monotonic()
    row = _play_game(
        codemaster, guesser, board, model, method, trial,
        call_delay, max_rounds, guesser_model, count_floor,
    )
    return {
        **row,
        "started_at": started_at.isoformat(),
        "duration_s": round(time.monotonic() - t0, 3),
    }


def _play_game(
    codemaster: Codemaster,
    guesser: Guesser,
    board: Board,
    model: str,
    method: str,
    trial: int,
    call_delay: float = 0.0,
    max_rounds: int | None = None,
    guesser_model: str | None = None,
    count_floor: int | None = None,
) -> dict:
    base = {
        "model": model,
        "method": method,
        # Varies per row under self-play, so it has to be recorded here rather
        # than inferred from the run config.
        "guesser_model": guesser_model,
        "board_seed": board.seed,
        "board_style": board.style,
        "trial": trial,
        # Which arm of the count-constraint axis this game belongs to.
        "count_constraint": count_constraint_label(count_floor),
    }
    if max_rounds is None:
        # Safety backstop, not the expected path: a round that guesses at all
        # reveals at least one word, so the game is structurally bounded by
        # the board size. (Rounds lost to guesser failures reveal nothing;
        # `_MAX_CONSECUTIVE_STALLS` bounds those separately.)
        max_rounds = len(board.words)

    revealed: dict[str, str] = {}
    target_words = set(board.words_with_role("target"))
    # Revealing every OPPONENT word means the opposing team has found all of
    # its own — a loss, exactly as in the physical game. Taken from the board
    # rather than ROLE_COUNTS so a non-standard board scores by its own key.
    opponent_words = set(board.words_with_role("opponent"))
    rounds: list[dict] = []
    stats: Counter = Counter()
    outcome = "max_rounds_reached"
    loss_reason: str | None = None
    terminal_error: str | None = None
    consecutive_stalls = 0

    for round_num in range(1, max_rounds + 1):
        try:
            # Cap the floor at the targets still hidden. Without this, the
            # endgame of every constrained game is unsatisfiable — 16.5% of
            # rounds on the 08-19 grid had fewer than 3 targets left — and the
            # model would burn all its retries and die as a codemaster_failure.
            # The effective value is recorded per round, so the stricter
            # analysis (rounds where the FULL floor applied) stays recoverable.
            available = len(target_words - revealed.keys())
            effective_floor = min(count_floor, available) if count_floor else None
            cm = codemaster.give_clue(
                board, effective_floor, revealed=dict(revealed), stats=stats
            )
        except FormatFailure as exc:
            # No clue means no round to play. End the game but keep every
            # round already completed.
            outcome = "codemaster_failure"
            terminal_error = str(exc)
            break
        except Exception as exc:  # backstop: a harness/infra failure must not abort the run
            return {
                **base,
                "status": "error",
                "stage": "codemaster",
                "round": round_num,
                "rounds": rounds,
                "error": f"{type(exc).__name__}: {exc}",
            }
        if call_delay:
            time.sleep(call_delay)

        try:
            correct, guess_sequence, round_outcome, round_error = _play_round(
                guesser, board, cm["clue"], cm["count"], revealed, call_delay, stats
            )
        except Exception as exc:  # backstop: a harness/infra failure must not abort the run
            return {
                **base,
                "status": "error",
                "stage": "guesser",
                "round": round_num,
                "rounds": rounds,
                "error": f"{type(exc).__name__}: {exc}",
                **cm,
            }

        assassin_hit = round_outcome == "hit_assassin"
        round_metrics = compute_round_metrics(
            cm["count"], cm["intended_targets"], correct, round_outcome, assassin_hit
        )
        rounds.append(
            {
                "round": round_num,
                "required_count": effective_floor,
                **cm,
                "guess_sequence": guess_sequence,
                "error": round_error,
                **round_metrics,
            }
        )

        # The three terminal conditions cannot co-occur within one round — a
        # non-target guess ends the round immediately, and `_play_round`
        # returns as soon as the last target falls — but the order is written
        # out anyway so it never has to be re-derived.
        if assassin_hit:
            outcome = "loss"
            loss_reason = "assassin"
            break
        if target_words <= revealed.keys():
            outcome = "win"
            break
        if opponent_words <= revealed.keys():
            outcome = "loss"
            loss_reason = "opponent_words"
            break

        # A round that revealed nothing made no progress; repeating it just
        # burns API calls on a guesser that can't answer for this board.
        if guess_sequence:
            consecutive_stalls = 0
        else:
            consecutive_stalls += 1
            if consecutive_stalls >= _MAX_CONSECUTIVE_STALLS:
                outcome = "stalled"
                terminal_error = round_error
                break

    targets_found = len(target_words & revealed.keys())
    return {
        **base,
        "status": "ok",
        "outcome": outcome,
        # Which of the two ways the game was lost; None on any other outcome.
        "loss_reason": loss_reason,
        "game_length": len(rounds),
        "targets_found": targets_found,
        "target_recovery_rate": targets_found / len(target_words) if target_words else None,
        # Must come from the event, not from `outcome`: a loss is no longer
        # necessarily an assassin loss.
        "assassin_hit": loss_reason == "assassin",
        "opponent_words_revealed": len(opponent_words & revealed.keys()),
        "terminal_error": terminal_error,
        **_compliance_summary(stats),
        "rounds": rounds,
    }


_CSV_FIELDNAMES = [
    "model",
    "method",
    "guesser_model",
    "board_seed",
    "board_style",
    "trial",
    "count_constraint",
    "status",
    "stage",
    "outcome",
    "loss_reason",
    "game_length",
    "targets_found",
    "target_recovery_rate",
    "assassin_hit",
    "opponent_words_revealed",
    "codemaster_attempts",
    "codemaster_rejected",
    "codemaster_compliance_rate",
    "codemaster_call_failures",
    "guesser_attempts",
    "guesser_rejected",
    "guesser_compliance_rate",
    "guesser_call_failures",
    "started_at",
    "duration_s",
    "terminal_error",
    "error",
]

# Rows are written to raw.jsonl in completion order once games run
# concurrently, so the rolled-up CSV is sorted to stay deterministic and
# diffable across runs.
_CSV_SORT_KEY = (
    "model", "method", "guesser_model", "count_constraint",
    "board_style", "board_seed", "trial",
)


def _write_metrics_csv(rows: list[dict], path: Path) -> None:
    ordered = sorted(
        rows,
        # "" keeps rows sortable when a key is absent (error rows) or None
        # (board_style on older runs) — mixed None/str would raise.
        key=lambda r: tuple(str(r.get(k) or "") for k in _CSV_SORT_KEY),
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in ordered:
            writer.writerow(row)


def _board_to_dict(board: Board) -> dict:
    return {
        "seed": board.seed,
        "style": board.style,
        "words": list(board.words),
        "roles": dict(board.roles),
        "is_dual": {w: board.is_dual(w) for w in board.words},
    }


def _write_run_manifest(
    run_dir: Path,
    boards: list[Board],
    config: ExperimentConfig,
    config_path,
    max_workers: int = 1,
) -> None:
    """Persist the exact boards used and the config, so a run is self-describing."""
    (run_dir / "boards.json").write_text(
        json.dumps([_board_to_dict(b) for b in boards], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if config_path is not None:
        content = Path(config_path).read_text(encoding="utf-8")
    else:
        content = yaml.safe_dump(asdict(config), allow_unicode=True, sort_keys=False)
    (run_dir / "config.yaml").write_text(content, encoding="utf-8")
    # Recorded separately because it can be overridden per invocation, and
    # because `duration_s` is uninterpretable without knowing how many games
    # were competing for bandwidth alongside it.
    (run_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "max_workers": max_workers,
                "guesser_models": list(config.guesser_models),
                "count_constraints": list(config.count_constraints),
                "board_seeds": [
                    config.board_seed_offset,
                    config.board_seed_offset + config.n_boards - 1,
                ],
                "n_pairs": len(config.models) * len(config.guesser_models),
                "dispatch": "latin_square",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def resolve_guesser(model: str, guesser: str) -> str:
    """The guesser that actually plays, once the self-play sentinel is applied."""
    return model if guesser == SAME_AS_CODEMASTER else guesser


def _game_key(row: dict) -> tuple:
    """Identity of one game, matching the shape of a task tuple."""
    return (
        row.get("model"),
        row.get("guesser_model"),
        row.get("method"),
        # Rows written before M4 carry no constraint; they were all free choice.
        row.get("count_constraint") or "free",
        row.get("board_style"),
        row.get("board_seed"),
        row.get("trial"),
    )


def _task_key(task: tuple) -> tuple:
    model, guesser, method, floor, board, trial = task
    return (model, guesser, method, count_constraint_label(floor),
            board.style, board.seed, trial)


def _read_raw_rows(run_dir: Path) -> list[dict]:
    """Games already on disk. A trailing partial line is dropped, not fatal:
    a hard kill mid-write leaves one, and that game simply gets replayed."""
    path = run_dir / "raw.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _check_resume_matches(
    run_dir: Path, config: ExperimentConfig, boards: list[Board], done: set
) -> None:
    """Refuse to resume a run whose design does not match the config given.

    The games already on disk were played against a specific grid and a
    specific set of boards. Continuing with a different one would append a
    second experiment into the same file, and nothing downstream could tell
    the two apart — every row looks equally valid.

    The run's own `config.yaml` is the authority, not the recorded rows: a
    config that merely *grows* the grid (say n_boards 2 -> 5) leaves every
    existing row still playable, so comparing rows alone would wave it through.
    """
    recorded = run_dir / "config.yaml"
    if recorded.exists():
        original = load_config(recorded)
        design = ("models", "guesser_models", "codemaster_prompt_methods",
                  "board_styles", "n_boards", "n_trials", "count_constraints",
                  "board_seed_offset")
        differing = [
            f"{field}: {getattr(original, field)!r} -> {getattr(config, field)!r}"
            for field in design
            if getattr(original, field) != getattr(config, field)
        ]
        if differing:
            raise ValueError(
                f"Cannot resume {run_dir}: the config given describes a different "
                f"design than the run was started with ({'; '.join(differing)}). "
                f"Resume it with its own config.yaml, or start a new run."
            )

    playable = {_task_key(t) for t in _ordered_tasks(config, boards)}
    orphans = done - playable
    if orphans:
        raise ValueError(
            f"Cannot resume {run_dir}: {len(orphans)} recorded game(s) are not in "
            f"the grid this config describes (e.g. {sorted(orphans)[0]}). The run "
            f"was played against a different design — resume it with its own "
            f"config.yaml, or start a new run."
        )


def _ordered_tasks(config: ExperimentConfig, boards: list[Board]) -> list[tuple]:
    """One task per game, ordered so concurrent games spread across providers.

    Ordering is the rate-limit safety mechanism. Each model sits behind a
    different upstream provider, so dispatching model-by-model would point
    every concurrent worker at the SAME provider — the concentrated-burst
    pattern that killed a 180-game run with HTTP 429 (DECISIONS.md,
    2026-08-10). Now that a game occupies *two* providers, interleaving by
    codemaster alone is not enough: four games with four distinct codemasters
    could still share one guesser.

    So pairs are grouped into Latin-square rounds by the diagonal offset
    `k = (guesser_index - model_index) % n_guessers`. Every round holds one
    pair per codemaster with the guessers all distinct, and the pairs within a
    round are interleaved round-robin, so any `max_workers` consecutive tasks
    inside a round use distinct models in both roles.

    The perfect property does not extend across round handovers, and cannot:
    demanding that every sliding window of N be N-distinct in both roles forces
    both indices to cycle with period N, which reaches only N of the N^2 pairs.
    Two concurrent calls per provider is the achievable bound, and it is only
    reached in the (n_guessers - 1) brief handovers.
    """
    n_guessers = len(config.guesser_models)
    ordered: list[tuple] = []
    for offset in range(n_guessers):
        per_pair: list[list[tuple]] = []
        for index, model in enumerate(config.models):
            guesser = config.guesser_models[(index + offset) % n_guessers]
            per_pair.append(
                [
                    (model, resolve_guesser(model, guesser), method, floor, board, trial)
                    for method in config.codemaster_prompt_methods
                    for floor in config.count_constraints
                    for board in boards
                    for trial in range(config.n_trials)
                ]
            )
        ordered.extend(t for group in zip_longest(*per_pair) for t in group if t is not None)
    return ordered


def run_experiment(
    config: ExperimentConfig,
    word_lists: WordLists,
    make_codemaster: Callable[[str, str], Codemaster],
    make_guesser: Callable[[str], Guesser],
    results_dir,
    config_path=None,
    trial_delay: float = 3.0,
    max_workers: int | None = None,
    resume_from=None,
) -> Path:
    # Explicit argument wins; otherwise the config's value, defaulting to
    # sequential so nothing becomes concurrent by accident.
    if max_workers is None:
        max_workers = config.max_workers

    if resume_from is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir = Path(results_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir = Path(resume_from)
        if not run_dir.is_dir():
            raise ValueError(f"Cannot resume: {run_dir} is not a run directory")

    boards = [
        generate_board(word_lists.regular, word_lists.dual, seed=i, style=style)
        for style in config.board_styles
        for i in range(
            config.board_seed_offset, config.board_seed_offset + config.n_boards
        )
    ]

    done: set = set()
    existing: list[dict] = []
    if resume_from is not None:
        existing = _read_raw_rows(run_dir)
        done = {_game_key(row) for row in existing}
        _check_resume_matches(run_dir, config, boards, done)
    else:
        _write_run_manifest(run_dir, boards, config, config_path, max_workers)

    # Adapters are built up front, sequentially, rather than lazily inside
    # workers: construction order and count stay deterministic, and no two
    # threads race to build the same one.
    # Keyed by the guesser that actually plays, so a model appearing in both
    # roles — or in several pairs — is built once, not once per codemaster.
    guessers: dict[str, Guesser] = {}
    codemasters: dict[tuple[str, str], Codemaster] = {}
    for model in config.models:
        for method in config.codemaster_prompt_methods:
            codemasters[(model, method)] = make_codemaster(model, method)
    for model in config.models:
        for guesser in config.guesser_models:
            resolved = resolve_guesser(model, guesser)
            if resolved not in guessers:
                guessers[resolved] = make_guesser(resolved)

    tasks = [t for t in _ordered_tasks(config, boards) if _task_key(t) not in done]
    # Progress counts the whole run, not just this leg, so a resumed run reads
    # against the same denominator as the one that was interrupted.
    already = len(existing)
    total = already + len(tasks)
    if already:
        print(f"Resuming {run_dir}: {already} games already recorded, {len(tasks)} to play",
              flush=True)

    def play(task: tuple) -> dict:
        model, guesser, method, floor, board, trial = task
        try:
            return run_game(
                codemasters[(model, method)],
                guessers[guesser],
                board,
                model,
                method,
                trial,
                call_delay=trial_delay,
                guesser_model=guesser,
                count_floor=floor,
            )
        except Exception as exc:  # a poisoned task must not take down the pool
            return {
                "model": model,
                "method": method,
                "guesser_model": guesser,
                "count_constraint": count_constraint_label(floor),
                "board_seed": board.seed,
                "board_style": board.style,
                "trial": trial,
                "status": "error",
                "stage": "runner",
                "error": f"{type(exc).__name__}: {exc}",
                "rounds": [],
            }

    rows: list[dict] = list(existing)
    write_lock = threading.Lock()
    # Append, never truncate: the completed games in this file are the reason
    # resuming is possible at all.
    mode = "a" if existing else "w"
    with (run_dir / "raw.jsonl").open(mode, encoding="utf-8") as raw_file:

        def record(row: dict) -> None:
            # Flushed on every row: an unattended multi-hour run must not lose
            # completed games to a buffer on a hard kill, and progress has to
            # be observable while it runs.
            with write_lock:
                raw_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                raw_file.flush()
                rows.append(row)
                print(
                    f"[{len(rows):>5}/{total}] {row['model']} "
                    f"vs {row.get('guesser_model')} {row.get('board_style')} "
                    f"{row['method']} -> {row.get('outcome') or row.get('status')}",
                    flush=True,
                )

        if max_workers <= 1:
            for task in tasks:
                record(play(task))
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for future in as_completed(pool.submit(play, t) for t in tasks):
                    record(future.result())

    _write_metrics_csv(rows, run_dir / "metrics.csv")
    return run_dir
