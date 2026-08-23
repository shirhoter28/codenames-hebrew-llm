from dataclasses import dataclass

from codenames_heb.board import ROLE_TAGS, Board
from codenames_heb.prompts.rules import GAME_RULES


@dataclass(frozen=True)
class CodemasterResponse:
    clue: str
    count: int
    intended_targets: list[str]
    # No longer requested in the prompt; kept so a volunteered one is not
    # thrown away, and so older runs stay loadable.
    reasoning: str = ""
    translation_map: dict[str, str] | None = None
    en_clue: str | None = None
    en_targets: list[str] | None = None


def _format_board_section(board: Board, revealed: dict[str, str] | None = None) -> str:
    revealed = revealed or {}

    def unrevealed(role: str) -> list[str]:
        return [w for w in board.words_with_role(role) if w not in revealed]

    # The opposing team's progress toward its own win. The codemaster can see
    # the key, so this is counted against the board's real opponent total
    # rather than the standard distribution.
    opponent_total = len(board.words_with_role("opponent"))
    opponent_gone = sum(1 for role in revealed.values() if role == "opponent")

    section = (
        f"YOUR_WORDS: {', '.join(unrevealed('target'))}\n"
        f"OPPONENT_WORDS: {', '.join(unrevealed('opponent'))}\n"
        f"CIVILIAN_WORDS: {', '.join(unrevealed('civilian'))}\n"
        f"ASSASSIN_WORD: {', '.join(unrevealed('assassin'))}\n"
        f"OPPONENT_PROGRESS: {opponent_gone} of {opponent_total} OPPONENT words "
        f"revealed — {opponent_total - opponent_gone} more and the opposing team wins."
    )
    if revealed:
        revealed_line = ", ".join(
            f"{word} ({ROLE_TAGS[role]})" for word, role in revealed.items()
        )
        section += f"\nREVEALED_SO_FAR: {revealed_line}"
    return section


def _required_count_line(required_count: int | None) -> str:
    """The clue-count floor, when this arm of the run imposes one.

    A floor rather than an exact requirement: it accepts any answer at or above
    the minimum, so it rejects less often — and rejections are the main cost of
    constraining a model far outside its usual behaviour (only 10% of rounds on
    the 08-19 grid used count >= 3 voluntarily).
    """
    if required_count is None:
        return ""
    return (
        f"\nYour clue must point to AT LEAST {required_count} of YOUR_WORDS, so "
        f"`count` must be {required_count} or more. A `count` of 0 does NOT "
        f"satisfy this — 0 means an unlimited-guess clue, not an ambitious one.\n"
    )


_STRONG_HEBREW_TEMPLATE = """{game_rules}

You are an expert Codemaster in Codenames, playing in Hebrew.
{board_section}

Strict rules:
1. Clue must be exactly one valid Hebrew word — no phrases, no punctuation,
   not a word already on the board. Before finalizing, compare your clue
   character-by-character against every word listed above (YOUR_WORDS,
   OPPONENT_WORDS, CIVILIAN_WORDS, ASSASSIN_WORD, and REVEALED_SO_FAR if
   present) — if it exactly matches any of them, you must pick a different
   clue.
2. Clue must not be a morphological derivative/inflection of any board word
   (shared root or binyan that makes the link mechanical rather than semantic).
3. Before answering, check the clue's association strength against EVERY
   opponent, civilian, and assassin word — if any is as strongly or more
   strongly linked to the clue as your intended targets, pick a different
   clue or drop that target.
4. Only include a word in intended_targets if you're confident a guesser
   could find it from the clue alone with no other help. Every word in
   intended_targets must be copied exactly, character-for-character, from
   YOUR_WORDS above — never a related or synonymous word that merely sounds
   right.
5. `count` must equal exactly the number of words in `intended_targets` —
   no more, no fewer.
{required_count_line}
Respond with JSON only: {{"clue": "...", "count": <int>,
"intended_targets": ["..."]}}"""


def build_strong_hebrew_prompt(
    board: Board, required_count: int | None = None, revealed: dict[str, str] | None = None
) -> tuple[str, str]:
    system = _STRONG_HEBREW_TEMPLATE.format(
        game_rules=GAME_RULES,
        board_section=_format_board_section(board, revealed),
        required_count_line=_required_count_line(required_count),
    )
    return system, "Provide your clue now."


