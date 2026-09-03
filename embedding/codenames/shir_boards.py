"""Fixed boards from Shir's JSON (not sampled from our wordpools).

OOV is vs the Word2Vec ∩ fastText intersection (exact string), so all six
methods see the same unreadable cards. Policy (shir_v1):

- Any OOV **red** → do not play; outcome ``oov_loss``.
- OOV **assassin** (and no OOV red) → play; assassin cannot be looked up
  (unfair: it cannot be hit and does not enter ``max_bad``).
- OOV **blue** (and/or civilian) → play; those cards are skipped in cosine
  and cannot be guessed. Logged, not a forced outcome.

Official intersection sampling is unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from codenames.board import (
    BOARD_SIZE,
    REPO_ROOT,
    ROLE_ASSASSIN,
    ROLE_BLUE,
    ROLE_CIVILIAN,
    ROLE_RED,
    Board,
)
from codenames.embeddings import EmbeddingModel

DEFAULT_BOARDS_PATH = REPO_ROOT / "data" / "boards" / "shirs_boards.json"
SHIR_STYLES = ("dual_0", "natural", "dual_100")
SHIR_ROLE_MAP = {
    "target": ROLE_RED,
    "opponent": ROLE_BLUE,
    "civilian": ROLE_CIVILIAN,
    "assassin": ROLE_ASSASSIN,
}
OUTCOME_OOV_LOSS = "oov_loss"
OOV_POLICY = "shir_v1"


@dataclass(frozen=True)
class ShirOovInfo:
    words: tuple[str, ...]
    by_role: dict[str, tuple[str, ...]]
    red_loss: bool
    assassin_unfair: bool
    oov_blue: bool
    oov_civilian: bool

    def as_log_dict(self) -> dict:
        return {
            "oov_policy": OOV_POLICY,
            "oov_words": list(self.words),
            "oov_by_role": {role: list(words) for role, words in self.by_role.items()},
            "oov_red_loss": self.red_loss,
            "assassin_oov_unfair": self.assassin_unfair,
            "oov_blue": self.oov_blue,
            "oov_civilian": self.oov_civilian,
        }


def shir_wordpool_label(style: str) -> str:
    return f"shir_{style}"


def load_shir_records(path: Path | None = None) -> list[dict]:
    source = path or DEFAULT_BOARDS_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list of boards in {source}")
    return payload


def board_from_record(record: dict) -> Board:
    style = record["style"]
    words = tuple(record["words"])
    roles = record["roles"]
    if len(words) != BOARD_SIZE:
        raise ValueError(f"Shir board seed={record.get('seed')} has {len(words)} words")
    key_grid = tuple(SHIR_ROLE_MAP[roles[word]] for word in words)
    return Board(
        seed=int(record["seed"]),
        wordpool=shir_wordpool_label(style),
        words=words,
        key_grid=key_grid,
    )


def load_shir_boards(
    path: Path | None = None,
    *,
    style: str | None = None,
) -> list[Board]:
    boards = [board_from_record(record) for record in load_shir_records(path)]
    if style is not None:
        label = shir_wordpool_label(style)
        boards = [board for board in boards if board.wordpool == label]
    return boards


def intersection_oov_words(
    words: list[str],
    *models: EmbeddingModel,
) -> list[str]:
    """Words missing from at least one table, in board order."""
    missing: list[str] = []
    seen: set[str] = set()
    for word in words:
        if word in seen:
            continue
        if any(not model.contains(word) for model in models):
            missing.append(word)
            seen.add(word)
    return missing


def classify_oov(board: Board, oov_words: list[str]) -> ShirOovInfo:
    by_role = {
        ROLE_RED: [],
        ROLE_BLUE: [],
        ROLE_CIVILIAN: [],
        ROLE_ASSASSIN: [],
    }
    for word in oov_words:
        by_role[board.role_of(word)].append(word)
    red_loss = bool(by_role[ROLE_RED])
    return ShirOovInfo(
        words=tuple(oov_words),
        by_role={role: tuple(words) for role, words in by_role.items()},
        red_loss=red_loss,
        assassin_unfair=bool(by_role[ROLE_ASSASSIN]) and not red_loss,
        oov_blue=bool(by_role[ROLE_BLUE]),
        oov_civilian=bool(by_role[ROLE_CIVILIAN]),
    )
