import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


@dataclass(frozen=True)
class WordLists:
    regular: list[str]
    dual: list[str]

    @property
    def all(self) -> list[str]:
        return list(dict.fromkeys(self.regular + self.dual))


def _read_word_column(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]
    if rows and rows[0] == "מילה":
        rows = rows[1:]
    return rows


def _validate_pools(regular: list[str], dual: list[str]) -> None:
    """The regular/dual split is the experiment's independent variable.

    A word in both lists silently contaminates the dual_0 control board (it would
    be "unambiguous" by construction yet also flagged ambiguous), and a word listed
    twice in one file is drawn twice as often as its neighbours. Both are
    measurement errors, not cosmetic — fail at load rather than at analysis time.
    """
    for name, words in (("regular", regular), ("dual", dual)):
        duplicates = sorted(w for w, count in Counter(words).items() if count > 1)
        if duplicates:
            raise ValueError(f"{name} word list has duplicate entries: {duplicates}")

    overlap = sorted(set(regular) & set(dual))
    if overlap:
        raise ValueError(
            f"words appear in both the regular and dual lists: {overlap}; "
            f"each word must belong to exactly one list"
        )


def load_word_lists(data_dir: Path = DEFAULT_DATA_DIR) -> WordLists:
    data_dir = Path(data_dir)
    regular = _read_word_column(data_dir / "condenames_heb_regular.csv")
    dual = _read_word_column(data_dir / "condenames_heb_dual.csv")
    _validate_pools(regular, dual)
    return WordLists(regular=regular, dual=dual)
