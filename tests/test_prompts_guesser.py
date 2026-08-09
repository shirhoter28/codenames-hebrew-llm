import pytest

from codenames_heb.prompts.guesser import build_guesser_prompt, parse_guesser_response


def test_build_guesser_prompt_includes_board_clue_and_count():
    system, user = build_guesser_prompt(["א", "ב", "ג"], clue="אור", count=2)

    assert "א" in system
    assert "ב" in system
    assert "ג" in system
    assert "אור" in system
    assert "2" in system
    assert "JSON" in system
    assert user


def test_build_guesser_prompt_describes_unlimited_guesses_when_count_is_zero():
    system, _ = build_guesser_prompt(["א", "ב"], clue="אור", count=0)

    assert "unlimited" in system.lower()


def test_parse_guesser_response_valid():
    result = parse_guesser_response({"guesses": [" ירח ", "שמש"]})

    assert result == ["ירח", "שמש"]


def test_parse_guesser_response_raises_when_guesses_missing():
    with pytest.raises(ValueError):
        parse_guesser_response({})


def test_parse_guesser_response_raises_when_guesses_not_a_list():
    with pytest.raises(ValueError):
        parse_guesser_response({"guesses": "ירח"})
