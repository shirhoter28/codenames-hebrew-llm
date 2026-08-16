from pathlib import Path

import pytest

from codenames_heb.words import WordLists, load_word_lists


def _write_csv(path: Path, header: str, words: list[str]) -> None:
    path.write_text("\n".join([header, *words]) + "\n", encoding="utf-8")


def _write_pair(tmp_path: Path, regular: list[str], dual: list[str]) -> None:
    _write_csv(tmp_path / "condenames_heb_regular.csv", "מילה", regular)
    _write_csv(tmp_path / "condenames_heb_dual.csv", "מילה", dual)


def test_load_word_lists_reads_regular_and_dual(tmp_path):
    _write_pair(tmp_path, ["כלב", "חתול", "עץ"], ["בול", "עין"])

    result = load_word_lists(tmp_path)

    assert result.regular == ["כלב", "חתול", "עץ"]
    assert result.dual == ["בול", "עין"]


def test_all_combines_regular_and_dual_and_dedupes():
    # Exercised on the data model directly: load_word_lists now rejects the
    # overlap that would make dedup observable through it.
    result = WordLists(regular=["כלב", "חתול"], dual=["חתול", "עין"])

    assert result.all == ["כלב", "חתול", "עין"]


def test_load_word_lists_rejects_words_in_both_lists(tmp_path):
    _write_pair(tmp_path, ["כלב", "עין"], ["בול", "עין"])

    with pytest.raises(ValueError, match="עין"):
        load_word_lists(tmp_path)


@pytest.mark.parametrize("list_name", ["regular", "dual"])
def test_load_word_lists_rejects_duplicates_within_a_list(tmp_path, list_name):
    words = {"regular": ["כלב", "חתול"], "dual": ["בול", "עין"]}
    words[list_name] = words[list_name] + [words[list_name][0]]
    _write_pair(tmp_path, words["regular"], words["dual"])

    with pytest.raises(ValueError, match=f"{list_name} word list has duplicate"):
        load_word_lists(tmp_path)


def test_load_word_lists_defaults_to_data_raw_dir():
    result = load_word_lists()

    assert len(result.regular) > 0
    assert len(result.dual) > 0
    assert len(result.all) >= 25


def test_shipped_word_lists_are_disjoint_and_large_enough_for_every_style():
    # The regular/dual split is the experiment's independent variable, so the
    # shipped data has to satisfy it, not just the loader's synthetic fixtures.
    result = load_word_lists()

    assert not set(result.regular) & set(result.dual)
    assert len(result.regular) >= 25
    assert len(result.dual) >= 25
