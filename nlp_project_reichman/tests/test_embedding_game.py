"""Wire embedding agents into SingleTeamGame (toy vectors, not NLPL 47)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from gensim.models import KeyedVectors

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import (
    ASSASSIN_COUNT,
    BLUE_COUNT,
    BOARD_SIZE,
    CIVILIAN_COUNT,
    RED_COUNT,
    ROLE_ASSASSIN,
    ROLE_BLUE,
    ROLE_CIVILIAN,
    ROLE_RED,
    Board,
)
from codenames.embedding_codemaster import EmbeddingCodemaster
from codenames.embedding_guesser import EmbeddingGuesser
from codenames.embeddings import Word2VecEmbeddings, concatenate_embeddings
from codenames.game import OUTCOME_ASSASSIN, OUTCOME_WIN, SingleTeamGame


def _synthetic_board_and_model() -> tuple[Board, Word2VecEmbeddings]:
    """25 length-3 Hebrew cards plus extra clue tokens, all in-vocab."""
    board_words = tuple(f"א{i:02d}" for i in range(BOARD_SIZE))
    clue_words = tuple(f"רמז{i}" for i in range(8))
    key_grid = tuple(
        [ROLE_RED] * RED_COUNT
        + [ROLE_BLUE] * BLUE_COUNT
        + [ROLE_CIVILIAN] * CIVILIAN_COUNT
        + [ROLE_ASSASSIN] * ASSASSIN_COUNT
    )
    board = Board(seed=0, wordpool="toy", words=board_words, key_grid=key_grid)

    rng = np.random.default_rng(0)
    vectors = []
    names = list(board_words) + list(clue_words)
    for i, word in enumerate(names):
        if i < RED_COUNT or word.startswith("רמז"):
            base = np.array([1.0, 0.05, 0.0], dtype=np.float32)
        else:
            base = np.array([0.0, 1.0, 0.05], dtype=np.float32)
        vec = base + 0.02 * rng.standard_normal(3).astype(np.float32)
        vectors.append(vec)

    kv = KeyedVectors(vector_size=3)
    kv.add_vectors(names, np.stack(vectors))
    return board, Word2VecEmbeddings(kv, name="word2vec")


class TestEmbeddingSingleTeamGame(unittest.TestCase):
    def test_toy_embedding_game_finishes_and_logs_targets(self) -> None:
        board, embeddings = _synthetic_board_and_model()
        self.assertEqual(embeddings.missing(list(board.words)), [])
        cm = EmbeddingCodemaster(embeddings, threshold=0.15, candidate_limit=50)
        guesser = EmbeddingGuesser(embeddings)
        result = SingleTeamGame(board, cm, guesser, do_print=False).run()
        self.assertIn(result.outcome, {OUTCOME_WIN, OUTCOME_ASSASSIN, "blue_cleared"})
        self.assertEqual(result.codemaster, "embedding")
        self.assertEqual(result.guesser, "embedding")
        self.assertEqual(result.model, "word2vec")
        self.assertIsNotNone(result.model_params)
        self.assertGreaterEqual(result.num_turns, 1)
        self.assertEqual(result.turns[0].remaining_red, board.red)
        self.assertTrue(result.turns[0].parsed_targets)
        self.assertIsNotNone(result.turns[0].min_target)
        self.assertIsNotNone(result.turns[0].max_bad)
        self.assertGreater(result.turns[0].min_target, result.turns[0].max_bad)

    def test_model_field_is_a_string_not_the_vector_table(self) -> None:
        _, embeddings = _synthetic_board_and_model()
        cm = EmbeddingCodemaster(embeddings)
        self.assertEqual(cm.model, "word2vec")
        self.assertIsInstance(cm.model_params, dict)

    def test_cross_model_game_logs_both_tables(self) -> None:
        board, cm_emb = _synthetic_board_and_model()
        kv = KeyedVectors(vector_size=3)
        kv.add_vectors(list(cm_emb.vocabulary()), [cm_emb._kv[w] for w in cm_emb.vocabulary()])
        guesser_emb = Word2VecEmbeddings(kv, name="fasttext")
        cm = EmbeddingCodemaster(
            cm_emb, threshold=0.15, candidate_limit=50, guesser_embeddings=guesser_emb
        )
        result = SingleTeamGame(
            board, cm, EmbeddingGuesser(guesser_emb), do_print=False
        ).run()
        self.assertEqual(result.model, "word2vec->fasttext")
        self.assertEqual(result.model_params["codemaster_model"], "word2vec")
        self.assertEqual(result.model_params["guesser_model"], "fasttext")
        self.assertTrue(result.model_params["clues_restricted_to_guesser_vocab"])
        self.assertIn(result.outcome, {OUTCOME_WIN, OUTCOME_ASSASSIN, "blue_cleared"})

    def test_concat_codemaster_game_logs_concat_to_fasttext(self) -> None:
        board, w2v = _synthetic_board_and_model()
        kv = KeyedVectors(vector_size=3)
        kv.add_vectors(list(w2v.vocabulary()), [w2v._kv[w] for w in w2v.vocabulary()])
        ft = Word2VecEmbeddings(kv, name="fasttext")
        concat = concatenate_embeddings(w2v, ft)
        cm = EmbeddingCodemaster(
            concat, threshold=0.15, candidate_limit=50, guesser_embeddings=ft
        )
        result = SingleTeamGame(
            board, cm, EmbeddingGuesser(ft), do_print=False
        ).run()
        self.assertEqual(result.model, "concat->fasttext")
        self.assertEqual(result.model_params["concat_parts"], ["word2vec", "fasttext"])
        self.assertEqual(result.model_params["concat_dims"], [3, 3])
        self.assertTrue(result.model_params["concat_normalize_each"])
        self.assertIn(result.outcome, {OUTCOME_WIN, OUTCOME_ASSASSIN, "blue_cleared"})

    def test_concat_concat_game_logs_arrow_model_id(self) -> None:
        board, w2v = _synthetic_board_and_model()
        kv = KeyedVectors(vector_size=3)
        kv.add_vectors(list(w2v.vocabulary()), [w2v._kv[w] for w in w2v.vocabulary()])
        ft = Word2VecEmbeddings(kv, name="fasttext")
        concat = concatenate_embeddings(w2v, ft)
        cm = EmbeddingCodemaster(
            concat, threshold=0.15, candidate_limit=50, guesser_embeddings=concat
        )
        result = SingleTeamGame(
            board, cm, EmbeddingGuesser(concat), do_print=False
        ).run()
        self.assertEqual(result.model, "concat->concat")
        self.assertEqual(result.model_params["codemaster_model"], "concat")
        self.assertEqual(result.model_params["guesser_model"], "concat")
        self.assertEqual(result.model_params["concat_parts"], ["word2vec", "fasttext"])
        self.assertIn(result.outcome, {OUTCOME_WIN, OUTCOME_ASSASSIN, "blue_cleared"})


if __name__ == "__main__":
    unittest.main()
