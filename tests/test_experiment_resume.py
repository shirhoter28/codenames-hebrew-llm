"""Resuming a run that died partway.

A 320-game grid takes ~3 hours and there was no way to continue one: the
2026-08-19 run was killed at game 82 with 82 valid games on disk and no way to
use them. `raw.jsonl` is already flushed per row precisely so a hard kill keeps
its completed games — resume is what makes that durability worth anything.
"""

import json
from pathlib import Path

import pytest

from codenames_heb.experiment import ExperimentConfig, run_experiment
from codenames_heb.words import WordLists


def _word_lists() -> WordLists:
    return WordLists(
        regular=[f"reg{i}" for i in range(40)],
        dual=[f"dual{i}" for i in range(40)],
    )


class _Codemaster:
    def give_clue(self, board, required_count=None, revealed=None, stats=None):
        if stats is not None:
            stats["codemaster_attempts"] += 1
        targets = [w for w in board.words_with_role("target") if w not in (revealed or {})]
        return {"clue": "c", "count": 1, "intended_targets": targets[:1], "reasoning": ""}


class _Guesser:
    def guess_one(self, words, clue, count, correct_so_far, revealed=None, stats=None):
        if stats is not None:
            stats["guesser_attempts"] += 1
        return words[0] if words else None


def _config(**overrides):
    base = dict(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_models=["model-a", "model-b"],
        board_styles=["dual_50"],
        n_boards=2,
        n_trials=1,
    )
    base.update(overrides)
    return ExperimentConfig(**base)


def _run(results_dir, resume_from=None, **kwargs):
    return run_experiment(
        config=_config(**kwargs),
        word_lists=_word_lists(),
        make_codemaster=lambda model, method: _Codemaster(),
        make_guesser=lambda model: _Guesser(),
        results_dir=results_dir,
        trial_delay=0,
        resume_from=resume_from,
    )


def _rows(run_dir: Path) -> list:
    return [
        json.loads(line)
        for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]


def _key(row) -> tuple:
    return (
        row["model"], row["guesser_model"], row["method"],
        row["board_style"], row["board_seed"], row["trial"],
    )


def _truncate(run_dir: Path, keep: int) -> list:
    """Simulate a run killed after `keep` games."""
    rows = _rows(run_dir)[:keep]
    (run_dir / "raw.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    (run_dir / "metrics.csv").unlink(missing_ok=True)
    return rows


def test_resume_replays_only_the_games_that_are_missing(tmp_path):
    run_dir = _run(tmp_path)
    kept = _truncate(run_dir, 3)

    _run(tmp_path, resume_from=run_dir)

    rows = _rows(run_dir)
    assert len(rows) == 8  # 2 codemasters x 2 guessers x 2 boards
    assert [_key(r) for r in rows[:3]] == [_key(r) for r in kept]


def test_resume_leaves_every_game_recorded_exactly_once(tmp_path):
    run_dir = _run(tmp_path)
    _truncate(run_dir, 5)

    _run(tmp_path, resume_from=run_dir)

    keys = [_key(r) for r in _rows(run_dir)]
    assert len(keys) == len(set(keys))


def test_resume_writes_metrics_for_the_whole_run_not_just_the_tail(tmp_path):
    import csv

    run_dir = _run(tmp_path)
    _truncate(run_dir, 3)

    _run(tmp_path, resume_from=run_dir)

    with (run_dir / "metrics.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 8


def test_resume_into_a_finished_run_plays_nothing(tmp_path):
    run_dir = _run(tmp_path)
    before = _rows(run_dir)

    _run(tmp_path, resume_from=run_dir)

    assert [_key(r) for r in _rows(run_dir)] == [_key(r) for r in before]


def test_resume_refuses_a_config_that_does_not_match_the_run(tmp_path):
    """The half-finished games were played against a specific design. Resuming
    with a different one would silently mix two experiments into one file."""
    run_dir = _run(tmp_path)
    _truncate(run_dir, 3)

    with pytest.raises(ValueError) as excinfo:
        _run(tmp_path, resume_from=run_dir, n_boards=5)

    assert "resume" in str(excinfo.value).lower()


def test_resume_refuses_a_changed_board_seed_offset(tmp_path):
    # A different offset means different boards entirely, so the games on disk
    # do not belong to the grid the new config describes.
    config = _config(board_seed_offset=0)
    run_dir = run_experiment(
        config, _word_lists(), lambda m, meth: _Codemaster(), lambda m: _Guesser(),
        tmp_path, trial_delay=0,
    )

    with pytest.raises(ValueError, match="different design"):
        run_experiment(
            _config(board_seed_offset=10), _word_lists(),
            lambda m, meth: _Codemaster(), lambda m: _Guesser(),
            tmp_path, trial_delay=0, resume_from=run_dir,
        )
