import pytest
import pandas as pd

from codenames_heb.agreement import (
    CELL_KEY, PANEL_KEY, first_rounds, normalize_clue, panel_agreement,
    consensus_hard_by_dual, word_consensus,
)


def test_normalize_strips_niqqud():
    # Vocalization is optional in the source and appears inconsistently, so two
    # spellings of one word must not read as disagreement.
    assert normalize_clue("בַּיִת") == normalize_clue("בית")


def test_normalize_folds_final_letters():
    # Final forms are positional variants of the same letter.
    assert normalize_clue("ארץ") == normalize_clue("ארצ")


def test_normalize_keeps_genuinely_different_words_apart():
    # The definite article changes meaning; folding it would overstate agreement.
    assert normalize_clue("ים") != normalize_clue("הים")
    assert normalize_clue("כלב") != normalize_clue("לב")


def test_normalize_handles_a_missing_clue():
    assert normalize_clue(None) == ""


def _round(model, guesser, clue, targets, rnd=1, style="natural", seed=0):
    return {
        "board_style": style, "board_seed": seed, "model": model,
        "guesser_model": guesser, "method": "strong_hebrew",
        "count_constraint": "free", "round": rnd,
        "clue": clue, "intended_targets": targets,
        "count": len(targets), "n_correct": 1,
        "stop_class": "stopped_at_quota", "first_miss_role": None,
    }


@pytest.fixture
def cell_rounds():
    """One cell: model alpha, 4 guessers, all giving the same clue.

    Plus a round-2 row that must never be counted, and a second codemaster.
    """
    rows = [_round("v/alpha", f"g{i}", "בית", ["א", "ב"]) for i in range(4)]
    rows.append(_round("v/alpha", "g0", "אחר", ["ג"], rnd=2))
    rows += [_round("v/beta", f"g{i}", f"קלו{i}", ["א"]) for i in range(4)]
    return pd.DataFrame(rows)


def test_first_rounds_keeps_only_round_one(cell_rounds):
    out = first_rounds(cell_rounds)

    assert set(out["round"]) == {1}
    assert len(out) == 8


def test_first_rounds_attaches_normalized_clue_and_target_set(cell_rounds):
    out = first_rounds(cell_rounds)
    alpha = out[out["model"] == "v/alpha"]

    assert set(alpha["clue_norm"]) == {"בית"}
    assert set(alpha["target_set"]) == {frozenset({"א", "ב"})}


def test_keys_name_the_two_units():
    # A cell is one model's replicates; a panel pools the codemasters on one
    # board, holding method and floor fixed so it stays a model contrast.
    assert CELL_KEY == ["board_style", "board_seed", "model", "method", "count_constraint"]
    assert PANEL_KEY == ["board_style", "board_seed", "method", "count_constraint"]


def test_jaccard_is_one_on_identical_sets():
    from codenames_heb.agreement import mean_pairwise_jaccard
    sets = [frozenset({"א", "ב"})] * 3
    assert mean_pairwise_jaccard(sets) == 1.0


def test_jaccard_is_zero_on_disjoint_sets():
    from codenames_heb.agreement import mean_pairwise_jaccard
    assert mean_pairwise_jaccard([frozenset({"א"}), frozenset({"ב"})]) == 0.0


def test_jaccard_is_undefined_for_a_single_draw():
    from codenames_heb.agreement import mean_pairwise_jaccard
    # One draw has no pair, so there is nothing to agree with.
    assert mean_pairwise_jaccard([frozenset({"א"})]) is None


def test_unanimous_cell_scores_one_distinct_clue(cell_rounds):
    from codenames_heb.agreement import self_consistency
    cells = self_consistency(cell_rounds)
    alpha = cells[cells["model"] == "v/alpha"].iloc[0]

    assert alpha["n_draws"] == 4
    assert alpha["n_distinct_clues"] == 1
    assert alpha["is_unanimous"] == 1.0
    assert alpha["modal_share"] == 1.0


