"""Round-1 agreement: does a model repeat itself, and do models agree?

On round 1 `revealed` is empty, so `give_clue` receives an input fixed by
`(board_style, board_seed, model, method, count_constraint)` — the guesser
cannot have influenced it, and nothing in the prompt builders or `llm_client`
shuffles word order, sets a temperature, or seeds. The four guesser-runs of one
cell are therefore four draws from a byte-identical prompt, which makes round 1
a controlled replicate experiment.

Round 1 is also the ONLY such point: from round 2 the revealed set diverges with
the first differing guess, so any later matched state is both rare and
self-selected by the games that happened to agree.
"""

from __future__ import annotations

import re
from collections import Counter
from itertools import combinations

import pandas as pd

from codenames_heb.analysis import summarize

# Hebrew vocalization marks. Optional in the source and applied inconsistently,
# so they are formatting rather than lexical content.
_NIQQUD = re.compile(r"[֑-ׇ]")
# Whitespace, punctuation and maqaf. A one-word clue should carry none of it.
_PUNCT = re.compile(r"[\s־\-–—.,;:!?'\"()\[\]]+")
# Final forms are positional variants, so folding them cannot merge two
# genuinely different words.
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")


def normalize_clue(text) -> str:
    """Fold the spelling differences that are not disagreements.

    Deliberately does NOT strip the definite article: `הים` and `ים` are
    different words, and treating them as one would overstate agreement.
    """
    if not isinstance(text, str):
        return ""
    return _PUNCT.sub("", _NIQQUD.sub("", text)).translate(_FINALS)


# A replicate cell holds one model's draws from one identical prompt.
CELL_KEY = ["board_style", "board_seed", "model", "method", "count_constraint"]
# A panel pools the codemasters on one board. Method and floor are held fixed
# so a panel is a model contrast and not a method contrast; pass different
# columns to pool them.
PANEL_KEY = ["board_style", "board_seed", "method", "count_constraint"]


def first_rounds(rounds: pd.DataFrame) -> pd.DataFrame:
    """Round 1 only, with the comparison keys attached."""
    first = rounds[rounds["round"] == 1].copy()
    first["clue_norm"] = first["clue"].map(normalize_clue)
    first["target_set"] = first["intended_targets"].map(
        lambda t: frozenset(t) if isinstance(t, (list, tuple, set)) else frozenset()
    )
    return first


def _jaccard(left: frozenset, right: frozenset):
    union = left | right
    return len(left & right) / len(union) if union else None


def mean_pairwise_jaccard(sets) -> float | None:
    """Mean overlap of the target sets across draws.

    The load-bearing metric: it separates two instabilities that
    `n_distinct_clues` conflates. A model that varies its *wording* while
    aiming at the same words is behaving reasonably; one that varies *which
    words it aims at* has an unstable strategy.
    """
    scores = [s for s in (_jaccard(a, b) for a, b in combinations(sets, 2)) if s is not None]
    return sum(scores) / len(scores) if scores else None


def _keys_to_dict(columns, keys) -> dict:
    """groupby hands back a scalar for a single column and a tuple for many."""
    return dict(zip(columns, keys if isinstance(keys, tuple) else (keys,)))


def self_consistency(rounds: pd.DataFrame) -> pd.DataFrame:
    """One row per replicate cell: does this model repeat itself?"""
    first = first_rounds(rounds)
    records = []
    for keys, sub in first.groupby(CELL_KEY, dropna=False, observed=True):
        clues, sets = list(sub["clue_norm"]), list(sub["target_set"])
        records.append({
            **_keys_to_dict(CELL_KEY, keys),
            "n_draws": len(clues),
            "n_distinct_clues": len(set(clues)),
            "is_unanimous": float(len(set(clues)) == 1),
            "modal_share": Counter(clues).most_common(1)[0][1] / len(clues),
            "n_distinct_target_sets": len(set(sets)),
            "target_set_modal_share": Counter(sets).most_common(1)[0][1] / len(sets),
            "self_jaccard": mean_pairwise_jaccard(sets),
        })
    return pd.DataFrame(records)


