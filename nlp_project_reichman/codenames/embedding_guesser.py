"""Embedding guesser (Kim et al. 2019 style).

Ranks remaining board words by cosine similarity to the clue and picks the
highest. Official games do not skip out-of-vocabulary words. Shir boards may
pass ``skip_board_words`` so unreadable cards are never guessed.

This implements ``Guesser`` so it can later plug into ``SingleTeamGame``.
It is not wired into a game runner yet.
"""

from __future__ import annotations

from codenames.embeddings import EmbeddingModel, OutOfVocabularyError
from codenames.players import Guesser


def rank_by_similarity(
    model: EmbeddingModel,
    clue: str,
    remaining_words: list[str],
    skip_board_words: list[str] | None = None,
) -> list[tuple[str, float]]:
    """Return remaining words sorted by cosine similarity to ``clue`` (highest first).

    Raises ``OutOfVocabularyError`` listing every missing word (clue and/or board).
    ``skip_board_words`` (Shir boards only) are left out of the ranking.
    Tie-break is original remaining-word order (stable sort).
    """
    skip = set(skip_board_words or ())
    ranked_words = [word for word in remaining_words if word not in skip]
    missing = [clue] if not model.contains(clue) else []
    missing.extend(word for word in ranked_words if not model.contains(word))
    if missing:
        raise OutOfVocabularyError(*missing)
    if not ranked_words:
        raise RuntimeError("No in-vocab remaining words to guess")

    scored = [(word, model.similarity(clue, word)) for word in ranked_words]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


class EmbeddingGuesser(Guesser):
    """Pick the remaining board word most similar to the clue."""

    name = "embedding"

    def __init__(
        self,
        model: EmbeddingModel,
        skip_board_words: list[str] | None = None,
    ) -> None:
        self.model = model
        self.skip_board_words = list(skip_board_words or [])
        self.remaining: list[str] = []
        self.clue = ""
        self.num = 1
        self.guesses_this_turn = 0
        self.last_ranking: list[tuple[str, float]] = []

    def set_board(self, remaining_words: list[str]) -> None:
        self.remaining = list(remaining_words)

    def set_clue(self, clue: str, num: int) -> None:
        self.clue = clue
        self.num = num
        self.guesses_this_turn = 0
        self.last_ranking = []

    def keep_guessing(self) -> bool:
        """Continue after a correct red guess, up to the clue number (no extra guess)."""
        return self.guesses_this_turn < self.num

    def rank(self, clue: str, remaining_words: list[str]) -> list[tuple[str, float]]:
        """Debug helper: full similarity ranking without consuming a guess."""
        self.last_ranking = rank_by_similarity(
            self.model, clue, remaining_words, skip_board_words=self.skip_board_words
        )
        return self.last_ranking

    def get_answer(self) -> str:
        if not self.remaining:
            raise RuntimeError("EmbeddingGuesser has no remaining words")
        ranking = self.rank(self.clue, self.remaining)
        self.guesses_this_turn += 1
        return ranking[0][0]