def test_all_different_cell_scores_four_distinct_clues(cell_rounds):
    from codenames_heb.agreement import self_consistency
    cells = self_consistency(cell_rounds)
    beta = cells[cells["model"] == "v/beta"].iloc[0]

    assert beta["n_distinct_clues"] == 4
    assert beta["is_unanimous"] == 0.0
    assert beta["modal_share"] == 0.25
    # Different wording, identical aim: the strategy is stable even though the
    # clue is not. This is the distinction n_distinct_clues cannot make.
    assert beta["self_jaccard"] == 1.0


def test_short_cell_is_scored_over_the_draws_it_has(cell_rounds):
    from codenames_heb.agreement import self_consistency
    trimmed = cell_rounds.drop(cell_rounds[cell_rounds["model"] == "v/alpha"].index[:2])
    cells = self_consistency(trimmed)
    alpha = cells[cells["model"] == "v/alpha"].iloc[0]

    assert alpha["n_draws"] == 2
    assert alpha["modal_share"] == 1.0


def test_summary_groups_cells_by_model(cell_rounds):
    from codenames_heb.agreement import self_consistency_summary
    out = self_consistency_summary(cell_rounds)

    assert set(out["model"]) == {"v/alpha", "v/beta"}
    assert "is_unanimous_mean" in out.columns


def test_panel_agreement_excludes_same_codemaster_pairs(cell_rounds):
    # alpha is unanimous (4 identical clues), beta gives 4 different ones, and
    # no alpha clue equals a beta clue. Counting alpha's 6 self-pairs would
    # report agreement 6/28 instead of the true cross-model 0/16.
    panel = panel_agreement(cell_rounds).iloc[0]

    assert panel["n_draws"] == 8
    assert panel["n_codemasters"] == 2
    assert panel["n_cross_pairs"] == 16
    assert panel["pairwise_clue_agreement"] == 0.0


def test_panel_agreement_counts_a_shared_clue(cell_rounds):
    agreed = cell_rounds.copy()
    agreed.loc[agreed["model"] == "v/beta", "clue"] = "בית"
    panel = panel_agreement(agreed).iloc[0]

    assert panel["pairwise_clue_agreement"] == 1.0
    assert panel["consensus_clue"] == "בית"
    assert panel["consensus_share"] == 1.0


def test_panel_agreement_reports_target_overlap(cell_rounds):
    # alpha aims at {א, ב}, beta at {א}: Jaccard = 1/2 on every cross pair.
    panel = panel_agreement(cell_rounds).iloc[0]

    assert panel["pairwise_target_jaccard"] == 0.5


def test_panel_agreement_skips_a_single_codemaster_panel(cell_rounds):
    solo = cell_rounds[cell_rounds["model"] == "v/alpha"]

    assert panel_agreement(solo).empty


@pytest.fixture
def boards():
    """One board. `א` is aimed at by every draw; `ד` by none."""
    return {
        ("natural", 0): {
            "roles": {"א": "target", "ב": "target", "ד": "target", "ה": "civilian"},
            "is_dual": {"א": False, "ב": False, "ד": True, "ה": False},
        }
    }


def test_word_consensus_flags_a_target_no_model_aims_at(cell_rounds, boards):
    out = word_consensus(cell_rounds, boards)
    hard = out[out["is_consensus_hard"] == 1.0]

    assert set(hard["word"]) == {"ד"}


def test_word_consensus_does_not_flag_a_word_every_draw_names(cell_rounds, boards):
    out = word_consensus(cell_rounds, boards)
    row = out[out["word"] == "א"].iloc[0]

    assert row["n_picks"] == 8
    assert row["word_pick_rate"] == 1.0
    assert row["is_consensus_hard"] == 0.0


def test_word_consensus_never_flags_a_non_target(cell_rounds, boards):
    # A civilian that nobody aims at is correct play, not a hard word.
    out = word_consensus(cell_rounds, boards)
    civilian = out[out["word"] == "ה"].iloc[0]

    assert civilian["n_picks"] == 0
    assert civilian["is_consensus_hard"] == 0.0


def test_consensus_hard_crosses_with_the_dual_flag(cell_rounds, boards):
    out = consensus_hard_by_dual(word_consensus(cell_rounds, boards))

    assert "is_consensus_hard_mean" in out.columns
    assert set(out["is_dual"]) == {0.0, 1.0}
