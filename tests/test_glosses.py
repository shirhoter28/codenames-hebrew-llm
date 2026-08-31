"""Sense classification for ambiguous board words, and the tables behind the
two ambiguity figures.

The claim these support is that a model's *default sense* for an ambiguous
Hebrew word is model-specific. That only holds up if a gloss is assigned to a
sense the same way every time, so the classifier is the part worth pinning: a
hedge names both senses and is neither, an off-sense answer is kept rather than
dropped, and a token never matches inside a longer word.
"""

import json

import pandas as pd
import pytest

from codenames_heb.glosses import (
    BOTH,
    SENSES,
    UNRELATED,
    classify,
    gloss_counts,
    sense_shares,
    top_glosses,
)


def test_a_gloss_naming_one_sense_takes_that_sense():
    assert classify("הודו", "india") == "India"
    assert classify("הודו", "turkey") == "turkey"


def test_a_hedge_naming_both_senses_is_neither():
    assert classify("כבד", "heavy/liver") == BOTH
    assert classify("כבד", "liver/heavy") == BOTH


def test_a_gloss_naming_no_listed_sense_is_kept_as_unrelated():
    # qwen glosses אוגר as "ogre"; dropping it would hide most of its mass.
    assert classify("אוגר", "ogre") == UNRELATED


def test_tokens_match_whole_words_only():
    # "god" must not match inside "goddess" — אלה's two senses are these/goddess.
    assert classify("אלה", "goddess") == "goddess"
    assert classify("אלה", "these") == "these"


def test_case_and_punctuation_do_not_change_the_sense():
    assert classify("הודו", "India") == classify("הודו", "  india ") == "India"
    assert classify("קניון", "mall / canyon") == BOTH


def test_an_unknown_word_is_an_error_not_a_silent_bucket():
    with pytest.raises(KeyError):
        classify("לאמילהכזאת", "whatever")


@pytest.fixture
def run_dir(tmp_path):
    def game(method, tmap):
        return {
            "model": "vendor/alpha", "guesser_model": "vendor/beta", "method": method,
            "board_seed": 1, "board_style": "natural", "trial": 0,
            "count_constraint": None, "outcome": "win", "game_length": 1,
            "rounds": [{"round": 1, "clue": "c", "count": 1, "intended_targets": [],
                        "translation_map": tmap, "guess_sequence": []}],
        }
    d = tmp_path / "20260101T000000000000Z"
    d.mkdir()
    (d / "raw.jsonl").write_text("\n".join(json.dumps(g) for g in [
        game("translate_pipeline", {"הודו": "india", "כבד": "heavy"}),
        game("translate_pipeline", {"הודו": "turkey", "כבד": "heavy/liver"}),
        # strong_hebrew carries no map and must not contribute.
        game("strong_hebrew", None),
        # A model that answered with a shape instead of a map.
        game("translate_pipeline", {"YOUR_WORDS": ["a", "b"]}),
    ]) + "\n")
    return d


def test_only_translate_games_contribute(run_dir):
    counts = gloss_counts([run_dir], words=SENSES)
    assert int(counts["n"].sum()) == 4


def test_non_hebrew_keys_are_skipped(run_dir):
    counts = gloss_counts([run_dir], words=SENSES)
    assert "YOUR_WORDS" not in set(counts["word"])


def test_counts_are_per_round_not_per_game(run_dir):
    counts = gloss_counts([run_dir], words=SENSES)
    hodu = counts[counts["word"] == "הודו"].set_index("gloss")["n"]
    assert hodu["india"] == 1 and hodu["turkey"] == 1


def test_shares_split_three_ways_and_sum_with_unrelated(run_dir):
    shares = sense_shares(gloss_counts([run_dir], words=SENSES))
    row = shares[shares["word"] == "כבד"].iloc[0]
    assert row["share_a"] == pytest.approx(0.5)     # heavy
    assert row["share_both"] == pytest.approx(0.5)  # heavy/liver
    total = row[["share_a", "share_both", "share_b", "share_unrelated"]].sum()
    assert total == pytest.approx(1.0)


def test_shares_are_labelled_with_the_sense_names(run_dir):
    shares = sense_shares(gloss_counts([run_dir], words=SENSES))
    row = shares[shares["word"] == "הודו"].iloc[0]
    assert (row["sense_a"], row["sense_b"]) == ("India", "turkey")


def test_top_glosses_reports_distinct_count_and_shares(run_dir):
    tops = top_glosses(gloss_counts([run_dir], words=SENSES), k=2)
    row = tops[tops["word"] == "הודו"].iloc[0]
    assert row["n_glosses"] == 2
    assert {g for g, _, _ in row["top"]} == {"india", "turkey"}
    assert all(share == pytest.approx(0.5) for _, _, share in row["top"])


def test_empty_runs_give_an_empty_frame_with_the_right_columns(tmp_path):
    counts = gloss_counts([tmp_path])
    assert counts.empty
    assert list(counts.columns) == ["model", "word", "gloss", "n"]


def test_every_sense_definition_is_well_formed():
    for word, ((a_label, a_tokens), (b_label, b_tokens)) in SENSES.items():
        assert a_label != b_label, word
        assert a_tokens and b_tokens, word
        assert not set(a_tokens) & set(b_tokens), word
        # The labels must themselves classify to their own side, or the chart
        # legend and the bars would disagree.
        assert classify(word, a_label) == a_label, word
        assert classify(word, b_label) == b_label, word
