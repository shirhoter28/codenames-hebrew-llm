from typing import Protocol, runtime_checkable

from codenames_heb.board import Board


@runtime_checkable
class Codemaster(Protocol):
    def give_clue(self, board: Board, required_count: int | None = None) -> dict:
        """Return {"clue": str, "count": int, "intended_targets": list[str], "reasoning": str, ...}."""
        ...


@runtime_checkable
class Guesser(Protocol):
    def guess(self, words: list[str], clue: str, count: int) -> list[str]:
        """Return an ordered list of guessed words, most confident first."""
        ...
