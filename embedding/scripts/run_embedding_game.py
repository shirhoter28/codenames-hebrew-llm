#!/usr/bin/env python3
"""Run one single-team game with embedding codemaster and guesser.

Boards are sampled from an in-vocab subset of the named CSV wordpool.
``regular.csv`` is not edited.

Default logged wordpool: ``{source}_in_vocab_{model}``.

For **comparable** boards across two tables, pass ``--intersect-with`` so
both same-model and cross games share the same 25 cards at a given seed.
Per-model in-vocab (no ``--intersect-with``) is a different condition.

``--intersect-with`` is a **separate condition**: keep words in both vocabs
(original CSV order) so the same seed is the same 25 cards for both models.
Logged as ``{source}_in_vocab_intersection_{nameA}_{nameB}`` (names sorted).
``--play-both`` runs same-model games for each table on that shared pool.
``--cross`` runs Kim-style mixed games (codemaster from one table, guesser from
the other) on the same intersection boards. Cross-model clues are restricted
to tokens present in the guesser table so the guesser does not hit OOV.
``--concat`` uses concatenated Word2Vec+fastText as **codemaster only**, paired
with each single-table guesser (``concat->word2vec``, ``concat->fasttext``).
``--concat-guesser`` plays each of the three codemasters (word2vec, fasttext,
concat) against a concatenated guesser. Concat vectors are
``[L2(word2vec) | L2(fasttext)]``.

Usage (from repo root):

    PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --seed 0
    PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --seeds 1,3,4,5
    PYTHONPATH=. python scripts/run_embedding_game.py \\
        --model data/model.bin \\
        --intersect-with data/embeddings/wiki.he.vec \\
        --play-both --seeds 0,1,2,3,4,5
    PYTHONPATH=. python scripts/run_embedding_game.py \\
        --model data/model.bin \\
        --intersect-with data/embeddings/wiki.he.vec \\
        --cross --seeds 0,1,2,3,4,5
    PYTHONPATH=. python scripts/run_embedding_game.py \\
        --model data/model.bin \\
        --intersect-with data/embeddings/wiki.he.vec \\
        --concat --seed 0
    PYTHONPATH=. python scripts/run_embedding_game.py \\
        --model data/model.bin \\
        --intersect-with data/embeddings/wiki.he.vec \\
        --concat-guesser --seed 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import WORDPOOLS, create_board, load_wordpool
from codenames.embedding_codemaster import DEFAULT_CANDIDATE_LIMIT, DEFAULT_THRESHOLD, EmbeddingCodemaster
from codenames.embedding_guesser import EmbeddingGuesser
from codenames.embeddings import (
    EmbeddingModel,
    Word2VecEmbeddings,
    concatenate_embeddings,
    in_vocab_wordpool_label,
    intersection_in_vocab,
    intersection_wordpool_label,
)
from codenames.game import SingleTeamGame
from codenames.logging_io import write_game_result

DEFAULT_MODEL_CANDIDATES = (
    REPO_ROOT / "data" / "model.bin",
    REPO_ROOT / "data" / "embeddings" / "model.bin",
)


def _default_model_path() -> Path:
    for path in DEFAULT_MODEL_CANDIDATES:
        if path.is_file():
            return path
    return DEFAULT_MODEL_CANDIDATES[0]


def _parse_seeds(seed: int, seeds: str | None) -> list[int]:
    if seeds:
        return [int(part.strip()) for part in seeds.split(",") if part.strip()]
    return [seed]


def play_one(
    cm_embeddings: EmbeddingModel,
    guesser_embeddings: EmbeddingModel,
    playable: list[str],
    label: str,
    seed: int,
    threshold: float,
    candidate_limit: int,
    do_print: bool,
    write_log: bool,
) -> None:
    board = create_board(seed=seed, wordpool=label, pool=playable)
    still_missing = cm_embeddings.missing(list(board.words)) + guesser_embeddings.missing(
        list(board.words)
    )
    if still_missing:
        raise RuntimeError(f"in-vocab board still has OOV: {still_missing}")

    result = SingleTeamGame(
        board,
        EmbeddingCodemaster(
            cm_embeddings,
            threshold=threshold,
            candidate_limit=candidate_limit,
            guesser_embeddings=guesser_embeddings,
        ),
        EmbeddingGuesser(guesser_embeddings),
        do_print=do_print,
    ).run()
    print(
        f"seed={seed}  cm={cm_embeddings.name}  guesser={guesser_embeddings.name}  "
        f"model={result.model}  wordpool={label}  threshold={threshold}  "
        f"outcome={result.outcome}  turns={result.num_turns}  score={result.score}"
    )
    if write_log:
        path = write_game_result(result)
        print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Single-team Codenames with embedding codemaster and guesser"
    )
    parser.add_argument("--model", type=Path, default=_default_model_path())
    parser.add_argument(
        "--name",
        default=None,
        help="Logged model id (word2vec / fasttext). Default: infer from filename.",
    )
    parser.add_argument(
        "--intersect-with",
        type=Path,
        default=None,
        help="Second embedding file; sample boards from the intersection vocab.",
    )
    parser.add_argument(
        "--intersect-name",
        default=None,
        help="Logged id for --intersect-with (default: infer from filename).",
    )
    parser.add_argument(
        "--play-both",
        action="store_true",
        help="With --intersect-with, also play same-model games using the second table.",
    )
    parser.add_argument(
        "--cross",
        action="store_true",
        help="With --intersect-with, play mixed games (each table as CM, the other as guesser).",
    )
    parser.add_argument(
        "--concat",
        action="store_true",
        help=(
            "With --intersect-with, play concat codemaster vs each single-table "
            "guesser (not concat-concat)."
        ),
    )
    parser.add_argument(
        "--concat-guesser",
        action="store_true",
        help=(
            "With --intersect-with, play each codemaster (word2vec, fasttext, "
            "concat) against a concatenated guesser."
        ),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma-separated seeds; loads the model once (e.g. 1,3,4,5)",
    )
    parser.add_argument("--wordpool", choices=WORDPOOLS, default="regular")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--candidate-limit", type=int, default=DEFAULT_CANDIDATE_LIMIT)
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print the board and each guess (still prints a one-line summary)",
    )
    args = parser.parse_args()

    if args.play_both and args.intersect_with is None:
        parser.error("--play-both requires --intersect-with")
    if args.cross and args.intersect_with is None:
        parser.error("--cross requires --intersect-with")
    if args.concat and args.intersect_with is None:
        parser.error("--concat requires --intersect-with")
    if args.concat_guesser and args.intersect_with is None:
        parser.error("--concat-guesser requires --intersect-with")

    embeddings = Word2VecEmbeddings.from_path(args.model, name=args.name)
    source = load_wordpool(args.wordpool)
    other: Word2VecEmbeddings | None = None
    if args.intersect_with is not None:
        other = Word2VecEmbeddings.from_path(
            args.intersect_with, name=args.intersect_name
        )
        playable = intersection_in_vocab(source, embeddings, other)
        label = intersection_wordpool_label(
            args.wordpool, [embeddings.name, other.name]
        )
        dropped = [word for word in source if word not in set(playable)]
    else:
        playable = embeddings.in_vocab(source)
        label = in_vocab_wordpool_label(args.wordpool, embeddings.name)
        dropped = embeddings.missing(source)

    print(
        f"source_wordpool={args.wordpool}  n={len(source)}  "
        f"playable={len(playable)}  dropped={len(dropped)}  logged_as={label}"
    )
    if dropped:
        print("Dropped OOV words (not removed from the CSV):")
        for word in dropped:
            print(f"  {word}")

    pairs: list[tuple[EmbeddingModel, EmbeddingModel]] = []
    concat_model = None
    if (args.concat or args.concat_guesser) and other is not None:
        concat_model = concatenate_embeddings(embeddings, other)
    if args.play_both and other is not None:
        pairs.append((embeddings, embeddings))
        pairs.append((other, other))
    if args.cross and other is not None:
        pairs.append((embeddings, other))
        pairs.append((other, embeddings))
    if args.concat and concat_model is not None:
        pairs.append((concat_model, embeddings))
        pairs.append((concat_model, other))
    if args.concat_guesser and concat_model is not None:
        pairs.append((embeddings, concat_model))
        pairs.append((other, concat_model))
        pairs.append((concat_model, concat_model))
    if not pairs:
        pairs.append((embeddings, embeddings))

    seed_list = _parse_seeds(args.seed, args.seeds)
    quiet = args.quiet or len(seed_list) > 1 or len(pairs) > 1
    for cm_model, guesser_model in pairs:
        print(f"Playing cm={cm_model.name} guesser={guesser_model.name}")
        for seed in seed_list:
            try:
                play_one(
                    cm_model,
                    guesser_model,
                    playable,
                    label,
                    seed,
                    args.threshold,
                    args.candidate_limit,
                    do_print=not quiet,
                    write_log=not args.no_log,
                )
            except RuntimeError as exc:
                print(
                    f"FAILED seed={seed}  cm={cm_model.name}  "
                    f"guesser={guesser_model.name}  {exc}"
                )


if __name__ == "__main__":
    main()
