"""Load pretrained word vectors for embedding Codenames agents.

Word2Vec C binary/text and fastText ``.vec`` dumps all use
``KeyedVectors.load_word2vec_format``. Facebook fastText ``.bin`` (subword)
is a different format and is not used in the first model comparison.

Concatenation (``ConcatenatedEmbeddings``) is a separate method:
``[L2(word2vec) | L2(fasttext)]``. Official games use it as codemaster
(with a single-table guesser) and, as an added condition, as guesser.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from gensim.models import KeyedVectors

TEXT_SUFFIXES = {".txt", ".vec"}
BINARY_SUFFIXES = {".bin"}


class OutOfVocabularyError(KeyError):
    """Raised when a word has no vector. Callers must not skip the word silently."""

    def __init__(self, *words: str) -> None:
        self.words = words
        super().__init__(", ".join(words) if words else "unknown word")


def infer_embedding_name(path: Path, explicit: str | None = None) -> str:
    """Logged model id. Explicit ``--name`` wins; else guess from the filename."""
    if explicit:
        return explicit
    name = path.name.lower()
    if "glove" in name:
        return "glove"
    if "cc.he" in name or "wiki.he" in name or "fasttext" in name:
        return "fasttext"
    return "word2vec"


def _is_facebook_fasttext_bin(path: Path) -> bool:
    name = path.name.lower()
    return path.suffix.lower() == ".bin" and (
        "cc.he" in name or name.startswith("wiki.he") or "fasttext" in name
    )


def _is_binary_word2vec_path(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return False
    if suffix in BINARY_SUFFIXES:
        return True
    raise ValueError(
        f"Unknown embedding file type {path.name!r}. "
        "Use Word2Vec model.bin, or fastText wiki.he.vec / cc.he.300.vec."
    )


class Word2VecEmbeddings:
    """Cosine similarity over a gensim ``KeyedVectors`` table (any compatible dump)."""

    def __init__(self, keyed_vectors: KeyedVectors, name: str = "word2vec") -> None:
        self._kv = keyed_vectors
        self.name = name

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        name: str | None = None,
    ) -> Word2VecEmbeddings:
        model_path = Path(path)
        if model_path.suffix.lower() == ".zip":
            raise ValueError(
                "Pass the extracted vector file, not a zip archive."
            )
        if not model_path.is_file():
            raise FileNotFoundError(f"Embedding file not found: {model_path}")
        if _is_facebook_fasttext_bin(model_path):
            raise ValueError(
                "Facebook fastText .bin includes subword vectors and is a later "
                "experimental condition. For the first comparison download the "
                "word-level .vec file (wiki.he.vec or cc.he.300.vec)."
            )

        binary = _is_binary_word2vec_path(model_path)
        keyed = KeyedVectors.load_word2vec_format(
            str(model_path),
            binary=binary,
            unicode_errors="ignore",
        )
        return cls(keyed, name=infer_embedding_name(model_path, name))

    @property
    def vector_size(self) -> int:
        return int(self._kv.vector_size)

    def contains(self, word: str) -> bool:
        return word in self._kv

    def _require(self, word: str) -> None:
        if word not in self._kv:
            raise OutOfVocabularyError(word)

    def get_vector(self, word: str) -> np.ndarray:
        """Raw vector for ``word``. Raises ``OutOfVocabularyError`` if missing."""
        self._require(word)
        return np.asarray(self._kv.get_vector(word), dtype=np.float64)

    def similarity(self, word1: str, word2: str) -> float:
        """Cosine similarity. Raises ``OutOfVocabularyError`` if either word is missing."""
        self._require(word1)
        self._require(word2)
        return float(self._kv.similarity(word1, word2))

    def nearest_neighbors(self, word: str, topn: int = 10) -> list[tuple[str, float]]:
        """Most similar vocabulary items by cosine similarity."""
        self._require(word)
        return [(w, float(score)) for w, score in self._kv.most_similar(word, topn=topn)]

    def vocabulary(self, limit: int | None = None) -> list[str]:
        """Keys in model order (word2vec dumps are typically frequency-sorted)."""
        keys = self._kv.index_to_key
        if limit is None:
            return list(keys)
        return list(keys[:limit])

    def missing(self, words: list[str]) -> list[str]:
        """Board or probe words with no vector, in input order."""
        return [word for word in words if word not in self._kv]

    def in_vocab(self, words: list[str]) -> list[str]:
        """Keep words that have a vector, original order, exact match."""
        return [word for word in words if word in self._kv]


def in_vocab_wordpool_label(base: str, model_name: str) -> str:
    """Logged wordpool name for embedding games (does not change CSV files)."""
    return f"{base}_in_vocab_{model_name}"


def intersection_in_vocab(
    words: list[str], *models: Word2VecEmbeddings
) -> list[str]:
    """Words present in every model, original list order, exact string match."""
    if not models:
        raise ValueError("Need at least one embedding model")
    return [word for word in words if all(model.contains(word) for model in models)]


def intersection_wordpool_label(base: str, model_names: list[str]) -> str:
    """Logged label for a shared in-vocab pool. Names are sorted so CLI order does not matter."""
    parts = sorted(set(model_names))
    if len(parts) < 2:
        raise ValueError("Intersection label needs at least two distinct model names")
    return f"{base}_in_vocab_intersection_{'_'.join(parts)}"


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    vec = np.asarray(vec, dtype=np.float64)
    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return vec
    return vec / norm


def _cosine(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    denom = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


def ordered_concat_pair(
    first: Word2VecEmbeddings, second: Word2VecEmbeddings
) -> tuple[Word2VecEmbeddings, Word2VecEmbeddings]:
    """Stable concat layout: word2vec then fastText when those names are used."""
    by_name = {first.name: first, second.name: second}
    if "word2vec" in by_name and "fasttext" in by_name:
        return by_name["word2vec"], by_name["fasttext"]
    if first.name <= second.name:
        return first, second
    return second, first


class ConcatenatedEmbeddings:
    """Equal-weight concatenation of two tables: ``[L2(a) | L2(b)]``.

    Each source vector is L2-normalized before concat so a 300-d table does not
    dominate a 100-d table. Cosine in this space is the mean of the two unit
    cosines. Vocabulary is the exact-string intersection, in the first part's
    dump order (Word2Vec frequency order when parts are word2vec + fasttext).

    This is a **method**, not a dimension hyperparameter. Official games include
    concat as codemaster (with a single-table guesser) and, separately,
    concat as guesser (``word2vec->concat``, ``fasttext->concat``,
    ``concat->concat``).
    """

    def __init__(
        self,
        first: Word2VecEmbeddings,
        second: Word2VecEmbeddings,
        name: str = "concat",
        normalize_each: bool = True,
    ) -> None:
        if first.name == second.name:
            raise ValueError("Concatenation needs two distinct embedding tables")
        self.left, self.right = ordered_concat_pair(first, second)
        self.name = name
        self.normalize_each = normalize_each
        self.part_names = (self.left.name, self.right.name)
        self.part_dims = (self.left.vector_size, self.right.vector_size)

    @property
    def vector_size(self) -> int:
        return self.left.vector_size + self.right.vector_size

    def contains(self, word: str) -> bool:
        return self.left.contains(word) and self.right.contains(word)

    def _require(self, word: str) -> None:
        missing = []
        if not self.left.contains(word):
            missing.append(word)
        elif not self.right.contains(word):
            missing.append(word)
        if missing:
            raise OutOfVocabularyError(*missing)

    def get_vector(self, word: str) -> np.ndarray:
        self._require(word)
        left = self.left.get_vector(word)
        right = self.right.get_vector(word)
        if self.normalize_each:
            left = _l2_normalize(left)
            right = _l2_normalize(right)
        return np.concatenate([left, right])

    def similarity(self, word1: str, word2: str) -> float:
        return _cosine(self.get_vector(word1), self.get_vector(word2))

    def vocabulary(self, limit: int | None = None) -> list[str]:
        """Intersection keys in the first part's dump order."""
        out: list[str] = []
        for word in self.left.vocabulary():
            if not self.right.contains(word):
                continue
            out.append(word)
            if limit is not None and len(out) >= limit:
                break
        return out

    def missing(self, words: list[str]) -> list[str]:
        return [word for word in words if not self.contains(word)]

    def in_vocab(self, words: list[str]) -> list[str]:
        return [word for word in words if self.contains(word)]


def concatenate_embeddings(
    first: Word2VecEmbeddings,
    second: Word2VecEmbeddings,
    name: str = "concat",
) -> ConcatenatedEmbeddings:
    """Build the official concat table (normalize each part, word2vec then fastText)."""
    return ConcatenatedEmbeddings(first, second, name=name, normalize_each=True)


EmbeddingModel = Word2VecEmbeddings | ConcatenatedEmbeddings
