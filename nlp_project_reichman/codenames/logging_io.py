"""Append-only experiment logging. Never overwrite a previous run file.

This branch writes under ``results/embedding/`` so transcripts are not mixed
with LLM / dummy logs from ``main`` or ``embeddings_method`` (those stayed in
``results/``).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from codenames.board import REPO_ROOT
from codenames.game import GameResult

RESULTS_DIR = REPO_ROOT / "results" / "embedding"
GAMES_JSONL = RESULTS_DIR / "games.jsonl"


SHIR_RESULTS_DIR = RESULTS_DIR / "shir"


def write_game_result(
    result: GameResult,
    results_dir: Path | None = None,
) -> Path:
    folder = results_dir or RESULTS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    filename = (
        f"single_team_seed{result.seed}_{result.wordpool}_"
        f"{result.codemaster}_{result.guesser}_{stamp}.json"
    )
    path = folder / filename
    payload = result.to_dict()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jsonl = folder / "games.jsonl"
    with jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path
