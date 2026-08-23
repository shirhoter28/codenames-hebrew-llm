"""Classification of model non-compliance, for per-call compliance metrics.

A game makes many LLM calls, so per-game completion rates are confounded by
game length (a model whose games run twice as long gets twice as many
chances to fail). Counting rejected *attempts* against total *attempts*
gives a length-independent compliance rate, and the reason labels double as
the error taxonomy for qualitative analysis.
"""

# Ordered: the first matching label wins, so put specific patterns before
# generic ones. Patterns match the exact wording raised by the validators in
# `prompts/` and `experiment.py` — keep them in sync with those messages.
_REASON_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("clue_on_board", ("must not be a word already on the board",)),
    ("clue_not_single_word", ("must be a single word",)),
    ("targets_not_on_board", ("intended_targets not on board",)),
    ("duplicate_targets", ("duplicate intended_targets",)),
    # Before count_mismatch: both messages mention a count, and conflating
    # them would hide how often the floor is what the model failed to meet.
    ("count_below_floor", ("below the required floor",)),
    ("count_mismatch", ("!= len(intended_targets)",)),
    ("guess_not_available", ("not among currently guessable words",)),
    ("premature_stop", ("cannot stop before guessing",)),
    (
        "bad_action",
        ("unknown action", "must contain an 'action'", "requires a non-empty 'word'"),
    ),
    (
        "bad_field_types",
        (
            "count must be a non-negative integer",
            "clue must be a non-empty string",
            "intended_targets must be a list",
        ),
    ),
    ("missing_keys", ("missing keys",)),
    ("json_parse", ("valid JSON", "parse JSON", "expected a JSON object")),
)


def classify_error(message: str) -> str:
    """Map a validation/parse error message to a stable reason label."""
    for label, needles in _REASON_PATTERNS:
        if any(needle in message for needle in needles):
            return label
    return "other"
