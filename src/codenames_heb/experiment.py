import csv
import json
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
                return asdict(response)
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Codemaster {self.model}/{self.method} failed after "
            f"{self.max_retries} attempts: {last_error}"
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
                return guesses
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Guesser {self.model} failed after {self.max_retries} attempts: {last_error}"
        )


@dataclass(frozen=True)
class ExperimentConfig:
    models: list[str]
    codemaster_prompt_methods: list[str]
    guesser_model: str
    board_style: str
    n_boards: int
    n_trials: int


def load_config(path) -> ExperimentConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ExperimentConfig(
        models=data["models"],
        codemaster_prompt_methods=data["codemaster_prompt_methods"],
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
        return {**base, "status": "format_failure", "stage": "codemaster", "error": str(exc)}

    try:
        guesses = guesser.guess(board.words, cm["clue"], cm["count"])
    except FormatFailure as exc:
        return {**base, "status": "format_failure", "stage": "guesser", "error": str(exc), **cm}

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


def run_experiment(
    config: ExperimentConfig,
    word_pool: list[str],
    make_codemaster: Callable[[str, str], Codemaster],
    make_guesser: Callable[[str], Guesser],
    results_dir,
) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = Path(results_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    boards = [generate_board(word_pool, seed=i) for i in range(config.n_boards)]
    guesser = make_guesser(config.guesser_model)

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

    _write_metrics_csv(rows, run_dir / "metrics.csv")
    return run_dir