_CONSISTENCY_METRICS = [
    "n_draws", "n_distinct_clues", "is_unanimous", "modal_share",
    "n_distinct_target_sets", "self_jaccard",
]


def self_consistency_summary(rounds: pd.DataFrame, group_cols=("model",)) -> pd.DataFrame:
    """Aggregate the cells. `is_unanimous` carries a Wilson interval."""
    cells = self_consistency(rounds)
    if cells.empty:
        return cells
    return summarize(cells, list(group_cols), _CONSISTENCY_METRICS,
                     proportions=["is_unanimous"])


def panel_agreement(rounds: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    """One row per board panel: do the codemasters converge?

    Pairs are restricted to DIFFERENT codemasters. Including same-codemaster
    pairs would fold self-consistency into the agreement number and inflate it
    for exactly the models that are most stable.
    """
    group_cols = list(group_cols or PANEL_KEY)
    first = first_rounds(rounds)
    records = []
    for keys, sub in first.groupby(group_cols, dropna=False, observed=True):
        draws = list(zip(sub["model"], sub["clue_norm"], sub["target_set"]))
        pairs = [(a, b) for a, b in combinations(draws, 2) if a[0] != b[0]]
        if not pairs:
            continue
        overlaps = [s for s in (_jaccard(a[2], b[2]) for a, b in pairs) if s is not None]
        clues = [clue for _, clue, _ in draws]
        modal_clue, modal_n = Counter(clues).most_common(1)[0]
        records.append({
            **_keys_to_dict(group_cols, keys),
            "n_draws": len(draws),
            "n_codemasters": len({m for m, _, _ in draws}),
            "n_distinct_clues": len(set(clues)),
            "n_cross_pairs": len(pairs),
            "pairwise_clue_agreement": sum(a[1] == b[1] for a, b in pairs) / len(pairs),
            "pairwise_target_jaccard": (sum(overlaps) / len(overlaps)) if overlaps else None,
            "consensus_clue": modal_clue,
            "consensus_share": modal_n / len(clues),
        })
    return pd.DataFrame(records)


def word_consensus(rounds: pd.DataFrame, boards: dict, group_cols=None) -> pd.DataFrame:
    """How often each board word is aimed at, per panel.

    A TARGET that no draw ever names is a consensus-hard word. Crossing that
    against `is_dual` tests whether ambiguity makes a word hard to CUE, which
    is the other half of the question `dual_miss_lift` asks about guessing.
    """
    group_cols = list(group_cols or PANEL_KEY)
    first = first_rounds(rounds)
    records = []
    for keys, sub in first.groupby(group_cols, dropna=False, observed=True):
        key = _keys_to_dict(group_cols, keys)
        board = boards.get((key.get("board_style"), key.get("board_seed")))
        if not board:
            continue
        picks = Counter(word for target_set in sub["target_set"] for word in target_set)
        for word, role in board["roles"].items():
            records.append({
                **key,
                "word": word,
                "role": role,
                "is_dual": float(bool((board.get("is_dual") or {}).get(word))),
                "n_draws": len(sub),
                "n_picks": picks.get(word, 0),
                "word_pick_rate": picks.get(word, 0) / len(sub),
            })
    out = pd.DataFrame(records)
    if out.empty:
        return out
    # Only a TARGET can be consensus-hard: a civilian nobody aims at is correct
    # play, not a word the models failed to find a link for.
    out["is_consensus_hard"] = (
        (out["role"] == "target") & (out["n_picks"] == 0)
    ).astype(float)
    return out


def consensus_hard_by_dual(consensus: pd.DataFrame) -> pd.DataFrame:
    """Are ambiguous target words harder to cue than unambiguous ones?"""
    if consensus.empty:
        return consensus
    targets = consensus[consensus["role"] == "target"]
    return summarize(targets, ["board_style", "is_dual"],
                     ["is_consensus_hard", "word_pick_rate"],
                     proportions=["is_consensus_hard"])
