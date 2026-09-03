"""Shir fixed-board loading and OOV policy."""

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
from codenames.embedding_codemaster import choose_clue
from codenames.embedding_guesser import rank_by_similarity
from codenames.embeddings import OutOfVocabularyError, Word2VecEmbeddings
from codenames.shir_boards import (
    DEFAULT_BOARDS_PATH,
    classify_oov,
    intersection_oov_words,
    load_shir_boards,
)


def _toy() -> Word2VecEmbeddings:
    kv = KeyedVectors(vector_size=3)
    kv.add_vectors(
        ["מלך", "מלכה", "כתר", "שולחן", "כיסא"],
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.85, 0.15, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
            ],
            dtype=np.float32,
        ),
    )
    return Word2VecEmbeddings(kv)


class TestShirBoards(unittest.TestCase):
    def test_load_90_boards_and_roles(self) -> None:
        if not DEFAULT_BOARDS_PATH.is_file():
            self.skipTest("data/boards/shirs_boards.json missing")
        boards = load_shir_boards()
        self.assertEqual(len(boards), 90)
        dual0 = [b for b in boards if b.wordpool == "shir_dual_0"]
        self.assertEqual(len(dual0), 30)
        board = dual0[0]
        self.assertEqual(len(board.red), 9)
        self.assertEqual(len(board.blue), 8)
        self.assertEqual(len(board.civilian), 7)
        self.assertEqual(board.assassin, board.assassin)

    def test_red_oov_is_loss_even_if_assassin_oov(self) -> None:
        boards = load_shir_boards()
        board = next(b for b in boards if b.wordpool == "shir_dual_0" and b.seed == 0)
        oov = classify_oov(board, [board.red[0], board.assassin])
        self.assertTrue(oov.red_loss)
        self.assertFalse(oov.assassin_unfair)

    def test_assassin_oov_without_red_is_unfair_play(self) -> None:
        boards = load_shir_boards()
        board = next(b for b in boards if b.wordpool == "shir_dual_0" and b.seed == 0)
        oov = classify_oov(board, [board.assassin])
        self.assertFalse(oov.red_loss)
        self.assertTrue(oov.assassin_unfair)

    def test_blue_oov_plays(self) -> None:
        boards = load_shir_boards()
        board = next(b for b in boards if b.wordpool == "shir_dual_0" and b.seed == 0)
        oov = classify_oov(board, [board.blue[0]])
        self.assertFalse(oov.red_loss)
        self.assertTrue(oov.oov_blue)
        self.assertFalse(oov.assassin_unfair)

    def test_intersection_oov_is_union_of_missing(self) -> None:
        a = _toy()
        kv = KeyedVectors(vector_size=3)
        kv.add_vectors(
            ["מלך", "מלכה", "כתר"],
            np.zeros((3, 3), dtype=np.float32),
        )
        b = Word2VecEmbeddings(kv, name="fasttext")
        missing = intersection_oov_words(["מלך", "שולחן", "פיצה"], a, b)
        self.assertEqual(missing, ["שולחן", "פיצה"])

    def test_choose_clue_skips_oov_bads(self) -> None:
        model = _toy()
        choice = choose_clue(
            model,
            reds=["מלך", "מלכה"],
            bads=["שולחן", "פיצה"],
            threshold=0.2,
            skip_board_words=["פיצה"],
        )
        self.assertGreater(choice.min_target, choice.max_bad)

    def test_choose_clue_still_raises_on_skipped_red(self) -> None:
        model = _toy()
        with self.assertRaises(OutOfVocabularyError):
            choose_clue(
                model,
                reds=["מלך", "פיצה"],
                bads=["שולחן"],
                threshold=0.2,
                skip_board_words=["פיצה"],
            )

    def test_rank_skips_oov_board_word(self) -> None:
        model = _toy()
        ranking = rank_by_similarity(
            model, "מלך", ["מלכה", "פיצה", "כתר"], skip_board_words=["פיצה"]
        )
        self.assertEqual([w for w, _ in ranking], ["מלכה", "כתר"])


if __name__ == "__main__":
    unittest.main()
