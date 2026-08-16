import csv
import json
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from codenames_heb.board import BOARD_STYLES, Board, generate_board
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
                return asdict(response)
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                if stats is not None:
                    stats["codemaster_rejected"] += 1
                    stats[f"reason:{classify_error(str(exc))}"] += 1
                # Tell the model what it got wrong; re-sending the identical
                # prompt just reproduces the same rejection.
                user = base_user + build_codemaster_correction(str(exc), board, revealed)
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
    guesser_model: str
    board_styles: list[str]
    n_boards: int
    n_trials: int


_REQUIRED_CONFIG_KEYS = (
    "models",
    "codemaster_prompt_methods",
    "guesser_model",
    "board_styles",
    "n_boards",
    "n_trials",
)


def load_config(path) -> ExperimentConfig:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must contain a YAML mapping, got {type(data).__name__}")

    missing = [key for key in _REQUIRED_CONFIG_KEYS if key not in data]
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
    unknown_styles = [s for s in styles if s not in BOARD_STYLES]
    if unknown_styles:
        raise ValueError(
            f"Config {path}: unknown board_styles {unknown_styles}; "
            f"valid options are {sorted(BOARD_STYLES)}"
        )

    guesser_model = data["guesser_model"]
    if not isinstance(guesser_model, str) or not guesser_model.strip():
        raise ValueError(
            f"Config {path}: guesser_model must be a model id or "
            f"{SAME_AS_CODEMASTER!r}, got {guesser_model!r}"
        )

    for key in ("n_boards", "n_trials"):
        value = data[key]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"Config {path}: {key} must be a positive integer, got {value!r}")

    return ExperimentConfig(
        models=data["models"],
        codemaster_prompt_methods=methods,
        guesser_model=data["guesser_model"],
        board_styles=styles,
        n_boards=data["n_boards"],
        n_trials=data["n_trials"],
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
    }
    if max_rounds is None:
        # Safety backstop, not the expected path: a round that guesses at all
        # reveals at least one word, so the game is structurally bounded by
        # the board size. (Rounds lost to guesser failures reveal nothing;
        # `_MAX_CONSECUTIVE_STALLS` bounds those separately.)
        max_rounds = len(board.words)

    revealed: dict[str, str] = {}
    target_words = set(board.words_with_role("target"))
    rounds: list[dict] = []
    stats: Counter = Counter()
    outcome = "max_rounds_reached"
    terminal_error: str | None = None
    consecutive_stalls = 0

    for round_num in range(1, max_rounds + 1):
        try:
            cm = codemaster.give_clue(board, revealed=dict(revealed), stats=stats)
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
                **cm,
                "guess_sequence": guess_sequence,
                "error": round_error,
                **round_metrics,
            }
        )

        if assassin_hit:
            outcome = "loss"
            break
        if target_words <= revealed.keys():
            outcome = "win"
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
        "game_length": len(rounds),
        "targets_found": targets_found,
        "target_recovery_rate": targets_found / len(target_words) if target_words else None,
        "assassin_hit": outcome == "loss",
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
    "status",
    "stage",
    "outcome",
    "game_length",
    "targets_found",
    "target_recovery_rate",
    "assassin_hit",
    "codemaster_attempts",
    "codemaster_rejected",
    "codemaster_compliance_rate",
    "codemaster_call_failures",
    "guesser_attempts",
    "guesser_rejected",
    "guesser_compliance_rate",
    "guesser_call_failures",
    "terminal_error",
    "error",
]


def _write_metrics_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
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
    run_dir: Path, boards: list[Board], config: ExperimentConfig, config_path
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


def run_experiment(
    config: ExperimentConfig,
    word_lists: WordLists,
    make_codemaster: Callable[[str, str], Codemaster],
    make_guesser: Callable[[str], Guesser],
    results_dir,
    config_path=None,
    trial_delay: float = 3.0,
) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = Path(results_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    boards = [
        generate_board(word_lists.regular, word_lists.dual, seed=i, style=style)
        for style in config.board_styles
        for i in range(config.n_boards)
    ]

    _write_run_manifest(run_dir, boards, config, config_path)

    rows: list[dict] = []
    with (run_dir / "raw.jsonl").open("w", encoding="utf-8") as raw_file:
        for model in config.models:
            # Under self-play the guesser changes with the codemaster, so it is
            # rebuilt per model rather than once for the whole run.
            guesser_model = (
                model if config.guesser_model == SAME_AS_CODEMASTER else config.guesser_model
            )
            guesser = make_guesser(guesser_model)
            for method in config.codemaster_prompt_methods:
                codemaster = make_codemaster(model, method)
                for board in boards:
                    for trial in range(config.n_trials):
                        row = run_game(
                            codemaster,
                            guesser,
                            board,
                            model,
                            method,
                            trial,
                            call_delay=trial_delay,
                            guesser_model=guesser_model,
                        )
                        raw_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                        rows.append(row)

    _write_metrics_csv(rows, run_dir / "metrics.csv")
    return run_dir
