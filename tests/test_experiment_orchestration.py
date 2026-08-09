import csv
import json
from pathlib import Path

import pytest

from codenames_heb.board import Board, generate_board
from codenames_heb.experiment import ExperimentConfig, load_config, run_experiment, run_trial
from codenames_heb.llm_client import FormatFailure


def _board() -> Board:
    return Board(
        seed=1,
        words=["t1", "t2", "t3", "o1", "c1", "a1"],
        roles={
            "t1": "target",
            "t2": "target",
            "t3": "target",
            "o1": "opponent",
            "c1": "civilian",
            "a1": "assassin",
        },
    )


class StubCodemaster:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def give_clue(self, board, required_count=None):
        if self.error:
            raise self.error
        return self.response


class StubGuesser:
    def __init__(self, guesses=None, error=None):
        self.guesses = guesses if guesses is not None else []
        self.error = error

    def guess(self, words, clue, count):
        if self.error:
            raise self.error
        return self.guesses


def test_run_trial_returns_ok_status_with_metrics():
    codemaster = StubCodemaster(
        response={"clue": "x", "count": 2, "intended_targets": ["t1", "t2"], "reasoning": "r"}
    )
    guesser = StubGuesser(guesses=["t1", "t2"])

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["model"] == "m"
    assert row["method"] == "strong_hebrew"
    assert row["board_seed"] == 1
    assert row["trial"] == 0
    assert row["guesses_before_miss"] == 2
    # Budget is count + 1 = 3; only 2 of 3 guesses were used (no wrong guess,
    # guesser just stopped), so per compute_metrics' established semantics
    # (see test_stopped_early_when_fewer_guesses_than_budget_all_correct in
    # test_metrics.py) this is "stopped_early", not "all_correct".
    assert row["turn_outcome"] == "stopped_early"


def test_run_trial_returns_format_failure_when_codemaster_fails():
    codemaster = StubCodemaster(error=FormatFailure("bad codemaster output"))
    guesser = StubGuesser()

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "format_failure"
    assert row["stage"] == "codemaster"


def test_run_trial_returns_format_failure_when_guesser_fails():
    codemaster = StubCodemaster(
        response={"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}
    )
    guesser = StubGuesser(error=FormatFailure("bad guesser output"))

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "format_failure"
    assert row["stage"] == "guesser"


def test_load_config_reads_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "models: [model-a, model-b]\n"
        "codemaster_prompt_methods: [strong_hebrew, translate_pipeline]\n"
        "guesser_model: guesser-model\n"
        "board_style: standard\n"
        "n_boards: 2\n"
        "n_trials: 1\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config == ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew", "translate_pipeline"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=2,
        n_trials=1,
    )


def test_run_experiment_writes_expected_number_of_rows(tmp_path):
    config = ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=2,
        n_trials=2,
    )
    word_pool = [f"word{i}" for i in range(40)]

    def make_codemaster(model, method):
        return StubCodemaster(
            response={"clue": "x", "count": 1, "intended_targets": [], "reasoning": "r"}
        )

    def make_guesser(model):
        return StubGuesser(guesses=[])

    run_dir = run_experiment(
        config=config,
        word_pool=word_pool,
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
    )

    raw_lines = (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    # 2 models x 1 method x 2 boards x 2 trials
    assert len(raw_lines) == 8
    for line in raw_lines:
        json.loads(line)  # each line is valid JSON

    with (run_dir / "metrics.csv").open(encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 8


def test_run_experiment_reuses_same_boards_across_models(tmp_path):
    config = ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=1,
        n_trials=1,
    )
    word_pool = [f"word{i}" for i in range(40)]

    def make_codemaster(model, method):
        return StubCodemaster(
            response={"clue": "x", "count": 1, "intended_targets": [], "reasoning": "r"}
        )

    def make_guesser(model):
        return StubGuesser(guesses=[])

    run_dir = run_experiment(
        config=config,
        word_pool=word_pool,
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
    )

    rows = [json.loads(line) for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()]
    board_seeds = {row["board_seed"] for row in rows}
    assert board_seeds == {0}