_TRANSLATE_PIPELINE_TEMPLATE = """{game_rules}

You are an expert Codemaster in Codenames, playing in Hebrew.
{board_section}

First translate all board words to English internally. Think as a
Codemaster playing in English and choose your target words and English
clue. Then translate that English clue into one Hebrew word for your
final answer. Before finalizing, compare your final Hebrew clue
character-by-character against every word listed above (YOUR_WORDS,
OPPONENT_WORDS, CIVILIAN_WORDS, ASSASSIN_WORD, and REVEALED_SO_FAR if
present) — if it exactly matches any of them, pick a different clue. Every
word in intended_targets must be copied exactly, character-for-character,
from YOUR_WORDS above. `count` must equal exactly the number of words in
`intended_targets` — no more, no fewer.
{required_count_line}
Answer in this key order — the translation work comes first, and the
Hebrew clue last, so that each field is derived from the ones above it.
Respond with JSON only: {{"translation_map": {{"he_word": "en_word", ...}},
"en_targets": ["..."], "en_clue": "...",
"intended_targets": ["..."], "count": <int>, "clue": "..."}}"""


def build_translate_pipeline_prompt(
    board: Board, required_count: int | None = None, revealed: dict[str, str] | None = None
) -> tuple[str, str]:
    system = _TRANSLATE_PIPELINE_TEMPLATE.format(
        game_rules=GAME_RULES,
        board_section=_format_board_section(board, revealed),
        required_count_line=_required_count_line(required_count),
    )
    return system, "Provide your clue now."


PROMPT_METHODS = {
    "strong_hebrew": build_strong_hebrew_prompt,
    "translate_pipeline": build_translate_pipeline_prompt,
}


def parse_codemaster_response(data: dict) -> CodemasterResponse:
    required = {"clue", "count", "intended_targets"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Codemaster response missing keys: {missing}")
    if not isinstance(data["clue"], str) or not data["clue"].strip():
        raise ValueError("clue must be a non-empty string")
    if not isinstance(data["count"], int) or isinstance(data["count"], bool) or data["count"] < 0:
        raise ValueError("count must be a non-negative integer")
    if not isinstance(data["intended_targets"], list):
        raise ValueError("intended_targets must be a list")
    return CodemasterResponse(
        clue=data["clue"].strip(),
        count=data["count"],
        intended_targets=[str(word).strip() for word in data["intended_targets"]],
        reasoning=str(data.get("reasoning", "")),
        translation_map=data.get("translation_map"),
        en_clue=data.get("en_clue"),
        en_targets=data.get("en_targets"),
    )


def build_correction_note(
    error: str, board: Board, revealed: dict[str, str] | None = None,
    required_count: int | None = None,
) -> str:
    """Text appended to the user prompt when re-asking after a rejection.

    Without this, a retry re-sends the identical prompt and the model has no
    reason to answer differently — observed in the 2026-08-16 pilot, where
    all retries failed with the same error as the first attempt. The floor is
    restated for the same reason: a rejection for missing it, answered by a
    note that never mentions it, is the identical failure.
    """
    revealed = revealed or {}
    available_targets = [w for w in board.words_with_role("target") if w not in revealed]
    floor_line = (
        f"- Your clue must point to at least {required_count} words: `count` must "
        f"be {required_count} or more, and never 0.\n"
        if required_count is not None
        else ""
    )
    return (
        "\n\nYOUR PREVIOUS RESPONSE WAS REJECTED.\n"
        f"Reason: {error}\n\n"
        "Fix exactly that problem and answer again. Reminders:\n"
        f"- Your clue must NOT be any of these board words: {', '.join(board.words)}\n"
        "- Every entry in intended_targets must be copied exactly, "
        f"character-for-character, from: {', '.join(available_targets)}\n"
        "- count must equal exactly the number of entries in intended_targets.\n"
        f"{floor_line}"
        "Respond with valid JSON only, in the format given above."
    )


def validate_clue_legality(clue: str, board: Board) -> None:
    if any(ch.isspace() for ch in clue):
        raise ValueError(f"clue '{clue}' must be a single word")
    if clue in board.words:
        raise ValueError(f"clue '{clue}' must not be a word already on the board")
