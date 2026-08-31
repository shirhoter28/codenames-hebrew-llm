"""The curated-example renderer behind `docs/examples/full_games.md`.

The manifest is the editable part — the point of the script is that adding an
example is a manifest entry, not a code change. So the contract is: every entry
is rendered under its own heading, a game named by several entries is still only
transcribed once, and an entry that names no real game fails loudly rather than
producing a doc with a silent hole in it.
"""

import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        f"{name}_script", PROJECT_ROOT / "scripts" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


script = _load("render_examples")

WORDS = [f"w{i}" for i in range(25)]
ROLES = {w: "civilian" for w in WORDS}
ROLES.update({w: "target" for w in WORDS[:9]})
ROLES.update({w: "opponent" for w in WORDS[9:17]})
ROLES[WORDS[24]] = "assassin"


def _game(**over):
    game = {
        "model": "vendor/alpha",
        "guesser_model": "vendor/beta",
        "method": "strong_hebrew",
        "board_seed": 3,
        "board_style": "natural",
        "trial": 0,
        "count_constraint": "min2",
        "outcome": "win",
        "loss_reason": None,
        "game_length": 1,
        "rounds": [{
            "round": 1, "clue": "klue", "count": 2,
            "intended_targets": [WORDS[0], WORDS[1]],
            "guess_sequence": [{"word": WORDS[0], "role": "target"}],
            "turn_outcome": "stopped_early",
        }],
    }
    game.update(over)
    return game


def _entry(**over):
    entry = {
        "section": "Sec", "title": "First point", "note": "why this game matters",
        "run": "20260101T000000000000Z", "cm": "vendor/alpha", "guesser": "vendor/beta",
        "method": "strong_hebrew", "style": "natural", "seed": 3, "cc": "min2",
        "round": 1,
    }
    entry.update(over)
    return entry


@pytest.fixture
def workspace(tmp_path):
    run = tmp_path / "20260101T000000000000Z"
    run.mkdir()
    (run / "boards.json").write_text(
        json.dumps([{"seed": 3, "style": "natural", "words": WORDS, "roles": ROLES}])
    )
    (run / "raw.jsonl").write_text(json.dumps(_game()) + "\n")
    return run, tmp_path / "manifest.json", tmp_path / "out.md"


def _render(workspace, entries):
    run, manifest, out = workspace
    manifest.write_text(json.dumps(entries, ensure_ascii=False))
    code = script.main([str(run), "--manifest", str(manifest), "--out", str(out)])
    return code, out.read_text()


def test_every_entry_gets_its_own_heading(workspace):
    code, text = _render(workspace, [_entry(), _entry(title="Second point")])
    assert code == 0
    assert "## First point" in text and "## Second point" in text


def test_one_game_named_twice_is_transcribed_once(workspace):
    _, text = _render(workspace, [_entry(), _entry(title="Second point")])
    assert text.count("YOUR WORDS (9)") == 1
    assert "Same game as above" in text


def test_a_missing_game_is_reported_not_silently_skipped(workspace):
    code, text = _render(workspace, [_entry(seed=999)])
    assert code == 1
    assert "Game not found" in text


def test_reproduction_command_names_the_run_and_board(workspace):
    _, text = _render(workspace, [_entry()])
    assert "scripts/show_game.py results/20260101T000000000000Z" in text
    assert "--style natural --seed 3" in text
    assert "--cc min2" in text


def test_free_choice_games_omit_the_count_flag(workspace):
    _, text = _render(workspace, [_entry(cc="None")])
    assert "--cc" not in text


def test_contents_lists_each_section_with_its_size(workspace):
    _, text = _render(workspace, [_entry(), _entry(title="b"), _entry(section="Other", title="c")])
    assert "- **Sec** — 2 examples" in text
    assert "- **Other** — 1 examples" in text


def test_shipped_manifest_is_well_formed():
    entries = json.loads((PROJECT_ROOT / "docs/examples/manifest.json").read_text())
    assert entries
    required = {"section", "title", "note", "run", "cm", "guesser", "method", "style", "seed", "cc"}
    for entry in entries:
        assert required <= entry.keys(), entry
