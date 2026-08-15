from codenames_heb.board import ROLE_TAGS
from codenames_heb.prompts.rules import GAME_RULES

_SINGLE_GUESS_TEMPLATE = """{game_rules}

You are the Guesser in Codenames. Your Codemaster has given a clue and a
number for the current round. You guess one word at a time; each guess is
revealed immediately.

Clue: {clue}
Count: {count}
Already guessed correctly this round: {correct_so_far}
{revealed_section}
Remaining board words you may guess: {words}

{action_instructions}"""


def _format_correct_so_far(correct_so_far: list[str]) -> str:
    return ", ".join(correct_so_far) if correct_so_far else "(none yet)"


def _format_revealed_section(revealed: dict[str, str] | None) -> str:
    if not revealed:
        return ""
    revealed_line = ", ".join(f"{word} ({ROLE_TAGS[role]})" for word, role in revealed.items())
    return f"REVEALED_SO_FAR: {revealed_line}\n"


def build_single_guess_prompt(
    words: list[str],
    clue: str,
    count: int,
    correct_so_far: list[str],
    can_stop: bool,
    revealed: dict[str, str] | None = None,
) -> tuple[str, str]:
    if can_stop:
        action_instructions = (
            'Respond with JSON only: {"action": "guess", "word": "..."} to guess a word, '
            'or {"action": "stop"} to stop guessing for this round.'
        )
    else:
        action_instructions = (
            "You must guess at least once this round.\n"
            'Respond with JSON only: {"action": "guess", "word": "..."}'
        )
    system = _SINGLE_GUESS_TEMPLATE.format(
        game_rules=GAME_RULES,
        clue=clue,
        count=count,
        correct_so_far=_format_correct_so_far(correct_so_far),
        revealed_section=_format_revealed_section(revealed),
        words=", ".join(words),
        action_instructions=action_instructions,
    )
    return system, "Provide your next action now."


def parse_single_guess_response(data: dict) -> str | None:
    if "action" not in data:
        raise ValueError("guesser response must contain an 'action' key")
    action = data["action"]
    if action == "stop":
        return None
    if action == "guess":
        word = data.get("word")
        if not isinstance(word, str) or not word.strip():
            raise ValueError("'guess' action requires a non-empty 'word'")
        return word.strip()
    raise ValueError(f"unknown action: {action!r}")
