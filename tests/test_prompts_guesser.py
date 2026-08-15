import pytest

from codenames_heb.prompts.guesser import build_single_guess_prompt, parse_single_guess_response


def test_build_single_guess_prompt_includes_board_clue_and_count():
    system, user = build_single_guess_prompt(
        ["א", "ב", "ג"], clue="אור", count=2, correct_so_far=[], can_stop=False
    )

    assert "א" in system
    assert "ב" in system
    assert "ג" in system
    assert "אור" in system
    assert "2" in system
    assert "JSON" in system
    assert user


def test_build_single_guess_prompt_requires_guessing_when_cannot_stop():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=1, correct_so_far=[], can_stop=False
    )

    assert '"action": "stop"' not in system
    assert "must guess at least once" in system.lower()


def test_build_single_guess_prompt_offers_stop_when_allowed():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=2, correct_so_far=["ב"], can_stop=True
    )

    assert '"action": "stop"' in system
    assert "ב" in system  # shown as already guessed correctly this round


def test_build_single_guess_prompt_includes_revealed_context():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=1, correct_so_far=[], can_stop=False,
        revealed={"ג": "opponent"},
    )

    assert "REVEALED_SO_FAR" in system
    assert "ג (OPPONENT)" in system


def test_parse_single_guess_response_valid_guess():
    result = parse_single_guess_response({"action": "guess", "word": " ירח "})

    assert result == "ירח"


def test_parse_single_guess_response_valid_stop():
    result = parse_single_guess_response({"action": "stop"})

    assert result is None


def test_parse_single_guess_response_raises_when_action_missing():
    with pytest.raises(ValueError):
        parse_single_guess_response({})


def test_parse_single_guess_response_raises_on_unknown_action():
    with pytest.raises(ValueError):
        parse_single_guess_response({"action": "pass"})


def test_parse_single_guess_response_raises_when_guess_missing_word():
    with pytest.raises(ValueError):
        parse_single_guess_response({"action": "guess"})
