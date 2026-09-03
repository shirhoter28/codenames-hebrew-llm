"""Hebrew Codenames clue validity.

Default rule set is ``v2``. The version string is logged on every game so a
later change is not confused with an older run.

v2 allows a clue if and only if:
- after stripping ends, it is a single token (no whitespace);
- the associated number is an integer >= 0;
- it is not exactly a remaining board word;
- it does not contain, and is not contained in, any remaining board word.

That last rule is the same containment check Stephenson et al. used in English.
It is a methodological choice: ``חתולים`` is illegal if ``חתול`` is still on
the board, and ``כדור`` is illegal if ``כדור-עף`` is still on the board.

This is not a full Hebrew morphological analyzer. Shared roots with no
substring overlap (e.g. some inflections) may still pass. Tightening further
would be a new version, not a silent edit of v2.
"""

from __future__ import annotations

from dataclasses import dataclass

VALIDITY_VERSION = "v2"
MAX_INVALID_CLUES = 10
FALLBACK_CLUE = ""
FALLBACK_CLUE_NUM = 1


@dataclass(frozen=True)
class ClueCheck:
    ok: bool
    reason: str
    clue: str
    clue_num: int
    version: str = VALIDITY_VERSION


def normalize_clue(clue: str) -> str:
    return (clue or "").strip()


def _overlaps_board_word(clue: str, word: str) -> bool:
    return clue == word or clue in word or word in clue


def check_clue(clue: str, clue_num: int, remaining_words: list[str]) -> ClueCheck:
    """Validate a candidate clue against remaining cards using rule set v2."""
    token = normalize_clue(clue)
    try:
        number = int(clue_num)
    except (TypeError, ValueError):
        return ClueCheck(False, "clue_num must be an integer", token, 0)

    if number < 0:
        return ClueCheck(False, "clue_num must be >= 0", token, number)
    if not token:
        return ClueCheck(False, "clue must be a non-empty token", token, number)
    if any(ch.isspace() for ch in token):
        return ClueCheck(False, "clue must be a single token (no whitespace)", token, number)
    for word in remaining_words:
        if _overlaps_board_word(token, word):
            if token == word:
                return ClueCheck(
                    False, "clue matches a remaining board word", token, number
                )
            return ClueCheck(
                False,
                f"clue overlaps remaining board word {word!r}",
                token,
                number,
            )
    return ClueCheck(True, "", token, number)
