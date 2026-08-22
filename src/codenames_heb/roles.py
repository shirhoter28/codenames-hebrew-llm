from collections import Counter
from typing import Protocol, runtime_checkable

from codenames_heb.board import Board


@runtime_checkable
class Codemaster(Protocol):
    def give_clue(
        self,
        board: Board,
        required_count: int | None = None,
        revealed: dict[str, str] | None = None,
        stats: Counter | None = None,
    ) -> dict:
        """Return {"clue": str, "count": int, "intended_targets": list[str], ...}.

        `stats`, when given, is incremented with per-attempt compliance counts.
        """
        ...


@runtime_checkable
class Guesser(Protocol):
    def guess_one(
        self,
        words: list[str],
        clue: str,
        count: int,
        correct_so_far: list[str],
        revealed: dict[str, str] | None = None,
        stats: Counter | None = None,
    ) -> str | None:
        """Return the next word to guess, or None to voluntarily stop the round.

        `stats`, when given, is incremented with per-attempt compliance counts.
        """
        ...
