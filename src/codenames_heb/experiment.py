from dataclasses import asdict, dataclass
from typing import Any

from codenames_heb.board import Board
from codenames_heb.llm_client import FormatFailure
from codenames_heb.prompts.codemaster import (
    PROMPT_METHODS,
    parse_codemaster_response,
    validate_clue_legality,
)
from codenames_heb.prompts.guesser import build_guesser_prompt, parse_guesser_response


@dataclass
class LLMCodemaster:
    client: Any
    model: str
    method: str
    max_retries: int = 3

    def give_clue(self, board: Board, required_count: int | None = None) -> dict:
        build_prompt = PROMPT_METHODS[self.method]
        system, user = build_prompt(board, required_count)
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            try:
                data = self.client.complete_json(self.model, system, user, max_retries=1)
                response = parse_codemaster_response(data)
                validate_clue_legality(response.clue, board)
                return asdict(response)
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Codemaster {self.model}/{self.method} failed after "
            f"{self.max_retries} attempts: {last_error}"
        )


@dataclass
class LLMGuesser:
    client: Any
    model: str
    max_retries: int = 3

    def guess(self, words: list[str], clue: str, count: int) -> list[str]:
        system, user = build_guesser_prompt(words, clue, count)
        last_error: Exception | None = None
        for _ in range(self.max_retries):
            try:
                data = self.client.complete_json(self.model, system, user, max_retries=1)
                return parse_guesser_response(data)
            except (FormatFailure, ValueError) as exc:
                last_error = exc
                continue
        raise FormatFailure(
            f"Guesser {self.model} failed after {self.max_retries} attempts: {last_error}"
        )
