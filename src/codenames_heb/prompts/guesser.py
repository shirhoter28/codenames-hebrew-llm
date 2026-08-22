from codenames_heb.board import ROLE_TAGS
from codenames_heb.prompts.rules import GAME_RULES

_SINGLE_GUESS_TEMPLATE = """{game_rules}

You are the Guesser in Codenames. Your Codemaster has given a clue and a
number for the current round. You guess one word at a time; each guess is
revealed immediately.

Clue: {clue}
Count: {count}
Already guessed correctly this round: {correct_so_far}
{budget_line}
{revealed_section}
Remaining board words you may guess: {words}

If you guess, "word" must be copied exactly, character-for-character, from
the "Remaining board words you may guess" list above — never a related,
synonymous, or associated word that isn't in that exact list, even if it
feels like a better match for the clue. If your best association isn't in
the list, pick the closest word that IS in the list.

{action_instructions}"""


def _format_correct_so_far(correct_so_far: list[str]) -> str:
    return ", ".join(correct_so_far) if correct_so_far else "(none yet)"


def _format_budget_line(count: int, correct_so_far: list[str]) -> str:
    """State the guess budget explicitly every turn.

    The rules block already defines it, but a model asked for one guess at a
    time can't see how much of the budget it has spent — and reads the
    clue's number as a quota it owes rather than a ceiling it may stop under.
    """
    used = len(correct_so_far)
    if count == 0:
        return f"Guesses used this round: {used} (a clue of 0 sets no guess limit)"
    return (
        f"Guesses used this round: {used} of at most {count + 1} "
        f"(the clue's number, plus one bonus guess)"
    )


def _format_revealed_section(revealed: dict[str, str] | None) -> str:
    """What has been turned over, and how close the opposing team is to winning.

    The guesser never sees the key, so it cannot be told how many OPPONENT
    words the board holds — only how many have surfaced. The total is in
    GAME_RULES; printing one here would be a guess that a non-standard board
    would make wrong.
    """
    if not revealed:
        return ""
    revealed_line = ", ".join(f"{word} ({ROLE_TAGS[role]})" for word, role in revealed.items())
    opponent_gone = sum(1 for role in revealed.values() if role == "opponent")
    return (
        f"REVEALED_SO_FAR: {revealed_line}\n"
        f"OPPONENT_PROGRESS: {opponent_gone} OPPONENT words revealed so far — the "
        f"opposing team wins the moment all of theirs are.\n"
    )


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
            "Your guess budget above is a ceiling, not a quota: you do not "
            "have to use all of it. "
            "If you have already found the words this clue points to, or you "
            "are not confident that another word fits it, stopping is the "
            "better move — a wrong guess ends the round and may hit the "
            "ASSASSIN, which loses the game outright.\n"
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
        budget_line=_format_budget_line(count, correct_so_far),
        revealed_section=_format_revealed_section(revealed),
        words=", ".join(words),
        action_instructions=action_instructions,
    )
    return system, "Provide your next action now."


def build_correction_note(error: str, words: list[str], can_stop: bool) -> str:
    """Text appended to the user prompt when re-asking after a rejection.

    Without this, a retry re-sends the identical prompt and the model has no
    reason to answer differently — observed in the 2026-08-16 pilot, where a
    guesser named the same off-board word on all three attempts.
    """
    actions = (
        '{"action": "guess", "word": "..."} or {"action": "stop"}'
        if can_stop
        else '{"action": "guess", "word": "..."}'
    )
    return (
        "\n\nYOUR PREVIOUS RESPONSE WAS REJECTED.\n"
        f"Reason: {error}\n\n"
        "Fix exactly that problem and answer again. Your guess must be one of "
        "these words, copied exactly character-for-character — no synonyms, no "
        "related words, nothing outside this list:\n"
        f"{', '.join(words)}\n"
        f"Respond with valid JSON only: {actions}"
    )


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
