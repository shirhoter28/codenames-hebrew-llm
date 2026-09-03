"""Codenames board construction.

Ported from the Colab setup (choose 25 words, assign 9/8/7/1 roles, 5x5 layout).

Methodological choice vs the notebook
-------------------------------------
The notebook could use three separate seeds (word draw, roles, layout) and
called ``random.seed`` on the global RNG. Here one integer ``seed`` controls
the whole board, using an isolated ``random.Random`` instance:

1. Sample 25 words without replacement from the named wordpool.
2. Shuffle a role list of 9 Red, 8 Blue, 7 Civilian, 1 Assassin.
3. Pair roles with words by index. The 5x5 grid is that list in row-major order.

Same seed + same wordpool ⇒ identical board. This matches the Stephenson et al.
framework (one seed per game) and our experiment logging.

Default wordpool is ``regular``. Use ``dual`` or ``union`` later for
double-meaning / mixed boards; that is an experimental condition, not a
silent default.

Embedding games may pass a pre-filtered ``pool`` and a distinct ``wordpool``
label (e.g. ``regular_in_vocab_word2vec``). That does not edit the CSV files.
Same seed + same pool contents and order ⇒ identical board. Same seed + full
``regular`` is a different experiment from a per-model in-vocab subset, and
both of those differ from a two-model **intersection** pool.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORDPOOL_DIR = REPO_ROOT / "data" / "wordpools"

RED_COUNT = 9
BLUE_COUNT = 8
CIVILIAN_COUNT = 7
ASSASSIN_COUNT = 1
BOARD_SIZE = 25
GRID_DIM = 5

ROLE_RED = "Red"
ROLE_BLUE = "Blue"
ROLE_CIVILIAN = "Civilian"
ROLE_ASSASSIN = "Assassin"

WORDPOOLS = ("regular", "dual", "union")


def _read_words_csv(path: Path) -> list[str]:
    """Read the ``מילה`` column, keep Hebrew text exactly, drop empties and later duplicates."""
    if not path.exists():
        raise FileNotFoundError(f"Wordpool file not found: {path}")

    words: list[str] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "מילה" not in reader.fieldnames:
            raise ValueError(f"Expected a מילה column in {path}, found {reader.fieldnames}")
        for row in reader:
            word = (row.get("מילה") or "").strip()
            if not word or word in seen:
                continue
            seen.add(word)
            words.append(word)
    return words


def load_wordpool(name: str = "regular") -> list[str]:
    """Load a local snapshot of the Hebrew word list.

    ``regular`` / ``dual`` are split by the second-column tag in the
    spreadsheet exports (``r``/``s`` vs ``d``), not by which tab a word
    sat on. ``union`` is regular first, then dual words not already present
    (the two lists are disjoint after the tag split).
    """
    if name not in WORDPOOLS:
        raise ValueError(f"Unknown wordpool {name!r}; expected one of {WORDPOOLS}")

    if name == "union":
        regular = _read_words_csv(WORDPOOL_DIR / "regular.csv")
        dual = _read_words_csv(WORDPOOL_DIR / "dual.csv")
        seen = set(regular)
        return regular + [w for w in dual if w not in seen]

    return _read_words_csv(WORDPOOL_DIR / f"{name}.csv")


@dataclass(frozen=True)
class Board:
    """One 25-card Codenames board."""

    seed: int
    wordpool: str
    words: tuple[str, ...]
    key_grid: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.words) != BOARD_SIZE or len(self.key_grid) != BOARD_SIZE:
            raise ValueError("Board must have 25 words and 25 roles")
        if len(set(self.words)) != BOARD_SIZE:
            raise ValueError("Board words must be unique")

    @property
    def grid(self) -> list[list[str]]:
        return [
            list(self.words[r * GRID_DIM : (r + 1) * GRID_DIM])
            for r in range(GRID_DIM)
        ]

    @property
    def role_grid(self) -> list[list[str]]:
        return [
            list(self.key_grid[r * GRID_DIM : (r + 1) * GRID_DIM])
            for r in range(GRID_DIM)
        ]

    def words_for_role(self, role: str) -> list[str]:
        return [w for w, r in zip(self.words, self.key_grid) if r == role]

    @property
    def red(self) -> list[str]:
        return self.words_for_role(ROLE_RED)

    @property
    def blue(self) -> list[str]:
        return self.words_for_role(ROLE_BLUE)

    @property
    def civilian(self) -> list[str]:
        return self.words_for_role(ROLE_CIVILIAN)

    @property
    def assassin(self) -> str:
        words = self.words_for_role(ROLE_ASSASSIN)
        if len(words) != 1:
            raise ValueError(f"Expected 1 assassin, found {len(words)}")
        return words[0]

    def role_of(self, word: str) -> str:
        try:
            return self.key_grid[self.words.index(word)]
        except ValueError as exc:
            raise KeyError(word) from exc

    def format_codemaster_view(self) -> str:
        """5x5 words with roles, for inspection (Codemaster sees colors)."""
        lines = [f"seed={self.seed}  wordpool={self.wordpool}"]
        for row_words, row_roles in zip(self.grid, self.role_grid):
            cells = [f"{word} ({role})" for word, role in zip(row_words, row_roles)]
            lines.append(" | ".join(cells))
        lines.append(
            f"Red ({len(self.red)}): {self.red}\n"
            f"Blue ({len(self.blue)}): {self.blue}\n"
            f"Civilian ({len(self.civilian)}): {self.civilian}\n"
            f"Assassin: {self.assassin}"
        )
        return "\n".join(lines)

    def format_guesser_view(self) -> str:
        lines = [f"seed={self.seed}  wordpool={self.wordpool}"]
        for row_words in self.grid:
            lines.append(" | ".join(row_words))
        return "\n".join(lines)


def create_board(
    seed: int,
    wordpool: str = "regular",
    pool: list[str] | None = None,
) -> Board:
    """Build a reproducible 25-card board.

    If ``pool`` is omitted, words are loaded with ``load_wordpool(wordpool)``.
    If ``pool`` is given, those words are sampled and ``wordpool`` is only the
    label stored on the board (for embedding in-vocab conditions).
    """
    source = list(pool) if pool is not None else load_wordpool(wordpool)
    if len(source) < BOARD_SIZE:
        raise ValueError(
            f"Wordpool {wordpool!r} has {len(source)} words; need at least {BOARD_SIZE}"
        )
    if len(set(source)) != len(source):
        raise ValueError(f"Wordpool {wordpool!r} has duplicate words")

    rng = random.Random(seed)
    words = tuple(rng.sample(source, BOARD_SIZE))
    key_grid = (
        [ROLE_RED] * RED_COUNT
        + [ROLE_BLUE] * BLUE_COUNT
        + [ROLE_CIVILIAN] * CIVILIAN_COUNT
        + [ROLE_ASSASSIN] * ASSASSIN_COUNT
    )
    rng.shuffle(key_grid)
    return Board(seed=seed, wordpool=wordpool, words=words, key_grid=tuple(key_grid))
