"""Embedding guesser checks. From repo root:

    PYTHONPATH=. python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from gensim.models import KeyedVectors

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.embedding_guesser import EmbeddingGuesser, rank_by_similarity
from codenames.embeddings import OutOfVocabularyError, Word2VecEmbeddings


def _toy_model() -> Word2VecEmbeddings:
    kv = KeyedVectors(vector_size=3)
    kv.add_vectors(
        ["מלך", "מלכה", "כתר", "שולחן", "כיסא"],
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.8, 0.2, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
            ],
            dtype=np.float32,
        ),
    )
    return Word2VecEmbeddings(kv)


class TestRankBySimilarity(unittest.TestCase):
    def setUp(self) -> None:
        self.model = _toy_model()

    def test_ranks_board_words_by_cosine_to_clue(self) -> None:
        remaining = ["שולחן", "כתר", "מלכה"]
        ranking = rank_by_similarity(self.model, "מלך", remaining)
        self.assertEqual([word for word, _ in ranking], ["מלכה", "כתר", "שולחן"])
        self.assertGreater(ranking[0][1], ranking[1][1])
        self.assertGreater(ranking[1][1], ranking[2][1])

    def test_guess_is_the_top_ranked_word(self) -> None:
        guesser = EmbeddingGuesser(self.model)
        guesser.set_board(["שולחן", "מלכה", "כיסא"])
        guesser.set_clue("כתר", 1)
        self.assertEqual(guesser.get_answer(), "מלכה")
        self.assertEqual(guesser.last_ranking[0][0], "מלכה")

    def test_oov_clue_or_board_word_raises_listing_missing(self) -> None:
        with self.assertRaises(OutOfVocabularyError) as ctx:
            rank_by_similarity(self.model, "אבטיח", ["מלך", "שולחן"])
        self.assertIn("אבטיח", ctx.exception.words)

        with self.assertRaises(OutOfVocabularyError) as ctx:
            rank_by_similarity(self.model, "מלך", ["מלכה", "פיצה"])
        self.assertEqual(ctx.exception.words, ("פיצה",))

    def test_keep_guessing_stops_at_clue_number(self) -> None:
        guesser = EmbeddingGuesser(self.model)
        guesser.set_clue("מלך", 2)
        guesser.set_board(["מלכה", "כתר", "שולחן"])
        guesser.get_answer()
        self.assertTrue(guesser.keep_guessing())
        guesser.get_answer()
        self.assertFalse(guesser.keep_guessing())


if __name__ == "__main__":
    unittest.main()
