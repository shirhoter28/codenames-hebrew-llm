"""Player interfaces and dummy agents.

Dummy players exist so the game loop can be tested with no embedding table.
They are not an experimental condition.

OracleGuesser knows card colors and always picks remaining Red. Use it only
to verify the win path of the engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codenames.board import ROLE_RED


class Codemaster(ABC):
    name: str

    @abstractmethod
    def set_game_state(self, remaining_by_role: dict[str, list[str]]) -> None:
        pass

    @abstractmethod
    def get_clue(self) -> tuple[str, int]:
        """Return (clue_word, intended_target_count)."""

    def notify_invalid(self, reason: str) -> None:
        """Called when a clue fails validity. Dummy agents ignore this."""
        return


class Guesser(ABC):
    name: str

    @abstractmethod
    def set_board(self, remaining_words: list[str]) -> None:
        pass

    @abstractmethod
    def set_clue(self, clue: str, num: int) -> None:
        pass

    @abstractmethod
    def keep_guessing(self) -> bool:
        """Called after a correct Red guess. True = guess again this turn."""

    @abstractmethod
    def get_answer(self) -> str:
        pass


class ScriptedCodemaster(Codemaster):
    """Returns clues from a queue. For engine/validity tests only."""

    name = "scripted"

    def __init__(self, clues: list[tuple[str, int]]) -> None:
        if not clues:
            raise ValueError("ScriptedCodemaster needs at least one clue")
        self.clues = list(clues)
        self.index = 0
        self.invalid_reasons: list[str] = []

    def set_game_state(self, remaining_by_role: dict[str, list[str]]) -> None:
        return

    def get_clue(self) -> tuple[str, int]:
        clue = self.clues[min(self.index, len(self.clues) - 1)]
        self.index += 1
        return clue

    def notify_invalid(self, reason: str) -> None:
        self.invalid_reasons.append(reason)


class DummyCodemaster(Codemaster):
    """Always returns a fixed legal-looking clue. Ignores the board."""

    name = "dummy"

    def __init__(self, clue: str = "בדיקה", number: int = 1) -> None:
        self.clue = clue
        self.number = number
        self.remaining_by_role: dict[str, list[str]] = {}

    def set_game_state(self, remaining_by_role: dict[str, list[str]]) -> None:
        self.remaining_by_role = remaining_by_role

    def get_clue(self) -> tuple[str, int]:
        return self.clue, self.number


class DummyGuesser(Guesser):
    """Picks the first remaining word in board order. Stops after ``num`` correct guesses."""

    name = "dummy"

    def __init__(self) -> None:
        self.remaining: list[str] = []
        self.clue = ""
        self.num = 1
        self.guesses_this_turn = 0

    def set_board(self, remaining_words: list[str]) -> None:
        self.remaining = list(remaining_words)

    def set_clue(self, clue: str, num: int) -> None:
        self.clue = clue
        self.num = num
        self.guesses_this_turn = 0

    def keep_guessing(self) -> bool:
        if self.num == 0:
            return bool(self.remaining)
        return self.guesses_this_turn < self.num

    def get_answer(self) -> str:
        if not self.remaining:
            raise RuntimeError("DummyGuesser has no remaining words")
        self.guesses_this_turn += 1
        return self.remaining[0]


class OracleGuesser(Guesser):
    """Cheating guesser: always selects a remaining Red word. Engine tests only."""

    name = "oracle"

    def __init__(self, role_of) -> None:
        self._role_of = role_of
        self.remaining: list[str] = []
        self.num = 1
        self.guesses_this_turn = 0

    def set_board(self, remaining_words: list[str]) -> None:
        self.remaining = list(remaining_words)

    def set_clue(self, clue: str, num: int) -> None:
        self.num = num
        self.guesses_this_turn = 0

    def keep_guessing(self) -> bool:
        if self.num == 0:
            return any(self._role_of(w) == ROLE_RED for w in self.remaining)
        return self.guesses_this_turn < self.num

    def get_answer(self) -> str:
        for word in self.remaining:
            if self._role_of(word) == ROLE_RED:
                self.guesses_this_turn += 1
                return word
        raise RuntimeError("OracleGuesser found no remaining Red words")


class AssassinGuesser(Guesser):
    """Always picks the assassin if it is still on the board. Engine tests only."""

    name = "assassin"

    def __init__(self, assassin_word: str) -> None:
        self.assassin_word = assassin_word
        self.remaining: list[str] = []

    def set_board(self, remaining_words: list[str]) -> None:
        self.remaining = list(remaining_words)

    def set_clue(self, clue: str, num: int) -> None:
        return

    def keep_guessing(self) -> bool:
        return False

    def get_answer(self) -> str:
        if self.assassin_word in self.remaining:
            return self.assassin_word
        return self.remaining[0]
