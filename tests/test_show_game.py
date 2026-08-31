"""The single-game viewer that the qualitative write-up in `docs/examples/` is
built from.

A game transcript is only useful for error analysis if it is complete and
faithful: every round in order, the board roles the guesses are scored against,
and — for translate games — the per-round gloss, which is the whole point of
looking at one of those games by hand.
"""

import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "show_game_script", PROJECT_ROOT / "scripts" / "show_game.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


script = _load_script()

WORDS = [f"w{i}" for i in range(25)]
ROLES = {w: "civilian" for w in WORDS}
ROLES.update({w: "target" for w in WORDS[:9]})
ROLES.update({w: "opponent" for w in WORDS[9:17]})
ROLES[WORDS[24]] = "assassin"

GAME = {
    "model": "vendor/alpha",
    "guesser_model": "vendor/beta",
    "method": "translate_pipeline",
    "board_seed": 7,
    "board_style": "dual_100",
    "trial": 0,
    "count_constraint": "min2",
    "outcome": "loss",
    "loss_reason": "assassin",
    "game_length": 2,
    "rounds": [
        {
            "round": 1,
            "clue": "clue-one",
            "count": 2,
            "intended_targets": [WORDS[0], WORDS[1]],
            "en_clue": "first",
            "en_targets": ["alpha", "beta"],
            "translation_map": {WORDS[0]: "alpha", WORDS[1]: "beta"},
            "guess_sequence": [{"word": WORDS[0], "role": "target"}],
            "turn_outcome": "stopped_early",
        },
        {
            "round": 2,
            "clue": "clue-two",
            "count": 2,
            "intended_targets": [WORDS[2]],
            "en_clue": "second",
            "en_targets": ["gamma"],
            # w0 is glossed differently than in round 1 — the drift the doc is about.
            "translation_map": {WORDS[0]: "ALPHA-PRIME", WORDS[2]: "gamma"},
            "guess_sequence": [{"word": WORDS[24], "role": "assassin"}],
            "turn_outcome": "hit_assassin",
        },
    ],
}


@pytest.fixture
def run_dir(tmp_path):
    d = tmp_path / "20260101T000000000000Z"
    d.mkdir()
    (d / "boards.json").write_text(
        json.dumps([{"seed": 7, "style": "dual_100", "words": WORDS, "roles": ROLES}])
    )
    (d / "raw.jsonl").write_text(json.dumps(GAME) + "\n")
    return d


def _run(run_dir, capsys, *argv):
    assert script.main([str(run_dir), *argv]) == 0
    return capsys.readouterr().out


def test_prints_every_round_in_order(run_dir, capsys):
    out = _run(run_dir, capsys)
    assert out.index("round 1") < out.index("round 2")
    assert "clue-one" in out and "clue-two" in out


def test_board_roles_are_shown_so_guesses_can_be_scored(run_dir, capsys):
    out = _run(run_dir, capsys)
    assert "YOUR WORDS (9)" in out
    assert "ASSASSIN (1)" in out
    assert WORDS[24] in out


def test_translate_games_show_the_per_round_gloss(run_dir, capsys):
    out = _run(run_dir, capsys)
    assert "w0=alpha" in out
    assert "w0=ALPHA-PRIME" in out


def test_markdown_mode_surfaces_words_glossed_more_than_one_way(run_dir, capsys):
    out = _run(run_dir, capsys, "--md")
    assert "glossed more than one way" in out
    assert "**w0**" in out
    # w2 was glossed once only, so it is not drift and must not be listed.
    assert "**w2**" not in out


def test_filters_are_substring_matches(run_dir, capsys):
    assert "clue-one" in _run(run_dir, capsys, "--cm", "alpha", "--method", "translate")
    assert script.main([str(run_dir), "--cm", "nosuchmodel"]) == 1


def test_list_mode_prints_one_line_per_game(run_dir, capsys):
    out = _run(run_dir, capsys, "--list")
    assert len(out.strip().splitlines()) == 1
    assert "dual_100" in out and "loss" in out
