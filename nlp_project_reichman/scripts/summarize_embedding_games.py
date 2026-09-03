#!/usr/bin/env python3
"""Print recaps of embedding games. Hebrew is more readable in the notebook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.summarize_embedding import load_embedding_games, print_recaps


def main() -> None:
    parser = argparse.ArgumentParser(description="Print embedding game recaps")
    parser.add_argument("--seeds", default="0,1,2,3,4")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument(
        "--wordpool",
        default="regular_in_vocab_intersection_fasttext_word2vec",
    )
    args = parser.parse_args()
    seeds = [int(part.strip()) for part in args.seeds.split(",") if part.strip()]
    print_recaps(
        load_embedding_games(),
        seeds=seeds,
        wordpool=args.wordpool or None,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
