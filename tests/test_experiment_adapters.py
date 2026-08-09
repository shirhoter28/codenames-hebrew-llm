import pytest

from codenames_heb.board import Board
from codenames_heb.experiment import LLMCodemaster, LLMGuesser
from codenames_heb.llm_client import FormatFailure


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete_json(self, model, system_prompt, user_prompt, max_retries=1):
        self.calls.append((model, system_prompt, user_prompt))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _board() -> Board:
    return Board(
        seed=1,
        words=["ירח", "ב", "ג", "ד"],
        roles={"ירח": "target", "ב": "opponent", "ג": "civilian", "ד": "assassin"},
    )


def test_llm_codemaster_returns_parsed_response_on_first_try():
    client = FakeClient(
        [
            {
                "clue": "אור",
                "count": 1,
                "intended_targets": ["ירח"],
                "reasoning": "r",
            }
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    result = codemaster.give_clue(_board())

    assert result["clue"] == "אור"
    assert result["intended_targets"] == ["ירח"]
    assert len(client.calls) == 1


def test_llm_codemaster_retries_on_invalid_schema_then_succeeds():
    client = FakeClient(
        [
            {"clue": "אור"},  # missing required keys
            {
                "clue": "אור",
                "count": 1,
                "intended_targets": ["ירח"],
                "reasoning": "r",
            },
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    result = codemaster.give_clue(_board())

    assert result["clue"] == "אור"
    assert len(client.calls) == 2


def test_llm_codemaster_retries_on_illegal_clue_then_gives_up():
    client = FakeClient(
        [
            {"clue": "ירח", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
            {"clue": "ירח", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
            {"clue": "ירח", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(
        client=client, model="m", method="strong_hebrew", max_retries=3
    )

    with pytest.raises(FormatFailure):
        codemaster.give_clue(_board())

    assert len(client.calls) == 3


def test_llm_guesser_returns_parsed_guesses():
    client = FakeClient([{"guesses": ["ירח", "ב"]}])
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess(["ירח", "ב", "ג"], clue="אור", count=1)

    assert result == ["ירח", "ב"]


def test_llm_guesser_retries_when_guess_is_not_on_board_then_succeeds():
    client = FakeClient(
        [
            {"guesses": ["not_on_board"]},
            {"guesses": ["ירח"]},
        ]
    )
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess(["ירח", "ב", "ג"], clue="אור", count=1)

    assert result == ["ירח"]
    assert len(client.calls) == 2


def test_llm_guesser_raises_format_failure_after_retries():
    client = FakeClient([FormatFailure("bad"), FormatFailure("bad"), FormatFailure("bad")])
    guesser = LLMGuesser(client=client, model="m", max_retries=3)

    with pytest.raises(FormatFailure):
        guesser.guess(["ירח"], clue="אור", count=1)
