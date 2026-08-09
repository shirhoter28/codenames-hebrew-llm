from dataclasses import dataclass

from codenames_heb.board import Board
from codenames_heb.prompts.rules import GAME_RULES


@dataclass(frozen=True)
class CodemasterResponse:
    clue: str
    count: int
    intended_targets: list[str]
    reasoning: str
    translation_map: dict[str, str] | None = None
    en_clue: str | None = None
    en_targets: list[str] | None = None


def _format_board_section(board: Board) -> str:
    return (
        f"YOUR_WORDS: {', '.join(board.words_with_role('target'))}\n"
        f"OPPONENT_WORDS: {', '.join(board.words_with_role('opponent'))}\n"
        f"CIVILIAN_WORDS: {', '.join(board.words_with_role('civilian'))}\n"
        f"ASSASSIN_WORD: {', '.join(board.words_with_role('assassin'))}"
    )


def _required_count_line(required_count: int | None) -> str:
    if required_count is None:
        return ""
    return f"\nYour clue must target exactly {required_count} words, chosen by you.\n"


_STRONG_HEBREW_TEMPLATE = """{game_rules}

You are an expert Codemaster in Codenames, playing in Hebrew.
{board_section}

Strict rules:
1. Clue must be exactly one valid Hebrew word — no phrases, no punctuation,
   not a word already on the board.
2. Clue must not be a morphological derivative/inflection of any board word
   (shared root or binyan that makes the link mechanical rather than semantic).
3. Before answering, check the clue's association strength against EVERY
   opponent, civilian, and assassin word — if any is as strongly or more
   strongly linked to the clue as your intended targets, pick a different
   clue or drop that target.
4. Only include a word in intended_targets if you're confident a guesser
   could find it from the clue alone with no other help.
{required_count_line}
Respond with JSON only: {{"clue": "...", "count": <int>,
"intended_targets": ["..."], "reasoning": "one sentence"}}"""


def build_strong_hebrew_prompt(
    board: Board, required_count: int | None = None
) -> tuple[str, str]:
    system = _STRONG_HEBREW_TEMPLATE.format(
        game_rules=GAME_RULES,
        board_section=_format_board_section(board),
        required_count_line=_required_count_line(required_count),
    )
    return system, "Provide your clue now."


_TRANSLATE_PIPELINE_TEMPLATE = """{game_rules}

You are an expert Codemaster in Codenames, playing in Hebrew.
{board_section}

First translate all board words to English internally. Think as a
Codemaster playing in English and choose your target words and English
clue. Then translate that English clue into one Hebrew word for your
final answer.
{required_count_line}
Respond with JSON only: {{"clue": "...", "count": <int>,
"intended_targets": ["..."], "reasoning": "...",
"translation_map": {{"he_word": "en_word", ...}},
"en_clue": "...", "en_targets": ["..."]}}"""


def build_translate_pipeline_prompt(
    board: Board, required_count: int | None = None
) -> tuple[str, str]:
    system = _TRANSLATE_PIPELINE_TEMPLATE.format(
        game_rules=GAME_RULES,
        board_section=_format_board_section(board),
        required_count_line=_required_count_line(required_count),
    )
    return system, "Provide your clue now."


PROMPT_METHODS = {
    "strong_hebrew": build_strong_hebrew_prompt,
    "translate_pipeline": build_translate_pipeline_prompt,
}


def parse_codemaster_response(data: dict) -> CodemasterResponse:
    required = {"clue", "count", "intended_targets", "reasoning"}
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


def validate_clue_legality(clue: str, board: Board) -> None:
    if any(ch.isspace() for ch in clue):
        raise ValueError(f"clue '{clue}' must be a single word")
    if clue in board.words:
        raise ValueError(f"clue '{clue}' must not be a word already on the board")
