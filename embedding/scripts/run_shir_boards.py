#!/usr/bin/env python3
"""Play official embedding methods on Shir's fixed boards.

Logs go to ``results/embedding/shir/`` (not the official series folder).
OOV is vs Word2Vec ∩ fastText. Policy ``shir_v1``: red OOV → ``oov_loss``
(no play); assassin/blue/civilian OOV → play with those cards skipped in
cosine. See ``codenames/shir_boards.py``.

Usage (from repo root):

    PYTHONPATH=. python scripts/run_shir_boards.py --play-both --cross --concat
    PYTHONPATH=. python scripts/run_shir_boards.py --concat-guesser
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import Board
from codenames.embedding_codemaster import DEFAULT_CANDIDATE_LIMIT, DEFAULT_THRESHOLD, EmbeddingCodemaster
from codenames.embedding_guesser import EmbeddingGuesser
from codenames.embeddings import EmbeddingModel, Word2VecEmbeddings, concatenate_embeddings
from codenames.game import LOSS_SCORE, GameResult, SingleTeamGame
from codenames.logging_io import SHIR_RESULTS_DIR, write_game_result
from codenames.shir_boards import (
    DEFAULT_BOARDS_PATH,
    OUTCOME_OOV_LOSS,
    SHIR_STYLES,
    ShirOovInfo,
    classify_oov,
    intersection_oov_words,
    load_shir_boards,
)

OUTCOME_NO_SAFE = "no_safe_clue"


def _parse_styles(raw: str | None) -> list[str]:
    if not raw:
        return list(SHIR_STYLES)
    return [part.strip() for part in raw.split(",") if part.strip()]


def _attach_oov(cm: EmbeddingCodemaster, board: Board, oov: ShirOovInfo) -> None:
    cm.model_params.update(oov.as_log_dict())
    cm.model_params["board_source"] = "shir"
    cm.model_params["shir_style"] = board.wordpool.removeprefix("shir_")


def _stub_result(
    board: Board,
    cm: EmbeddingCodemaster,
    outcome: str,
    reason: str,
) -> GameResult:
    params = dict(cm.model_params)
    params["stub_reason"] = reason
    return GameResult(
        mode="single_team",
        seed=board.seed,
        wordpool=board.wordpool,
        codemaster=cm.name,
        guesser="embedding",
        board_words=list(board.words),
        key_grid=list(board.key_grid),
        turns=[],
        outcome=outcome,
        num_turns=0,
        red_revealed=0,
        blue_revealed=0,
        civilian_revealed=0,
        assassin_revealed=False,
        score=LOSS_SCORE,
        finished_at=datetime.now(timezone.utc).isoformat(),
        model=cm.model,
        model_params=params,
    )


def play_board(
    cm_model: EmbeddingModel,
    guesser_model: EmbeddingModel,
    board: Board,
    oov: ShirOovInfo,
    threshold: float,
    candidate_limit: int,
    do_print: bool,
    write_log: bool,
) -> None:
    skip = list(oov.words)
    cm = EmbeddingCodemaster(
        cm_model,
        threshold=threshold,
        candidate_limit=candidate_limit,
        guesser_embeddings=guesser_model,
        skip_board_words=skip,
    )
    _attach_oov(cm, board, oov)
    guesser = EmbeddingGuesser(guesser_model, skip_board_words=skip)

    if oov.red_loss:
        result = _stub_result(board, cm, OUTCOME_OOV_LOSS, "red OOV")
    else:
        try:
            result = SingleTeamGame(board, cm, guesser, do_print=do_print).run()
        except RuntimeError as exc:
            if "No safe embedding clue" not in str(exc):
                raise
            result = _stub_result(board, cm, OUTCOME_NO_SAFE, str(exc))

    print(
        f"style={board.wordpool}  seed={board.seed}  model={result.model}  "
        f"outcome={result.outcome}  turns={result.num_turns}  "
        f"oov_red_loss={oov.red_loss}  assassin_oov_unfair={oov.assassin_unfair}  "
        f"oov_blue={oov.oov_blue}  oov_civilian={oov.oov_civilian}"
    )
    if write_log:
        path = write_game_result(result, results_dir=SHIR_RESULTS_DIR)
        print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Embedding games on Shir's fixed boards")
    parser.add_argument("--model", type=Path, default=REPO_ROOT / "data" / "model.bin")
    parser.add_argument(
        "--intersect-with",
        type=Path,
        default=REPO_ROOT / "data" / "embeddings" / "wiki.he.vec",
    )
    parser.add_argument("--boards", type=Path, default=DEFAULT_BOARDS_PATH)
    parser.add_argument("--play-both", action="store_true")
    parser.add_argument("--cross", action="store_true")
    parser.add_argument("--concat", action="store_true")
    parser.add_argument(
        "--concat-guesser",
        action="store_true",
        help="Play each of word2vec, fasttext, concat as CM vs a concatenated guesser",
    )
    parser.add_argument("--styles", default=None, help="Comma-separated: dual_0,natural,dual_100")
    parser.add_argument("--seeds", default=None, help="Comma-separated seeds (default: all)")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--candidate-limit", type=int, default=DEFAULT_CANDIDATE_LIMIT)
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    word2vec = Word2VecEmbeddings.from_path(args.model, name="word2vec")
    fasttext = Word2VecEmbeddings.from_path(args.intersect_with, name="fasttext")
    boards = load_shir_boards(args.boards)
    styles = set(_parse_styles(args.styles))
    seed_filter = None
    if args.seeds:
        seed_filter = {int(part.strip()) for part in args.seeds.split(",") if part.strip()}
    boards = [
        board
        for board in boards
        if board.wordpool.removeprefix("shir_") in styles
        and (seed_filter is None or board.seed in seed_filter)
    ]

    oov_by_key = {
        (board.wordpool, board.seed): classify_oov(
            board, intersection_oov_words(list(board.words), word2vec, fasttext)
        )
        for board in boards
    }

    pairs: list[tuple[EmbeddingModel, EmbeddingModel]] = []
    concat_model = None
    if args.concat or args.concat_guesser:
        concat_model = concatenate_embeddings(word2vec, fasttext)
    if args.play_both:
        pairs.append((word2vec, word2vec))
        pairs.append((fasttext, fasttext))
    if args.cross:
        pairs.append((word2vec, fasttext))
        pairs.append((fasttext, word2vec))
    if args.concat and concat_model is not None:
        pairs.append((concat_model, word2vec))
        pairs.append((concat_model, fasttext))
    if args.concat_guesser and concat_model is not None:
        pairs.append((word2vec, concat_model))
        pairs.append((fasttext, concat_model))
        pairs.append((concat_model, concat_model))
    if not pairs:
        pairs.append((word2vec, word2vec))

    quiet = args.quiet or len(boards) > 1 or len(pairs) > 1
    print(f"shir boards={len(boards)}  methods={len(pairs)}  logs={SHIR_RESULTS_DIR}")
    for cm_model, guesser_model in pairs:
        print(f"Playing cm={cm_model.name} guesser={guesser_model.name}")
        for board in boards:
            oov = oov_by_key[(board.wordpool, board.seed)]
            play_board(
                cm_model,
                guesser_model,
                board,
                oov,
                args.threshold,
                args.candidate_limit,
                do_print=not quiet,
                write_log=not args.no_log,
            )


if __name__ == "__main__":
    main()
