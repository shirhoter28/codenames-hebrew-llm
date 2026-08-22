import pytest

from codenames_heb.board import Board
from codenames_heb.prompts.codemaster import (
    PROMPT_METHODS,
    CodemasterResponse,
    build_strong_hebrew_prompt,
    build_translate_pipeline_prompt,
    parse_codemaster_response,
    validate_clue_legality,
)


def _board() -> Board:
    return Board(
        seed=1,
        words=["א", "ב", "ג", "ד"],
        roles={"א": "target", "ב": "opponent", "ג": "civilian", "ד": "assassin"},
    )


def test_strong_hebrew_prompt_includes_all_role_groups():
    system, user = build_strong_hebrew_prompt(_board())

    assert "א" in system
    assert "ב" in system
    assert "ג" in system
    assert "ד" in system
    assert "JSON" in system
    assert user


def test_strong_hebrew_prompt_includes_required_count_when_set():
    system, _ = build_strong_hebrew_prompt(_board(), required_count=2)

    assert "target exactly 2 words, chosen by you" in system


def test_strong_hebrew_prompt_omits_required_count_line_when_none():
    system, _ = build_strong_hebrew_prompt(_board(), required_count=None)

    assert "chosen by you" not in system


def test_strong_hebrew_prompt_hides_unrevealed_roles_of_revealed_words():
    board = Board(
        seed=1,
        words=["ירח", "שמש", "ב", "ג", "ד"],
        roles={
            "ירח": "target",
            "שמש": "target",
            "ב": "opponent",
            "ג": "civilian",
            "ד": "assassin",
        },
    )

    system, _ = build_strong_hebrew_prompt(board, revealed={"ירח": "target"})

    # revealed target is no longer offered as a fresh YOUR_WORDS candidate...
    assert "YOUR_WORDS: שמש" in system
    # ...but is surfaced with its role in the REVEALED_SO_FAR context.
    assert "REVEALED_SO_FAR: ירח (TARGET)" in system


def test_strong_hebrew_prompt_omits_revealed_section_when_nothing_revealed():
    system, _ = build_strong_hebrew_prompt(_board())

    # The strict-rules instructions reference the REVEALED_SO_FAR field name
    # generically; what must be absent is an actual populated section.
    assert "REVEALED_SO_FAR:" not in system


def test_strong_hebrew_prompt_states_count_must_match_intended_targets():
    system, _ = build_strong_hebrew_prompt(_board())

    assert "count" in system and "intended_targets" in system


def test_translate_pipeline_prompt_asks_for_english_intermediate_fields():
    system, _ = build_translate_pipeline_prompt(_board())

    assert "translation_map" in system
    assert "en_clue" in system


def test_prompt_methods_registry_has_both_m1_methods():
    assert set(PROMPT_METHODS) == {"strong_hebrew", "translate_pipeline"}
    assert PROMPT_METHODS["strong_hebrew"] is build_strong_hebrew_prompt
    assert PROMPT_METHODS["translate_pipeline"] is build_translate_pipeline_prompt


def test_parse_codemaster_response_valid():
    data = {
        "clue": "  אור  ",
        "count": 2,
        "intended_targets": ["ירח", "שמש"],
        "reasoning": "both relate to light",
    }

    result = parse_codemaster_response(data)

    assert result == CodemasterResponse(
        clue="אור",
        count=2,
        intended_targets=["ירח", "שמש"],
        reasoning="both relate to light",
    )


def test_parse_codemaster_response_keeps_translation_fields():
    data = {
        "clue": "אור",
        "count": 1,
        "intended_targets": ["ירח"],
        "reasoning": "r",
        "translation_map": {"ירח": "moon"},
        "en_clue": "light",
        "en_targets": ["moon"],
    }

    result = parse_codemaster_response(data)

    assert result.translation_map == {"ירח": "moon"}
    assert result.en_clue == "light"
    assert result.en_targets == ["moon"]


def test_parse_codemaster_response_raises_on_missing_keys():
    with pytest.raises(ValueError):
        parse_codemaster_response({"clue": "אור"})


def test_parse_codemaster_response_raises_on_non_integer_count():
    with pytest.raises(ValueError):
        parse_codemaster_response(
            {"clue": "אור", "count": "two", "intended_targets": [], "reasoning": ""}
        )


def test_validate_clue_legality_accepts_novel_single_word():
    validate_clue_legality("אור", _board())


def test_validate_clue_legality_rejects_multi_word_clue():
    with pytest.raises(ValueError):
        validate_clue_legality("אור גדול", _board())


def test_validate_clue_legality_rejects_clue_already_on_board():
    with pytest.raises(ValueError):
        validate_clue_legality("א", _board())


def test_parse_codemaster_response_strips_whitespace_from_intended_targets():
    # Guesses are stripped in parse_single_guess_response; intended_targets
    # must be stripped the same way or exact-string matching between them
    # silently breaks.
    response = parse_codemaster_response(
        {
            "clue": "אור",
            "count": 2,
            "intended_targets": ["  ירח ", "\nשמש\t"],
            "reasoning": "r",
        }
    )

    assert response.intended_targets == ["ירח", "שמש"]


# --- the opposing team's win condition -----------------------------------


def _two_opponent_board() -> Board:
    return Board(
        seed=2,
        words=["א", "ב", "ג", "ד", "ה"],
        roles={
            "א": "target",
            "ב": "opponent",
            "ג": "opponent",
            "ד": "civilian",
            "ה": "assassin",
        },
    )


def test_rules_state_that_revealing_every_opponent_word_loses():
    system, _ = build_strong_hebrew_prompt(_board())

    assert "OPPONENT" in system
    assert "opposing team" in system


def test_opponent_progress_counts_against_the_board_total():
    system, _ = build_strong_hebrew_prompt(
        _two_opponent_board(), revealed={"ב": "opponent"}
    )

    assert "OPPONENT_PROGRESS: 1 of 2" in system


def test_opponent_progress_starts_at_zero_before_anything_is_revealed():
    system, _ = build_strong_hebrew_prompt(_two_opponent_board())

    assert "OPPONENT_PROGRESS: 0 of 2" in system


def test_opponent_progress_ignores_revealed_words_of_other_roles():
    system, _ = build_strong_hebrew_prompt(
        _two_opponent_board(), revealed={"א": "target", "ד": "civilian"}
    )

    assert "OPPONENT_PROGRESS: 0 of 2" in system


def test_translate_pipeline_also_carries_the_opponent_progress_line():
    system, _ = build_translate_pipeline_prompt(
        _two_opponent_board(), revealed={"ב": "opponent"}
    )

    assert "OPPONENT_PROGRESS: 1 of 2" in system
