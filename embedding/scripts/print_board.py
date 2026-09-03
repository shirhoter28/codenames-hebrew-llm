#!/usr/bin/env python3
"""Print a reproducible Codenames board.

Usage (from repo root):

    PYTHONPATH=. python scripts/print_board.py --seed 0
    PYTHONPATH=. python scripts/print_board.py --seed 0 --wordpool dual
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import WORDPOOLS, create_board


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a Hebrew Codenames board")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--wordpool", choices=WORDPOOLS, default="regular")
    parser.add_argument(
        "--guesser",
        action="store_true",
        help="Hide roles (guesser view)",
    )
    args = parser.parse_args()

    board = create_board(seed=args.seed, wordpool=args.wordpool)
    if args.guesser:
        print(board.format_guesser_view())
    else:
        print(board.format_codemaster_view())


if __name__ == "__main__":
    main()
