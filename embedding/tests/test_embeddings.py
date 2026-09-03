"""Word2Vec wrapper checks. From repo root:

    PYTHONPATH=. python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from gensim.models import KeyedVectors

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.embeddings import (
    ConcatenatedEmbeddings,
    OutOfVocabularyError,
    Word2VecEmbeddings,
    concatenate_embeddings,
    infer_embedding_name,
    intersection_in_vocab,
    intersection_wordpool_label,
    ordered_concat_pair,
)


def _write_toy_binary(path: Path) -> None:
    kv = KeyedVectors(vector_size=3)
    kv.add_vectors(
        ["מלך", "מלכה", "שולחן", "כיסא"],
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.9, 0.1],
            ],
            dtype=np.float32,
        ),
    )
    kv.save_word2vec_format(str(path), binary=True)


class TestWord2VecEmbeddings(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.bin_path = Path(self.tmp.name) / "toy.bin"
        _write_toy_binary(self.bin_path)
        self.model = Word2VecEmbeddings.from_path(self.bin_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_loads_word2vec_c_binary_not_gensim_native(self) -> None:
        header = self.bin_path.read_bytes()[:16]
        self.assertTrue(header.startswith(b"4 3"))

    def test_contains_exact_hebrew(self) -> None:
        self.assertTrue(self.model.contains("מלך"))
        self.assertFalse(self.model.contains("אבטיח"))

    def test_cosine_ranks_related_pair_higher(self) -> None:
        royal = self.model.similarity("מלך", "מלכה")
        furniture = self.model.similarity("מלך", "שולחן")
        self.assertGreater(royal, furniture)

    def test_nearest_neighbor_of_king_is_queen(self) -> None:
        neighbors = self.model.nearest_neighbors("מלך", topn=3)
        self.assertEqual(neighbors[0][0], "מלכה")

    def test_missing_word_raises(self) -> None:
        with self.assertRaises(OutOfVocabularyError):
            self.model.similarity("מלך", "אבטיח")
        with self.assertRaises(OutOfVocabularyError):
            self.model.nearest_neighbors("אבטיח", topn=1)

    def test_zip_path_is_rejected(self) -> None:
        zip_path = Path(self.tmp.name) / "47.zip"
        zip_path.write_bytes(b"not a model")
        with self.assertRaises(ValueError):
            Word2VecEmbeddings.from_path(zip_path)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            Word2VecEmbeddings.from_path(Path(self.tmp.name) / "missing.bin")

    def test_in_vocab_keeps_order_and_drops_missing(self) -> None:
        kept = self.model.in_vocab(["מלכה", "אבטיח", "מלך", "אבטיח"])
        self.assertEqual(kept, ["מלכה", "מלך"])
        self.assertEqual(self.model.missing(["מלכה", "אבטיח"]), ["אבטיח"])

    def test_vec_file_is_named_fasttext_from_filename(self) -> None:
        vec_path = Path(self.tmp.name) / "wiki.he.vec"
        kv = KeyedVectors(vector_size=3)
        kv.add_vectors(
            ["מלך", "מלכה"],
            np.array([[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]], dtype=np.float32),
        )
        kv.save_word2vec_format(str(vec_path), binary=False)
        model = Word2VecEmbeddings.from_path(vec_path)
        self.assertEqual(model.name, "fasttext")
        self.assertTrue(model.contains("מלך"))

    def test_facebook_fasttext_bin_is_rejected_for_now(self) -> None:
        fake = Path(self.tmp.name) / "cc.he.300.bin"
        fake.write_bytes(b"not facebook format")
        with self.assertRaises(ValueError) as ctx:
            Word2VecEmbeddings.from_path(fake)
        self.assertIn(".vec", str(ctx.exception))

    def test_intersection_keeps_source_order(self) -> None:
        other = Word2VecEmbeddings(self.model._kv, name="fasttext")
        words = ["מלכה", "אבטיח", "מלך", "שולחן"]
        kept = intersection_in_vocab(words, self.model, other)
        self.assertEqual(kept, ["מלכה", "מלך", "שולחן"])
        self.assertEqual(
            intersection_wordpool_label("regular", ["word2vec", "fasttext"]),
            "regular_in_vocab_intersection_fasttext_word2vec",
        )
        self.assertEqual(
            intersection_wordpool_label("regular", ["fasttext", "word2vec"]),
            "regular_in_vocab_intersection_fasttext_word2vec",
        )

    def test_intersection_requires_both_models(self) -> None:
        kv2 = KeyedVectors(vector_size=3)
        kv2.add_vectors(
            ["מלך", "אבטיח", "שולחן"],
            np.array(
                [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                dtype=np.float32,
            ),
        )
        other = Word2VecEmbeddings(kv2, name="fasttext")
        kept = intersection_in_vocab(
            ["מלכה", "אבטיח", "מלך", "שולחן"], self.model, other
        )
        self.assertEqual(kept, ["מלך", "שולחן"])

    def test_infer_embedding_name(self) -> None:
        self.assertEqual(infer_embedding_name(Path("model.bin")), "word2vec")
        self.assertEqual(infer_embedding_name(Path("wiki.he.vec")), "fasttext")
        self.assertEqual(
            infer_embedding_name(Path("wiki.he.vec"), explicit="fasttext-wiki"),
            "fasttext-wiki",
        )


def _toy_concat_parts() -> tuple[Word2VecEmbeddings, Word2VecEmbeddings]:
    kv_w2v = KeyedVectors(vector_size=2)
    kv_w2v.add_vectors(
        ["מלך", "מלכה", "שולחן", "רק_ווק"],
        np.array(
            [
                [1.0, 0.0],
                [0.9, 0.1],
                [0.0, 1.0],
                [1.0, 1.0],
            ],
            dtype=np.float32,
        ),
    )
    kv_ft = KeyedVectors(vector_size=3)
    kv_ft.add_vectors(
        ["מלך", "מלכה", "שולחן", "רק_פט"],
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0],
            ],
            dtype=np.float32,
        ),
    )
    return (
        Word2VecEmbeddings(kv_w2v, name="word2vec"),
        Word2VecEmbeddings(kv_ft, name="fasttext"),
    )


class TestConcatenatedEmbeddings(unittest.TestCase):
    def setUp(self) -> None:
        self.w2v, self.ft = _toy_concat_parts()
        self.concat = concatenate_embeddings(self.w2v, self.ft)

    def test_intersection_vocab_and_word2vec_order(self) -> None:
        self.assertTrue(self.concat.contains("מלך"))
        self.assertFalse(self.concat.contains("רק_ווק"))
        self.assertFalse(self.concat.contains("רק_פט"))
        self.assertEqual(self.concat.vocabulary(), ["מלך", "מלכה", "שולחן"])
        self.assertEqual(self.concat.vector_size, 5)
        self.assertEqual(self.concat.part_names, ("word2vec", "fasttext"))
        self.assertEqual(self.concat.part_dims, (2, 3))

    def test_layout_ignores_constructor_order(self) -> None:
        reversed_pair = concatenate_embeddings(self.ft, self.w2v)
        self.assertEqual(reversed_pair.part_names, ("word2vec", "fasttext"))
        left, right = ordered_concat_pair(self.ft, self.w2v)
        self.assertIs(left, self.w2v)
        self.assertIs(right, self.ft)
        np.testing.assert_allclose(
            reversed_pair.get_vector("מלך"), self.concat.get_vector("מלך")
        )

    def test_cosine_is_mean_of_unit_cosines(self) -> None:
        w2v_cos = self.w2v.similarity("מלך", "מלכה")
        ft_cos = self.ft.similarity("מלך", "מלכה")
        expected = 0.5 * (w2v_cos + ft_cos)
        self.assertAlmostEqual(self.concat.similarity("מלך", "מלכה"), expected, places=6)

    def test_normalize_each_stops_longer_table_from_dominating(self) -> None:
        kv_small = KeyedVectors(vector_size=1)
        kv_small.add_vectors(
            ["א", "ב"],
            np.array([[1.0], [1.0]], dtype=np.float32),
        )
        kv_large = KeyedVectors(vector_size=2)
        kv_large.add_vectors(
            ["א", "ב"],
            np.array([[100.0, 0.0], [0.0, 100.0]], dtype=np.float32),
        )
        a = Word2VecEmbeddings(kv_small, name="word2vec")
        b = Word2VecEmbeddings(kv_large, name="fasttext")
        equal = ConcatenatedEmbeddings(a, b, normalize_each=True)
        raw = ConcatenatedEmbeddings(a, b, normalize_each=False)
        self.assertAlmostEqual(equal.similarity("א", "ב"), 0.5, places=5)
        self.assertLess(raw.similarity("א", "ב"), 0.05)

    def test_oov_in_either_table_raises(self) -> None:
        with self.assertRaises(OutOfVocabularyError):
            self.concat.similarity("מלך", "רק_ווק")

    def test_same_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            concatenate_embeddings(self.w2v, Word2VecEmbeddings(self.w2v._kv, name="word2vec"))


if __name__ == "__main__":
    unittest.main()
