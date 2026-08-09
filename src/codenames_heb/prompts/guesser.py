from codenames_heb.prompts.rules import GAME_RULES

_GUESSER_TEMPLATE = """{game_rules}

You are the Guesser in Codenames. Given the board and a clue+count from
your Codemaster, choose up to {max_guesses_desc} words you believe the
clue points to, ranked most-to-least confident.

Board words: {words}
Clue: {clue}
Count: {count}

Respond with JSON only: {{"guesses": ["...", ...]}}"""


def build_guesser_prompt(words: list[str], clue: str, count: int) -> tuple[str, str]:
    max_desc = "an unlimited number of" if count == 0 else f"{count + 1}"
    system = _GUESSER_TEMPLATE.format(
        game_rules=GAME_RULES,
        max_guesses_desc=max_desc,
        words=", ".join(words),
        clue=clue,
        count=count,
    )
    return system, "Provide your guesses now."


def parse_guesser_response(data: dict) -> list[str]:
    if "guesses" not in data or not isinstance(data["guesses"], list):
        raise ValueError("guesser response must contain a 'guesses' list")
    return [str(word).strip() for word in data["guesses"]]
