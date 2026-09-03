"""Print short recaps of embedding game JSON (UTF-8). Prefer the notebook for Hebrew."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from codenames.logging_io import RESULTS_DIR


def load_embedding_games(results_dir: Path | None = None) -> list[dict]:
    folder = results_dir or RESULTS_DIR
    games: list[dict] = []
    for path in sorted(folder.glob("single_team_*_embedding_embedding_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_path"] = str(path)
        games.append(payload)
    return games


def _condition_key(game: dict) -> tuple:
    params = game.get("model_params") or {}
    return (
        game.get("model"),
        game.get("seed"),
        params.get("threshold"),
        game.get("wordpool"),
        params.get("codemaster_model"),
        params.get("guesser_model"),
    )


def latest_per_condition(games: list[dict]) -> list[dict]:
    """If the same condition was replayed, keep the newest file."""
    best: dict[tuple, dict] = {}
    for game in games:
        key = _condition_key(game)
        prev = best.get(key)
        if prev is None or game.get("_path", "") > prev.get("_path", ""):
            best[key] = game
    return list(best.values())


def wrong_count(game: dict) -> int:
    return sum(
        1
        for turn in game.get("turns") or []
        for guess in turn.get("guesses") or []
        if not guess.get("correct")
    )


def format_game_recap(game: dict) -> str:
    params = game.get("model_params") or {}
    wrong = wrong_count(game)
    assassin = "yes" if game.get("assassin_revealed") else "no"
    header = (
        f"--- {game.get('model')}  seed={game.get('seed')}  "
        f"threshold={params.get('threshold')}  "
        f"outcome={game.get('outcome')}  turns={game.get('num_turns')}  "
        f"wrong={wrong}  assassin={assassin}"
    )
    lines = [header]
    for turn in game.get("turns") or []:
        targets = ", ".join(turn.get("parsed_targets") or [])
        guesses = ", ".join(
            f"{g['word']}({g['role']})" for g in turn.get("guesses") or []
        )
        min_t = turn.get("min_target")
        max_b = turn.get("max_bad")
        min_s = f"{min_t:.3f}" if isinstance(min_t, (int, float)) else str(min_t)
        max_s = f"{max_b:.3f}" if isinstance(max_b, (int, float)) else str(max_b)
        lines.append(
            f"  {turn.get('clue')} {turn.get('clue_num')}  "
            f"min_t={min_s}  max_bad={max_s}  "
            f"targets=[{targets}]  guesses=[{guesses}]"
        )
    return "\n".join(lines)


def select_games(
    games: list[dict],
    *,
    seeds: list[int] | None = None,
    wordpool: str | None = None,
    threshold: float | None = None,
) -> list[dict]:
    selected = latest_per_condition(games)
    if seeds is not None:
        seed_set = set(seeds)
        selected = [g for g in selected if g.get("seed") in seed_set]
    if wordpool is not None:
        selected = [g for g in selected if g.get("wordpool") == wordpool]
    if threshold is not None:
        selected = [
            g
            for g in selected
            if (g.get("model_params") or {}).get("threshold") == threshold
        ]
    return selected


def overview_rows(games: list[dict]) -> list[dict]:
    rows = []
    for game in sorted(
        games,
        key=lambda g: (str(g.get("model")), int(g.get("seed") or 0)),
    ):
        params = game.get("model_params") or {}
        rows.append(
            {
                "model": game.get("model"),
                "seed": game.get("seed"),
                "threshold": params.get("threshold"),
                "outcome": game.get("outcome"),
                "turns": game.get("num_turns"),
                "wrong": wrong_count(game),
                "assassin": bool(game.get("assassin_revealed")),
                "clue_ns": ",".join(
                    str(t["clue_num"]) for t in game.get("turns") or []
                ),
            }
        )
    return rows


def turn_rows(games: list[dict]) -> list[dict]:
    rows = []
    for game in sorted(
        games, key=lambda g: int(g.get("seed") or 0)
    ):
        for turn in game.get("turns") or []:
            min_t = turn.get("min_target")
            max_b = turn.get("max_bad")
            rows.append(
                {
                    "seed": game.get("seed"),
                    "turn": turn.get("turn"),
                    "clue": turn.get("clue"),
                    "n": turn.get("clue_num"),
                    "targets": ", ".join(turn.get("parsed_targets") or []),
                    "guesses": ", ".join(
                        f"{g['word']} ({g['role']})"
                        for g in turn.get("guesses") or []
                    ),
                    "min_t": round(min_t, 3)
                    if isinstance(min_t, (int, float))
                    else min_t,
                    "max_bad": round(max_b, 3)
                    if isinstance(max_b, (int, float))
                    else max_b,
                }
            )
    return rows


OFFICIAL_MODELS = (
    "word2vec",
    "fasttext",
    "word2vec->fasttext",
    "fasttext->word2vec",
    "concat->fasttext",
    "concat->word2vec",
    "word2vec->concat",
    "fasttext->concat",
    "concat->concat",
)
BOARD_TYPES = ("regular", "dual", "union")
OFFICIAL_SEEDS = list(range(30))
OFFICIAL_EXPECTED = len(OFFICIAL_MODELS) * len(BOARD_TYPES) * len(OFFICIAL_SEEDS)
INTERSECTION_MARK = "_in_vocab_intersection_fasttext_word2vec"
METHOD_LABELS = {
    "word2vec": "W2V→W2V",
    "fasttext": "FT→FT",
    "word2vec->fasttext": "W2V→FT",
    "fasttext->word2vec": "FT→W2V",
    "concat->fasttext": "concat→FT",
    "concat->word2vec": "concat→W2V",
    "word2vec->concat": "W2V→concat",
    "fasttext->concat": "FT→concat",
    "concat->concat": "concat→concat",
}


def board_type_from_wordpool(wordpool: str) -> str | None:
    for name in BOARD_TYPES:
        if wordpool.startswith(f"{name}_"):
            return name
    return None


def official_series(
    games: list[dict],
    *,
    seeds: list[int] | None = None,
    threshold: float = 0.4,
    candidate_limit: int = 20_000,
) -> list[dict]:
    """Official set: intersection boards, locked threshold, nine methods, seeds 0–29."""
    selected = select_games(
        games,
        seeds=seeds if seeds is not None else OFFICIAL_SEEDS,
        threshold=threshold,
    )
    out: list[dict] = []
    for game in selected:
        wordpool = game.get("wordpool") or ""
        if INTERSECTION_MARK not in wordpool:
            continue
        board = board_type_from_wordpool(wordpool)
        if board not in BOARD_TYPES:
            continue
        if game.get("model") not in OFFICIAL_MODELS:
            continue
        params = game.get("model_params") or {}
        if params.get("candidate_limit") not in (None, candidate_limit):
            continue
        row = {
            "model": game.get("model"),
            "method": METHOD_LABELS.get(str(game.get("model")), game.get("model")),
            "board": board,
            "seed": game.get("seed"),
            "wordpool": wordpool,
            "outcome": game.get("outcome"),
            "turns": game.get("num_turns"),
            "wrong": wrong_count(game),
            "assassin": bool(game.get("assassin_revealed")),
            "win": game.get("outcome") == "win",
            "mean_clue_n": (
                sum(t["clue_num"] for t in game.get("turns") or [])
                / max(len(game.get("turns") or []), 1)
            ),
        }
        if row["win"]:
            row["loss_kind"] = "win"
        elif row["assassin"] or game.get("outcome") == "assassin":
            row["loss_kind"] = "assassin"
        else:
            row["loss_kind"] = "other_loss"
        out.append(row)
    return out


def print_recaps(
    games: list[dict],
    *,
    seeds: list[int] | None = None,
    wordpool: str | None = None,
    threshold: float | None = None,
) -> None:
    selected = select_games(
        games, seeds=seeds, wordpool=wordpool, threshold=threshold
    )

    by_type: dict[str, list[dict]] = defaultdict(list)
    for game in selected:
        by_type[str(game.get("model"))].append(game)

    for model_name in sorted(by_type):
        batch = sorted(by_type[model_name], key=lambda g: int(g.get("seed") or 0))
        print(f"\n======== {model_name}  ({len(batch)} games) ========")
        for game in batch:
            print(format_game_recap(game))
            print()


SHIR_STYLES = ("dual_0", "natural", "dual_100")
SHIR_EXPECTED = len(OFFICIAL_MODELS) * len(SHIR_STYLES) * 30
SHIR_STYLE_LABELS = {
    "dual_0": "dual_0 (no dual)",
    "natural": "natural mix",
    "dual_100": "dual_100 (all dual)",
}


def shir_style_from_wordpool(wordpool: str) -> str | None:
    if not wordpool.startswith("shir_"):
        return None
    style = wordpool.removeprefix("shir_")
    return style if style in SHIR_STYLES else None


def shir_series(
    games: list[dict],
    *,
    threshold: float = 0.4,
    candidate_limit: int = 20_000,
) -> list[dict]:
    """Shir fixed boards, nine methods, OOV policy shir_v1."""
    selected = select_games(games, threshold=threshold)
    out: list[dict] = []
    for game in selected:
        style = shir_style_from_wordpool(game.get("wordpool") or "")
        if style is None:
            continue
        if game.get("model") not in OFFICIAL_MODELS:
            continue
        params = game.get("model_params") or {}
        if params.get("candidate_limit") not in (None, candidate_limit):
            continue
        if params.get("oov_policy") not in (None, "shir_v1"):
            continue
        outcome = game.get("outcome")
        win = outcome == "win"
        if outcome == "oov_loss":
            loss_kind = "oov_loss"
        elif win:
            loss_kind = "unfair_win" if params.get("assassin_oov_unfair") else "win"
        elif game.get("assassin_revealed") or outcome == "assassin":
            loss_kind = "assassin"
        else:
            loss_kind = "other_loss"
        turns_list = game.get("turns") or []
        out.append(
            {
                "model": game.get("model"),
                "method": METHOD_LABELS.get(str(game.get("model")), game.get("model")),
                "board": style,
                "seed": game.get("seed"),
                "wordpool": game.get("wordpool"),
                "outcome": outcome,
                "turns": game.get("num_turns"),
                "wrong": wrong_count(game),
                "assassin": bool(game.get("assassin_revealed")),
                "win": win,
                "fair_win": win and not params.get("assassin_oov_unfair"),
                "oov_red_loss": bool(params.get("oov_red_loss")),
                "assassin_oov_unfair": bool(params.get("assassin_oov_unfair")),
                "oov_blue": bool(params.get("oov_blue")),
                "oov_civilian": bool(params.get("oov_civilian")),
                "oov_words": ",".join(params.get("oov_words") or []),
                "loss_kind": loss_kind,
                "mean_clue_n": (
                    sum(t["clue_num"] for t in turns_list) / max(len(turns_list), 1)
                ),
            }
        )
    return out
