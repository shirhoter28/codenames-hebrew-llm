from pathlib import Path

from codenames_heb.words import load_word_lists


def _write_csv(path: Path, header: str, words: list[str]) -> None:
    path.write_text("\n".join([header, *words]) + "\n", encoding="utf-8")


def test_load_word_lists_reads_regular_and_dual(tmp_path):
    _write_csv(tmp_path / "condenames_heb_regular.csv", "מילה", ["כלב", "חתול", "עץ"])
    _write_csv(tmp_path / "condenames_heb_dual.csv", "מילה", ["בול", "עין"])

    result = load_word_lists(tmp_path)

    assert result.regular == ["כלב", "חתול", "עץ"]
    assert result.dual == ["בול", "עין"]


def test_all_combines_regular_and_dual_and_dedupes(tmp_path):
    _write_csv(tmp_path / "condenames_heb_regular.csv", "מילה", ["כלב", "חתול"])
    _write_csv(tmp_path / "condenames_heb_dual.csv", "מילה", ["חתול", "עין"])

    result = load_word_lists(tmp_path)

    assert result.all == ["כלב", "חתול", "עין"]


def test_load_word_lists_defaults_to_data_raw_dir():
    result = load_word_lists()

    assert len(result.regular) > 0
    assert len(result.dual) > 0
    assert len(result.all) >= 25
