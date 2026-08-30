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
