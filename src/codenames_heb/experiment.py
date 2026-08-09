import csv
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from codenames_heb.board import Board, generate_board
from codenames_heb.llm_client import FormatFailure
from codenames_heb.metrics import compute_metrics
from codenames_heb.prompts.codemaster import (
    PROMPT_METHODS,
    parse_codemaster_response,
    validate_clue_legality,
)
from codenames_heb.prompts.guesser import build_guesser_prompt, parse_guesser_response
from codenames_heb.roles import Codemaster, Guesser


@dataclass
class LLMCodemaster:
    client: Any
    model: str
    method: str
    max_retries: int = 3

    def give_clue(self, board: Board, required_count: int | None = None) -> dict:
        build_prompt = PROMPT_METHODS[self.method]
        system, user = build_prompt(board, required_count)
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            try:
                data = self.client.complete_json(self.model, system, user, max_retries=1)
                response = parse_codemaster_response(data)
                validate_clue_legality(response.clue, board)
                # intended_targets must be words the model was actually shown as
                # YOUR_WORDS — otherwise intended_recall/precision are corrupted.
                target_words = board.words_with_role("target")
                invalid = [w for w in response.intended_targets if w not in target_words]
                if invalid:
                    raise ValueError(f"intended_targets not on board: {invalid}")
                # A duplicate entry silently halves intended_recall for that
                # trial even though the model only meant to name one word.
                if len(set(response.intended_targets)) != len(response.intended_targets):
                    raise ValueError(f"duplicate intended_targets: {response.intended_targets}")
                return asdict(response)
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Codemaster {self.model}/{self.method} failed after "
            f"{self.max_retries} attempts: {last_error}",
            raw_response=getattr(last_error, "raw_response", None),
        )


@dataclass
class LLMGuesser:
    client: Any
    model: str
    max_retries: int = 3

    def guess(self, words: list[str], clue: str, count: int) -> list[str]:
        system, user = build_guesser_prompt(words, clue, count)
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            try:
                data = self.client.complete_json(self.model, system, user, max_retries=1)
                guesses = parse_guesser_response(data)
                invalid = [g for g in guesses if g not in words]
                if invalid:
                    raise ValueError(f"guesses not on board: {invalid}")
                # A revealed word can't be re-guessed in real Codenames; repeats
                # would inflate guesses_before_miss / recovery / recall.
                if len(set(guesses)) != len(guesses):
                    raise ValueError(f"duplicate guesses: {guesses}")
                return guesses
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Guesser {self.model} failed after {self.max_retries} attempts: {last_error}",
            raw_response=getattr(last_error, "raw_response", None),
        )


@dataclass(frozen=True)
class ExperimentConfig:
    models: list[str]
    codemaster_prompt_methods: list[str]
    guesser_model: str
    board_style: str
    n_boards: int
    n_trials: int


_REQUIRED_CONFIG_KEYS = (
    "models",
    "codemaster_prompt_methods",
    "guesser_model",
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

    for key in ("n_boards", "n_trials"):
        value = data[key]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"Config {path}: {key} must be a positive integer, got {value!r}")

    return ExperimentConfig(
        models=data["models"],
        codemaster_prompt_methods=methods,
        guesser_model=data["guesser_model"],
        board_style=data.get("board_style", "standard"),
        n_boards=data["n_boards"],
        n_trials=data["n_trials"],
    )


def run_trial(
    codemaster: Codemaster,
    guesser: Guesser,
    board: Board,
    model: str,
    method: str,
    trial: int,
) -> dict:
    base = {"model": model, "method": method, "board_seed": board.seed, "trial": trial}

    try:
        cm = codemaster.give_clue(board)
    except FormatFailure as exc:
        return {
            **base,
            "status": "format_failure",
            "stage": "codemaster",
            "error": str(exc),
            "raw_response": getattr(exc, "raw_response", None),
        }
    except Exception as exc:  # backstop: a harness/infra failure must not abort the run
        return {
            **base,
            "status": "error",
            "stage": "codemaster",
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        guesses = guesser.guess(board.words, cm["clue"], cm["count"])
    except FormatFailure as exc:
        return {
            **base,
            "status": "format_failure",
            "stage": "guesser",
            "error": str(exc),
            "raw_response": getattr(exc, "raw_response", None),
            **cm,
        }
    except Exception as exc:  # backstop: a harness/infra failure must not abort the run
        return {
            **base,
            "status": "error",
            "stage": "guesser",
            "error": f"{type(exc).__name__}: {exc}",
            **cm,
        }

    metrics = compute_metrics(board, cm["count"], cm["intended_targets"], guesses)
    return {**base, "status": "ok", **cm, "guesses": guesses, **metrics}


_CSV_FIELDNAMES = [
    "model",
    "method",
    "board_seed",
    "trial",
    "status",
    "stage",
    "clue",
    "count",
    "guesses_before_miss",
    "turn_outcome",
    "assassin_hit",
    "target_recovery_rate",
    "intended_recall",
    "intended_precision",
]


def _write_metrics_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _board_to_dict(board: Board) -> dict:
    return {"seed": board.seed, "words": list(board.words), "roles": dict(board.roles)}


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
    word_pool: list[str],
    make_codemaster: Callable[[str, str], Codemaster],
    make_guesser: Callable[[str], Guesser],
    results_dir,
    config_path=None,
    trial_delay: float = 0.5,
) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = Path(results_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    boards = [generate_board(word_pool, seed=i) for i in range(config.n_boards)]
    guesser = make_guesser(config.guesser_model)

    _write_run_manifest(run_dir, boards, config, config_path)

    rows: list[dict] = []
    with (run_dir / "raw.jsonl").open("w", encoding="utf-8") as raw_file:
        for model in config.models:
            for method in config.codemaster_prompt_methods:
                codemaster = make_codemaster(model, method)
                for board in boards:
                    for trial in range(config.n_trials):
                        row = run_trial(codemaster, guesser, board, model, method, trial)
                        raw_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                        rows.append(row)
                        if trial_delay:
                            time.sleep(trial_delay)

    _write_metrics_csv(rows, run_dir / "metrics.csv")
    return run_dir
