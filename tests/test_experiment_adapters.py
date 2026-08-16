from collections import Counter

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


def test_llm_guesser_returns_first_guess():
    client = FakeClient([{"action": "guess", "word": "ירח"}])
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess_one(["ירח", "ב", "ג"], clue="אור", count=1, correct_so_far=[])

    assert result == "ירח"


def test_llm_guesser_returns_none_on_stop_when_allowed():
    client = FakeClient([{"action": "stop"}])
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess_one(
        ["ב", "ג"], clue="אור", count=2, correct_so_far=["ירח"]
    )

    assert result is None


def test_llm_guesser_retries_when_stopping_before_first_guess():
    client = FakeClient(
        [
            {"action": "stop"},
            {"action": "guess", "word": "ירח"},
        ]
    )
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess_one(["ירח", "ב", "ג"], clue="אור", count=1, correct_so_far=[])

    assert result == "ירח"
    assert len(client.calls) == 2


def test_llm_guesser_retries_when_guess_is_not_on_board_then_succeeds():
    client = FakeClient(
        [
            {"action": "guess", "word": "not_on_board"},
            {"action": "guess", "word": "ירח"},
        ]
    )
    guesser = LLMGuesser(client=client, model="m")

    result = guesser.guess_one(["ירח", "ב", "ג"], clue="אור", count=1, correct_so_far=[])

    assert result == "ירח"
    assert len(client.calls) == 2


def test_llm_guesser_raises_format_failure_after_retries():
    client = FakeClient([FormatFailure("bad"), FormatFailure("bad"), FormatFailure("bad")])
    guesser = LLMGuesser(client=client, model="m", max_retries=3)

    with pytest.raises(FormatFailure):
        guesser.guess_one(["ירח"], clue="אור", count=1, correct_so_far=[])


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


