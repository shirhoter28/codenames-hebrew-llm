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


# --- Fix 3: intended_targets must be words the codemaster was actually given ---


def test_llm_codemaster_retries_when_intended_target_is_not_a_target_word():
    # "ב" is on the board, but it's an OPPONENT word — it was never in YOUR_WORDS.
    client = FakeClient(
        [
            {"clue": "אור", "count": 1, "intended_targets": ["ב"], "reasoning": "r"},
            {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    result = codemaster.give_clue(_board())

    assert result["intended_targets"] == ["ירח"]
    assert len(client.calls) == 2


def test_llm_codemaster_retries_when_intended_target_is_off_board_entirely():
    client = FakeClient(
        [
            {"clue": "אור", "count": 1, "intended_targets": ["שמש"], "reasoning": "r"},
            {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    assert codemaster.give_clue(_board())["intended_targets"] == ["ירח"]
    assert len(client.calls) == 2


def test_llm_codemaster_gives_up_and_names_the_offending_targets():
    bad = {"clue": "אור", "count": 1, "intended_targets": ["שמש"], "reasoning": "r"}
    client = FakeClient([bad, bad, bad])
    codemaster = LLMCodemaster(
        client=client, model="m", method="strong_hebrew", max_retries=3
    )

    with pytest.raises(FormatFailure) as excinfo:
        codemaster.give_clue(_board())

    assert "intended_targets not on board" in str(excinfo.value)
    assert "שמש" in str(excinfo.value)
    assert len(client.calls) == 3


def test_llm_codemaster_accepts_empty_intended_targets():
    client = FakeClient(
        [{"clue": "אור", "count": 0, "intended_targets": [], "reasoning": "r"}]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    assert codemaster.give_clue(_board())["intended_targets"] == []


# --- Fix 4: duplicate guesses are rejected ---


def test_llm_guesser_retries_on_duplicate_guesses_then_succeeds():
    client = FakeClient(
        [
            {"guesses": ["ירח", "ירח", "ירח"]},
            {"guesses": ["ירח", "ב"]},
        ]
    )
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess(["ירח", "ב", "ג"], clue="אור", count=1)

    assert result == ["ירח", "ב"]
    assert len(client.calls) == 2


def test_llm_guesser_gives_up_on_duplicates_and_names_them():
    client = FakeClient([{"guesses": ["ירח", "ירח"]}] * 3)
    guesser = LLMGuesser(client=client, model="m", max_retries=3)

    with pytest.raises(FormatFailure) as excinfo:
        guesser.guess(["ירח", "ב", "ג"], clue="אור", count=1)

    assert "duplicate guesses" in str(excinfo.value)
    assert len(client.calls) == 3


# --- Fix 6: raw_response propagates up through the adapter retry loops ---


def test_llm_codemaster_propagates_raw_response_from_underlying_failure():
    client = FakeClient([FormatFailure("no json", raw_response="model said this")] * 3)
    codemaster = LLMCodemaster(
        client=client, model="m", method="strong_hebrew", max_retries=3
    )

    with pytest.raises(FormatFailure) as excinfo:
        codemaster.give_clue(_board())

    assert excinfo.value.raw_response == "model said this"


def test_llm_guesser_propagates_raw_response_from_underlying_failure():
    client = FakeClient([FormatFailure("no json", raw_response="guesser said this")] * 3)
    guesser = LLMGuesser(client=client, model="m", max_retries=3)

    with pytest.raises(FormatFailure) as excinfo:
        guesser.guess(["ירח"], clue="אור", count=1)

    assert excinfo.value.raw_response == "guesser said this"


def test_llm_guesser_raw_response_is_none_for_local_validation_failure():
    # An off-board guess is a local ValueError; there is no separate raw text,
    # but the message already names the offending values.
    client = FakeClient([{"guesses": ["not_on_board"]}] * 3)
    guesser = LLMGuesser(client=client, model="m", max_retries=3)

    with pytest.raises(FormatFailure) as excinfo:
        guesser.guess(["ירח"], clue="אור", count=1)

    assert excinfo.value.raw_response is None
    assert "guesses not on board" in str(excinfo.value)
    assert "not_on_board" in str(excinfo.value)
