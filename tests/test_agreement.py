import pytest

from codenames_heb.agreement import normalize_clue


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
