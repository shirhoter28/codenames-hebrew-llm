import pytest
import pandas as pd

from codenames_heb.agreement import CELL_KEY, PANEL_KEY, first_rounds, normalize_clue


def test_normalize_strips_niqqud():
    # Vocalization is optional in the source and appears inconsistently, so two
    # spellings of one word must not read as disagreement.
    assert normalize_clue("בַּיִת") == normalize_clue("בית")


def test_normalize_folds_final_letters():
    # Final forms are positional variants of the same letter.
    assert normalize_clue("ארץ") == normalize_clue("ארצ")


def test_normalize_keeps_genuinely_different_words_apart():
    # The definite article changes meaning; folding it would overstate agreement.
    assert normalize_clue("ים") != normalize_clue("הים")
    assert normalize_clue("כלב") != normalize_clue("לב")


def test_normalize_handles_a_missing_clue():
    assert normalize_clue(None) == ""


def _round(model, guesser, clue, targets, rnd=1, style="natural", seed=0):
    return {
        "board_style": style, "board_seed": seed, "model": model,
        "guesser_model": guesser, "method": "strong_hebrew",
        "count_constraint": "free", "round": rnd,
        "clue": clue, "intended_targets": targets,
        "count": len(targets), "n_correct": 1,
        "stop_class": "stopped_at_quota", "first_miss_role": None,
    }


@pytest.fixture
def cell_rounds():
    """One cell: model alpha, 4 guessers, all giving the same clue.

    Plus a round-2 row that must never be counted, and a second codemaster.
    """
    rows = [_round("v/alpha", f"g{i}", "בית", ["א", "ב"]) for i in range(4)]
    rows.append(_round("v/alpha", "g0", "אחר", ["ג"], rnd=2))
    rows += [_round("v/beta", f"g{i}", f"קלו{i}", ["א"]) for i in range(4)]
    return pd.DataFrame(rows)


def test_first_rounds_keeps_only_round_one(cell_rounds):
    out = first_rounds(cell_rounds)

    assert set(out["round"]) == {1}
    assert len(out) == 8


def test_first_rounds_attaches_normalized_clue_and_target_set(cell_rounds):
    out = first_rounds(cell_rounds)
    alpha = out[out["model"] == "v/alpha"]

    assert set(alpha["clue_norm"]) == {"בית"}
    assert set(alpha["target_set"]) == {frozenset({"א", "ב"})}


def test_keys_name_the_two_units():
    # A cell is one model's replicates; a panel pools the codemasters on one
    # board, holding method and floor fixed so it stays a model contrast.
    assert CELL_KEY == ["board_style", "board_seed", "model", "method", "count_constraint"]
    assert PANEL_KEY == ["board_style", "board_seed", "method", "count_constraint"]
