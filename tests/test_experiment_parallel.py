"""Parallel dispatch: same work, safely scheduled.

The runner plays games concurrently to cut wall-clock on long runs. What
must not change is *which* games get played or what gets recorded — only
the order they complete in.
"""
import csv
import json

import pytest

from codenames_heb.experiment import (
    ExperimentConfig,
    _ordered_tasks,
    load_config,
    run_experiment,
)
from codenames_heb.words import WordLists


def _word_lists() -> WordLists:
    return WordLists(
        regular=[f"reg{i}" for i in range(40)],
        dual=[f"dual{i}" for i in range(40)],
    )


def _config(**overrides) -> ExperimentConfig:
    defaults = dict(
        models=["model-a"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_models=["guesser-model"],
        board_styles=["natural"],
        n_boards=2,
        n_trials=1,
    )
    defaults.update(overrides)
    return ExperimentConfig(**defaults)


class AutoCodemaster:
    def give_clue(self, board, required_count=None, revealed=None, stats=None):
        return {"clue": "x", "count": 0, "intended_targets": [], "reasoning": "r"}


class AutoGuesser:
    """Reveals one word per round, so any board terminates."""

    def guess_one(self, words, clue, count, correct_so_far, revealed=None, stats=None):
        return None if correct_so_far else words[0]


def _factories():
    return (lambda model, method: AutoCodemaster()), (lambda model: AutoGuesser())


def _run(tmp_path, workers, **cfg):
    make_codemaster, make_guesser = _factories()
    return run_experiment(
        config=_config(**cfg),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path / f"w{workers}",
        trial_delay=0,
        max_workers=workers,
    )


def _rows(run_dir) -> list[dict]:
    text = (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip()
    return [json.loads(line) for line in text.splitlines()]


def _cells(run_dir) -> set:
    return {
        (r["model"], r["method"], r["board_style"], r["board_seed"], r["trial"])
        for r in _rows(run_dir)
    }


def test_parallel_produces_the_same_games_as_sequential(tmp_path):
    cfg = dict(models=["model-a", "model-b", "model-c"], n_boards=3, n_trials=2)

    sequential = _run(tmp_path, 1, **cfg)
    parallel = _run(tmp_path, 3, **cfg)

    # Same work, however it was scheduled — only completion order differs.
    assert _cells(parallel) == _cells(sequential)
    assert len(_cells(parallel)) == 3 * 3 * 2  # models x boards x trials


def test_raw_jsonl_is_uncorrupted_by_concurrent_writes(tmp_path):
    run_dir = _run(tmp_path, 4, models=["a", "b", "c", "d"], n_boards=4)

    lines = (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4 * 4  # nothing lost or duplicated under the lock
    for line in lines:
        json.loads(line)  # no torn or interleaved writes


def test_metrics_csv_is_sorted_regardless_of_completion_order(tmp_path):
    run_dir = _run(tmp_path, 3, models=["model-c", "model-a", "model-b"], n_boards=2)

    with (run_dir / "metrics.csv").open(encoding="utf-8") as f:
        keys = [(r["model"], r["board_seed"]) for r in csv.DictReader(f)]

    # raw.jsonl is completion-ordered, but the rolled-up CSV stays stable so
    # runs remain diffable.
    assert keys == sorted(keys)


def test_adapters_are_built_up_front_not_raced_by_workers(tmp_path):
    built_cm, built_g = [], []

    def make_codemaster(model, method):
        built_cm.append((model, method))
        return AutoCodemaster()

    def make_guesser(model):
        built_g.append(model)
        return AutoGuesser()

    run_experiment(
        config=_config(models=["model-a", "model-b"], n_boards=5, n_trials=2),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
        max_workers=2,
    )

    # One per cell, in config order — not once per game, and not concurrently.
    assert built_cm == [("model-a", "strong_hebrew"), ("model-b", "strong_hebrew")]
    # One per distinct guesser, so a fixed guesser is built once for the run.
    assert built_g == ["guesser-model"]


def test_one_poisoned_game_does_not_take_down_the_pool(tmp_path):
    class ExplodingCodemaster:
        def give_clue(self, board, required_count=None, revealed=None, stats=None):
            raise RuntimeError("boom")

    def make_codemaster(model, method):
        return ExplodingCodemaster() if model == "model-b" else AutoCodemaster()

    _, make_guesser = _factories()
    run_dir = run_experiment(
        config=_config(models=["model-a", "model-b"], n_boards=3),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
        max_workers=2,
    )

    rows = _rows(run_dir)
    assert len(rows) == 6  # every task still produced a row
    assert all(r["status"] == "ok" for r in rows if r["model"] == "model-a")
    assert all(
        r["status"] == "error" and "boom" in r["error"]
        for r in rows
        if r["model"] == "model-b"
    )


def test_every_row_carries_timing_telemetry(tmp_path):
    for row in _rows(_run(tmp_path, 2, models=["model-a", "model-b"], n_boards=2)):
        assert row["duration_s"] >= 0
        assert row["started_at"].startswith("20")  # ISO-8601


def test_run_meta_records_max_workers(tmp_path):
    run_dir = _run(tmp_path, 2, models=["model-a", "model-b"])

    # duration_s can't be read without knowing the concurrency it ran at.
    meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["max_workers"] == 2


def test_tasks_interleave_by_model_so_workers_hit_different_providers():
    from codenames_heb.board import generate_board

    words = _word_lists()
    boards = [generate_board(words.regular, words.dual, seed=i, style="natural") for i in (0, 1)]

    order = [t[0] for t in _ordered_tasks(_config(models=["a", "b", "c"], n_boards=2), boards)]

    # Consecutive tasks rotate models. Dispatching model-by-model would aim
    # every concurrent worker at the same upstream provider, which is the
    # burst pattern that caused HTTP 429 collapse (DECISIONS.md 2026-08-10).
    assert order[:6] == ["a", "b", "c", "a", "b", "c"]
    assert sorted(order) == sorted(["a", "b", "c"] * 2)


def _write_config(tmp_path, text: str):
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


_CONFIG_TEXT = (
    "models: [model-a]\n"
    "codemaster_prompt_methods: [strong_hebrew]\n"
    "guesser_model: guesser-model\n"
    "board_styles: [natural]\n"
    "n_boards: 2\n"
    "n_trials: 1\n"
)


def test_load_config_defaults_to_sequential(tmp_path):
    assert load_config(_write_config(tmp_path, _CONFIG_TEXT)).max_workers == 1


def test_load_config_reads_max_workers(tmp_path):
    text = _CONFIG_TEXT.replace("models: [model-a]", "models: [model-a, model-b]")
    assert load_config(_write_config(tmp_path, text + "max_workers: 2\n")).max_workers == 2


def test_load_config_rejects_more_workers_than_models(tmp_path):
    path = _write_config(tmp_path, _CONFIG_TEXT + "max_workers: 4\n")

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    assert "max_workers" in str(excinfo.value)
