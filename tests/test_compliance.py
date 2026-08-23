from codenames_heb.compliance import classify_error


def test_classifies_each_known_validator_message():
    cases = {
        "clue 'ים' must not be a word already on the board": "clue_on_board",
        "clue 'דבר, 2' must be a single word": "clue_not_single_word",
        "intended_targets not on board: ['מצנח']": "targets_not_on_board",
        "duplicate intended_targets: ['ירח', 'ירח']": "duplicate_targets",
        "count 3 != len(intended_targets) 1": "count_mismatch",
        "guess 'סרט' not among currently guessable words": "guess_not_available",
        "cannot stop before guessing at least once": "premature_stop",
        "unknown action: 'pass'": "bad_action",
        "Codemaster response missing keys: {'count'}": "missing_keys",
        "failed to produce valid JSON after 1 attempts": "json_parse",
    }
    for message, expected in cases.items():
        assert classify_error(message) == expected, message


def test_unrecognized_message_falls_back_to_other():
    assert classify_error("something nobody has seen before") == "other"


def test_a_count_below_the_floor_is_its_own_reason():
    # Must classify before the generic count_mismatch entry: both messages
    # mention a count, and conflating them would hide how often the floor is
    # what the model failed to meet.
    assert classify_error("count 1 is below the required floor of 3") == "count_below_floor"


def test_the_floor_reason_does_not_swallow_a_plain_count_mismatch():
    assert classify_error("count 3 != len(intended_targets) 1") == "count_mismatch"
