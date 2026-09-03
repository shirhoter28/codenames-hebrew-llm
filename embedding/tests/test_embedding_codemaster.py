"""Embedding codemaster checks. From repo root:

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

from codenames.board import ROLE_ASSASSIN, ROLE_BLUE, ROLE_CIVILIAN, ROLE_RED
from codenames.embedding_codemaster import (
    DEFAULT_THRESHOLD,
    EmbeddingCodemaster,
    choose_clue,
    is_safe_clue,
)
from codenames.embeddings import OutOfVocabularyError, Word2VecEmbeddings, concatenate_embeddings


def _toy_model() -> Word2VecEmbeddings:
    kv = KeyedVectors(vector_size=3)
    kv.add_vectors(
        ["מלך", "מלכה", "כתר", "ארמון", "שולחן", "כיסא", "רהיט"],
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.85, 0.15, 0.0],
                [0.7, 0.3, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
                [0.05, 0.95, 0.0],
            ],
            dtype=np.float32,
        ),
    )
    return Word2VecEmbeddings(kv)


class TestEmbeddingCodemaster(unittest.TestCase):
    def setUp(self) -> None:
        self.model = _toy_model()
        self.reds = ["מלך", "מלכה"]
        self.bads = ["שולחן", "כיסא"]

    def test_safety_rule(self) -> None:
        self.assertEqual(DEFAULT_THRESHOLD, 0.4)
        self.assertTrue(is_safe_clue(0.5, 0.2, threshold=0.3))
        self.assertFalse(is_safe_clue(0.5, 0.6, threshold=0.3))
        self.assertFalse(is_safe_clue(0.25, 0.1, threshold=0.3))

    def test_prefers_larger_safe_group(self) -> None:
        choice = choose_clue(self.model, self.reds, self.bads, threshold=0.2)
        self.assertEqual(choice.targets, ("מלך", "מלכה"))
        self.assertEqual(len(choice.targets), 2)
        self.assertGreater(choice.min_target, choice.max_bad)

    def test_clue_is_not_a_board_word(self) -> None:
        choice = choose_clue(self.model, self.reds, self.bads, threshold=0.2)
        self.assertNotIn(choice.clue, self.reds + self.bads)

    def test_codemaster_returns_clue_and_number(self) -> None:
        cm = EmbeddingCodemaster(self.model, threshold=0.2)
        cm.set_game_state(
            {
                ROLE_RED: self.reds,
                ROLE_BLUE: ["שולחן"],
                ROLE_CIVILIAN: ["כיסא"],
                ROLE_ASSASSIN: ["רהיט"],
            }
        )
        clue, n = cm.get_clue()
        self.assertIsInstance(clue, str)
        self.assertEqual(cm.model, "word2vec")
        self.assertGreaterEqual(n, 1)
        self.assertEqual(n, len(cm.last_targets))
        self.assertTrue(cm.last_choice and is_safe_clue(
            cm.last_choice.min_target, cm.last_choice.max_bad, 0.2
        ))
        self.assertEqual(cm.model_params["codemaster_model"], "word2vec")
        self.assertEqual(cm.model_params["guesser_model"], "word2vec")
        self.assertFalse(cm.model_params["clues_restricted_to_guesser_vocab"])

    def test_oov_board_word_raises(self) -> None:
        with self.assertRaises(OutOfVocabularyError):
            choose_clue(self.model, ["מלך", "פיצה"], ["שולחן"], threshold=0.2)

    def test_no_safe_clue_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            choose_clue(
                self.model,
                reds=["מלך"],
                bads=["מלכה", "כתר", "ארמון"],
                threshold=0.9,
            )

    def test_cross_model_drops_clues_missing_from_guesser(self) -> None:
        kv = KeyedVectors(vector_size=3)
        kv.add_vectors(
            ["מלך", "מלכה", "שולחן", "כיסא", "ארמון"],
            np.array(
                [
                    [1.0, 0.0, 0.0],
                    [0.9, 0.1, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.9, 0.1],
                    [0.8, 0.2, 0.0],
                ],
                dtype=np.float32,
            ),
        )
        guesser = Word2VecEmbeddings(kv, name="fasttext")
        unrestricted = choose_clue(self.model, self.reds, self.bads, threshold=0.2)
        self.assertEqual(unrestricted.clue, "כתר")
        restricted = choose_clue(
            self.model,
            self.reds,
            self.bads,
            threshold=0.2,
            clue_must_be_in=guesser,
        )
        self.assertEqual(restricted.clue, "ארמון")
        self.assertFalse(guesser.contains("כתר"))
        self.assertTrue(guesser.contains("ארמון"))

        cm = EmbeddingCodemaster(
            self.model, threshold=0.2, guesser_embeddings=guesser
        )
        self.assertEqual(cm.model, "word2vec->fasttext")
        self.assertTrue(cm.model_params["clues_restricted_to_guesser_vocab"])

    def test_concat_codemaster_logs_parts_and_single_table_guesser(self) -> None:
        kv_ft = KeyedVectors(vector_size=3)
        kv_ft.add_vectors(
            ["מלך", "מלכה", "כתר", "ארמון", "שולחן", "כיסא", "רהיט"],
            np.array(
                [
                    [1.0, 0.0, 0.0],
                    [0.9, 0.1, 0.0],
                    [0.85, 0.15, 0.0],
                    [0.7, 0.3, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.9, 0.1],
                    [0.05, 0.95, 0.0],
                ],
                dtype=np.float32,
            ),
        )
        guesser = Word2VecEmbeddings(kv_ft, name="fasttext")
        concat = concatenate_embeddings(self.model, guesser)
        cm = EmbeddingCodemaster(
            concat, threshold=0.2, guesser_embeddings=guesser
        )
        self.assertEqual(cm.model, "concat->fasttext")
        self.assertEqual(cm.model_params["codemaster_model"], "concat")
        self.assertEqual(cm.model_params["guesser_model"], "fasttext")
        self.assertEqual(cm.model_params["concat_parts"], ["word2vec", "fasttext"])
        self.assertTrue(cm.model_params["concat_normalize_each"])
        self.assertTrue(cm.model_params["clues_restricted_to_guesser_vocab"])
        cm.set_game_state(
            {
                ROLE_RED: self.reds,
                ROLE_BLUE: ["שולחן"],
                ROLE_CIVILIAN: ["כיסא"],
                ROLE_ASSASSIN: ["רהיט"],
            }
        )
        clue, n = cm.get_clue()
        self.assertIsInstance(clue, str)
        self.assertEqual(n, len(cm.last_targets))

    def test_concat_concat_logs_arrow_model_id(self) -> None:
        kv_ft = KeyedVectors(vector_size=3)
        kv_ft.add_vectors(
            ["מלך", "מלכה", "כתר", "ארמון", "שולחן", "כיסא", "רהיט"],
            np.array(
                [
                    [1.0, 0.0, 0.0],
                    [0.9, 0.1, 0.0],
                    [0.85, 0.15, 0.0],
                    [0.7, 0.3, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.9, 0.1],
                    [0.05, 0.95, 0.0],
                ],
                dtype=np.float32,
            ),
        )
        ft = Word2VecEmbeddings(kv_ft, name="fasttext")
        concat = concatenate_embeddings(self.model, ft)
        cm = EmbeddingCodemaster(
            concat, threshold=0.2, guesser_embeddings=concat
        )
        self.assertEqual(cm.model, "concat->concat")
        self.assertEqual(cm.model_params["codemaster_model"], "concat")
        self.assertEqual(cm.model_params["guesser_model"], "concat")
        self.assertEqual(cm.model_params["concat_parts"], ["word2vec", "fasttext"])
        self.assertFalse(cm.model_params["clues_restricted_to_guesser_vocab"])

    def test_word2vec_to_concat_logs_concat_params(self) -> None:
        kv_ft = KeyedVectors(vector_size=3)
        kv_ft.add_vectors(
            ["מלך", "מלכה", "כתר", "ארמון", "שולחן", "כיסא", "רהיט"],
            np.array(
                [
                    [1.0, 0.0, 0.0],
                    [0.9, 0.1, 0.0],
                    [0.85, 0.15, 0.0],
                    [0.7, 0.3, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.9, 0.1],
                    [0.05, 0.95, 0.0],
                ],
                dtype=np.float32,
            ),
        )
        ft = Word2VecEmbeddings(kv_ft, name="fasttext")
        concat = concatenate_embeddings(self.model, ft)
        cm = EmbeddingCodemaster(
            self.model, threshold=0.2, guesser_embeddings=concat
        )
        self.assertEqual(cm.model, "word2vec->concat")
        self.assertEqual(cm.model_params["guesser_model"], "concat")
        self.assertEqual(cm.model_params["concat_parts"], ["word2vec", "fasttext"])
        self.assertTrue(cm.model_params["clues_restricted_to_guesser_vocab"])


if __name__ == "__main__":
    unittest.main()
