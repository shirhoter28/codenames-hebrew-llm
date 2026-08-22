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


def test_build_single_guess_prompt_states_how_much_of_the_budget_is_left():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=2, correct_so_far=["ב"], can_stop=True
    )

    assert "1 of at most 3" in system


def test_build_single_guess_prompt_says_the_budget_is_a_ceiling_not_a_quota():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=2, correct_so_far=["ב"], can_stop=True
    )

    assert "do not have to use" in system.lower()


def test_build_single_guess_prompt_reports_no_cap_when_count_is_zero():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=0, correct_so_far=["ב"], can_stop=True
    )

    assert "Guesses used this round: 1" in system
    assert "at most" not in system.lower()


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


# --- the opposing team's win condition -----------------------------------
#
# The guesser is never shown the key, so it cannot count the board's opponent
# words the way the codemaster can. It is told how many have been revealed and
# left to read the total off GAME_RULES, rather than shown a number that would
# be wrong on a non-standard board.


def test_rules_state_that_revealing_every_opponent_word_loses():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=1, correct_so_far=[], can_stop=False
    )

    assert "OPPONENT" in system
    assert "opposing team" in system


def test_guesser_is_told_how_many_opponent_words_have_been_revealed():
    system, _ = build_single_guess_prompt(
        ["א"],
        clue="אור",
        count=1,
        correct_so_far=[],
        can_stop=False,
        revealed={"ב": "opponent", "ג": "opponent", "ד": "civilian"},
    )

    assert "OPPONENT_PROGRESS: 2 OPPONENT" in system


def test_opponent_progress_is_omitted_before_any_word_is_revealed():
    system, _ = build_single_guess_prompt(
        ["א"], clue="אור", count=1, correct_so_far=[], can_stop=False
    )

    assert "OPPONENT_PROGRESS" not in system
