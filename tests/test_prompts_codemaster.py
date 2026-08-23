import pytest

from codenames_heb.board import Board
from codenames_heb.prompts.codemaster import (
    PROMPT_METHODS,
    CodemasterResponse,
    build_correction_note,
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

    assert "AT LEAST 2" in system


def test_strong_hebrew_prompt_omits_required_count_line_when_none():
    system, _ = build_strong_hebrew_prompt(_board(), required_count=None)

    assert "AT LEAST" not in system


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


# --- reasoning is no longer requested ------------------------------------
#
# It was 74% of the codemaster's reply bytes on the 08-17 run and, being the
# last key in the JSON, could only ever be post-hoc justification — the clue
# is already committed by the time it is written. Dropped for run cost; still
# accepted if a model volunteers one.


def test_prompts_no_longer_ask_for_reasoning():
    strong, _ = build_strong_hebrew_prompt(_board())
    translate, _ = build_translate_pipeline_prompt(_board())

    assert "reasoning" not in strong
    assert "reasoning" not in translate


def test_a_response_without_reasoning_is_accepted():
    result = parse_codemaster_response(
        {"clue": "אור", "count": 1, "intended_targets": ["ירח"]}
    )

    assert result.clue == "אור"
    assert result.reasoning == ""


def test_volunteered_reasoning_is_still_kept():
    result = parse_codemaster_response(
        {"clue": "אור", "count": 1, "intended_targets": ["ירח"], "reasoning": "light"}
    )

    assert result.reasoning == "light"


# --- clue-count floors ---------------------------------------------------
#
# The count constraint is a floor ("at least N"), not an exact requirement: a
# floor accepts anything at or above the minimum, so it rejects less often —
# and rejections are the main cost risk of the M4 run.


def test_the_floor_is_a_minimum_not_an_exact_requirement():
    system, _ = build_strong_hebrew_prompt(_board(), required_count=3)

    assert "AT LEAST 3" in system
    assert "exactly 3" not in system


def test_the_floor_line_rules_out_a_count_of_zero():
    # count 0 means "unlimited guesses" under GAME_RULES, so it would otherwise
    # slip under any floor numerically while meaning the opposite.
    system, _ = build_strong_hebrew_prompt(_board(), required_count=2)

    assert "0" in system
    assert "unlimited" in system.lower()


def test_translate_pipeline_carries_the_floor_too():
    system, _ = build_translate_pipeline_prompt(_board(), required_count=2)

    assert "AT LEAST 2" in system


def test_correction_note_states_the_floor_when_one_applies():
    note = build_correction_note("count 1 is below the floor", _board(), required_count=3)

    assert "3" in note
    assert "at least" in note.lower()


def test_correction_note_says_nothing_about_a_floor_when_there_is_none():
    note = build_correction_note("some other problem", _board())

    assert "at least" not in note.lower()


# --- translate_pipeline emits its translation work before the clue -------
#
# Generation is autoregressive: asking for `clue` first meant the Hebrew clue
# was committed before any translation existed in the output, so "translate,
# think in English, translate back" had nothing to condition on.


def test_translate_pipeline_asks_for_the_translation_before_the_clue():
    system, _ = build_translate_pipeline_prompt(_board())
    spec = system.split("Respond with JSON only:")[1]

    assert spec.index("translation_map") < spec.index('"clue"')
    assert spec.index("en_targets") < spec.index('"clue"')
    assert spec.index("en_clue") < spec.index('"clue"')


def test_translate_pipeline_still_parses_by_key_not_position():
    # The reorder is a generation-order change only; parsing is by key.
    result = parse_codemaster_response(
        {"translation_map": {"ירח": "moon"}, "en_targets": ["moon"], "en_clue": "light",
         "intended_targets": ["ירח"], "count": 1, "clue": "אור"}
    )

    assert result.clue == "אור"
    assert result.en_clue == "light"
