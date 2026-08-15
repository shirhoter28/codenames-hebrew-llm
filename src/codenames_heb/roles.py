from typing import Protocol, runtime_checkable

from codenames_heb.board import Board


@runtime_checkable
class Codemaster(Protocol):
    def give_clue(
        self,
        board: Board,
        required_count: int | None = None,
        revealed: dict[str, str] | None = None,
    ) -> dict:
        """Return {"clue": str, "count": int, "intended_targets": list[str], "reasoning": str, ...}."""
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
    ) -> str | None:
        """Return the next word to guess, or None to voluntarily stop the round."""
        ...