def test_llm_codemaster_retries_when_intended_target_already_revealed():
    # "ירח" is a real target word but it's already been found this game —
    # it can't be re-targeted.
    client = FakeClient(
        [
            {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
            {"clue": "אור", "count": 0, "intended_targets": [], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    result = codemaster.give_clue(_board(), revealed={"ירח": "target"})

    assert result["intended_targets"] == []
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


# --- count must equal len(intended_targets) ---


def test_llm_codemaster_retries_when_count_exceeds_intended_targets():
    client = FakeClient(
        [
            {"clue": "אור", "count": 2, "intended_targets": ["ירח"], "reasoning": "r"},
            {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    result = codemaster.give_clue(_board())

    assert result["count"] == 1
    assert len(client.calls) == 2


def test_llm_codemaster_gives_up_when_count_mismatches_intended_targets():
    bad = {"clue": "אור", "count": 3, "intended_targets": ["ירח"], "reasoning": "r"}
    client = FakeClient([bad, bad, bad])
    codemaster = LLMCodemaster(
        client=client, model="m", method="strong_hebrew", max_retries=3
    )

    with pytest.raises(FormatFailure) as excinfo:
        codemaster.give_clue(_board())

    assert "count 3 != len(intended_targets) 1" in str(excinfo.value)
    assert len(client.calls) == 3


# --- Fix 7: duplicate intended_targets are rejected (mirrors Fix 4 for guesses) ---


def _board_two_targets() -> Board:
    return Board(
        seed=1,
        words=["ירח", "שמש", "ג", "ד"],
        roles={"ירח": "target", "שמש": "target", "ג": "civilian", "ד": "assassin"},
    )


def test_llm_codemaster_retries_on_duplicate_intended_targets_then_succeeds():
    client = FakeClient(
        [
            {
                "clue": "אור",
                "count": 2,
                "intended_targets": ["ירח", "ירח"],
                "reasoning": "r",
            },
            {
                "clue": "אור",
                "count": 2,
                "intended_targets": ["ירח", "שמש"],
                "reasoning": "r",
            },
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    result = codemaster.give_clue(_board_two_targets())

    assert result["intended_targets"] == ["ירח", "שמש"]
    assert len(client.calls) == 2


def test_llm_codemaster_gives_up_on_duplicate_intended_targets_and_names_them():
    bad = {
        "clue": "אור",
        "count": 2,
        "intended_targets": ["ירח", "ירח"],
        "reasoning": "r",
    }
    client = FakeClient([bad, bad, bad])
    codemaster = LLMCodemaster(
        client=client, model="m", method="strong_hebrew", max_retries=3
    )

    with pytest.raises(FormatFailure) as excinfo:
        codemaster.give_clue(_board_two_targets())

    assert "duplicate intended_targets" in str(excinfo.value)
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
        guesser.guess_one(["ירח"], clue="אור", count=1, correct_so_far=[])

    assert excinfo.value.raw_response == "guesser said this"


def test_llm_guesser_raw_response_is_none_for_local_validation_failure():
    # An off-board guess is a local ValueError; there is no separate raw text,
    # but the message already names the offending value.
    client = FakeClient([{"action": "guess", "word": "not_on_board"}] * 3)
    guesser = LLMGuesser(client=client, model="m", max_retries=3)

    with pytest.raises(FormatFailure) as excinfo:
        guesser.guess_one(["ירח"], clue="אור", count=1, correct_so_far=[])

    assert excinfo.value.raw_response is None
    assert "not among currently guessable words" in str(excinfo.value)
    assert "not_on_board" in str(excinfo.value)


# --- Corrective retries: a rejected attempt is re-asked WITH the reason ---


def test_llm_codemaster_retry_prompt_names_the_rejection_reason():
    client = FakeClient(
        [
            # Illegal: the clue is itself a board word.
            {"clue": "ירח", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
            {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")

    codemaster.give_clue(_board())

    first_user = client.calls[0][2]
    retry_user = client.calls[1][2]
    # The first ask is clean; only the retry carries the correction, so the
    # model is told what to fix instead of being re-asked identically.
    assert "REJECTED" not in first_user
    assert "REJECTED" in retry_user
    assert "must not be a word already on the board" in retry_user
    assert first_user != retry_user


def test_llm_guesser_retry_prompt_names_the_reason_and_relists_legal_words():
    client = FakeClient(
        [
            {"action": "guess", "word": "שמש"},  # not on the board
            {"action": "guess", "word": "ירח"},
        ]
    )
    guesser = LLMGuesser(client=client, model="m")

    guesser.guess_one(["ירח", "ב"], clue="אור", count=1, correct_so_far=[])

    retry_user = client.calls[1][2]
    assert "REJECTED" in retry_user
    assert "not among currently guessable words" in retry_user
    assert "ירח" in retry_user and "ב" in retry_user


def test_llm_codemaster_records_per_attempt_compliance_stats():
    client = FakeClient(
        [
            {"clue": "ירח", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
            {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "r"},
        ]
    )
    codemaster = LLMCodemaster(client=client, model="m", method="strong_hebrew")
    stats: Counter = Counter()

    codemaster.give_clue(_board(), stats=stats)

    assert stats["codemaster_attempts"] == 2
    assert stats["codemaster_rejected"] == 1
    assert stats["reason:clue_on_board"] == 1
    assert stats["codemaster_call_failures"] == 0


def test_llm_guesser_records_call_failure_when_retries_are_exhausted():
    client = FakeClient([{"action": "guess", "word": "off_board"}] * 6)
    guesser = LLMGuesser(client=client, model="m", max_retries=6)
    stats: Counter = Counter()

    with pytest.raises(FormatFailure):
        guesser.guess_one(["ירח"], clue="אור", count=1, correct_so_far=[], stats=stats)

    assert stats["guesser_attempts"] == 6
    assert stats["guesser_rejected"] == 6
    assert stats["guesser_call_failures"] == 1
    assert stats["reason:guess_not_available"] == 6


def test_adapters_default_to_six_retries():
    # Raised from 3 after the 2026-08-16 pilot: with corrective feedback a
    # model often needs more than one nudge to land a legal response.
    assert LLMCodemaster(client=None, model="m", method="strong_hebrew").max_retries == 6
    assert LLMGuesser(client=None, model="m").max_retries == 6
