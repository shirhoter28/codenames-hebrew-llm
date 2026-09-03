#!/usr/bin/env python3
"""Measure how much of our Hebrew Codenames wordpool is in an embedding table.

Exact string match against ``load_wordpool``. Missing words are listed, not skipped.

Usage (from repo root):

    PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/model.bin
    PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/embeddings/wiki.he.vec
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import WORDPOOLS, load_wordpool
from codenames.embeddings import Word2VecEmbeddings, intersection_in_vocab

DEFAULT_MODEL = REPO_ROOT / "data" / "embeddings" / "model.bin"
PROBE_PAIRS = (("מלך", "מלכה"), ("מלך", "שולחן"))
NEIGHBOR_PROBES = ("מלך", "עיר", "מים")


def coverage(model: Word2VecEmbeddings, words: list[str]) -> tuple[list[str], list[str]]:
    in_vocab: list[str] = []
    oov: list[str] = []
    for word in words:
        if model.contains(word):
            in_vocab.append(word)
        else:
            oov.append(word)
    return in_vocab, oov


def _print_probes(model: Word2VecEmbeddings) -> None:
    print("\nCosine similarity probes (model vocab, not the Codenames list):")
    for a, b in PROBE_PAIRS:
        if model.contains(a) and model.contains(b):
            print(f"  sim({a!r}, {b!r}) = {model.similarity(a, b):.4f}")
        else:
            missing = [w for w in (a, b) if not model.contains(w)]
            print(f"  skipped ({a!r}, {b!r}); OOV: {missing}")

    print("\nNearest neighbors:")
    for word in NEIGHBOR_PROBES:
        if not model.contains(word):
            print(f"  {word!r}: OOV in the embedding model")
            continue
        neighbors = model.nearest_neighbors(word, topn=5)
        formatted = ", ".join(f"{w} ({s:.3f})" for w, s in neighbors)
        print(f"  {word}: {formatted}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Codenames wordpool coverage against a Word2Vec file"
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL,
        help="Path to Word2Vec model.bin or fastText .vec",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Logged model id (default: infer from filename: wiki.he.vec → fasttext)",
    )
    parser.add_argument("--wordpool", choices=WORDPOOLS, default="regular")
    parser.add_argument(
        "--intersect-with",
        type=Path,
        default=None,
        help="Second embedding file; also print the intersection in-vocab list.",
    )
    parser.add_argument(
        "--intersect-name",
        default=None,
        help="Logged id for --intersect-with (default: infer from filename).",
    )
    parser.add_argument(
        "--no-probes",
        action="store_true",
        help="Print coverage only; skip similarity / neighbor examples",
    )
    args = parser.parse_args()

    words = load_wordpool(args.wordpool)
    model = Word2VecEmbeddings.from_path(args.model, name=args.name)
    in_vocab, oov = coverage(model, words)
    n = len(words)
    n_in = len(in_vocab)
    pct = 100.0 * n_in / n if n else 0.0

    print(f"model_file={args.model}  model_name={model.name}")
    print(f"wordpool={args.wordpool}  n={n}")
    print(f"in_vocab={n_in}  oov={len(oov)}  coverage={pct:.1f}%")
    print("\nOOV words:")
    if oov:
        for word in oov:
            print(f"  {word}")
    else:
        print("  (none)")

    if not args.no_probes:
        _print_probes(model)

    if args.intersect_with is not None:
        other = Word2VecEmbeddings.from_path(
            args.intersect_with, name=args.intersect_name
        )
        both = intersection_in_vocab(words, model, other)
        dropped = [word for word in words if word not in set(both)]
        pct_both = 100.0 * len(both) / n if n else 0.0
        print(
            f"\nintersection with {args.intersect_with} ({other.name})\n"
            f"in_both={len(both)}  dropped={len(dropped)}  coverage={pct_both:.1f}%"
        )
        print("Dropped (union of OOVs):")
        if dropped:
            for word in dropped:
                print(f"  {word}")
        else:
            print("  (none)")


if __name__ == "__main__":
    main()
