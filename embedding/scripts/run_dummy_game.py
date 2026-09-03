#!/usr/bin/env python3
"""Run one single-team dummy game.

Usage (from repo root):

    PYTHONPATH=. python scripts/run_dummy_game.py --seed 0
    PYTHONPATH=. python scripts/run_dummy_game.py --seed 0 --guesser oracle
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import WORDPOOLS, create_board
from codenames.game import SingleTeamGame
from codenames.logging_io import write_game_result
from codenames.players import DummyCodemaster, DummyGuesser, OracleGuesser


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single-team dummy Codenames game")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--wordpool", choices=WORDPOOLS, default="regular")
    parser.add_argument(
        "--guesser",
        choices=("dummy", "oracle"),
        default="dummy",
        help="dummy = first remaining word; oracle = always pick Red (engine check only)",
    )
    parser.add_argument("--no-log", action="store_true")
    args = parser.parse_args()

    board = create_board(seed=args.seed, wordpool=args.wordpool)
    codemaster = DummyCodemaster()
    if args.guesser == "oracle":
        guesser = OracleGuesser(board.role_of)
    else:
        guesser = DummyGuesser()

    result = SingleTeamGame(board, codemaster, guesser, do_print=True).run()
    if not args.no_log:
        path = write_game_result(result)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
