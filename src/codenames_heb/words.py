import csv
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


def load_word_lists(data_dir: Path = DEFAULT_DATA_DIR) -> WordLists:
    data_dir = Path(data_dir)
    regular = _read_word_column(data_dir / "condenames_heb_regular.csv")
    dual = _read_word_column(data_dir / "condenames_heb_dual.csv")
    return WordLists(regular=regular, dual=dual)
