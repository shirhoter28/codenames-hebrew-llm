"""Analysis-layer support for the Guesser as a crossed factor.

The tables all take caller-supplied `group_cols`, so the guesser slots in
without signature changes. The two things that do not are sizing an
*interaction* (the point of a 4x4 grid) and keeping the report's stratum list
honest when a factor has only one level.
"""

import pandas as pd
import pytest

from codenames_heb.analysis import comparison_power


def _games(n_models=4, n_guessers=4, per_cell=5):
    """A completed-games frame spanning a full codemaster x guesser grid."""
    rows = []
    for m in range(n_models):
        for g in range(n_guessers):
            for i in range(per_cell):
                rows.append(
                    {
                        "model": f"m{m}",
                        "guesser_model": f"m{g}",
                        "method": "strong_hebrew",
                        "board_style": "dual_0",
                        "completed": True,
                        "is_win": i % 2 == 0,
                        "first_guess_lift": 0.3 + 0.01 * i,
                        "game_length": 8 + i,
                        "total_api_calls": 26,
                    }
                )
    return pd.DataFrame(rows)


DESIGN = ("model", "guesser_model", "method", "board_style")


def test_a_tuple_comparison_sizes_the_pair_as_one_arm():
    """A 4x4 grid has 16 pair arms, not 4 — sizing it as a main effect
    overstates the games behind each cell by 4x."""
    result = comparison_power(
        _games(),
        candidate_ns=(5,),
        design_cols=DESIGN,
        comparisons=[("model", "guesser_model")],
    )

    assert len(result) == 1
    row = result.iloc[0]
    assert row["levels"] == 16
    assert row["games_per_arm"] == pytest.approx(5 * 16 / 16)


def test_the_pair_arm_is_harder_to_resolve_than_either_main_effect():
    result = comparison_power(
        _games(),
        candidate_ns=(5,),
        design_cols=DESIGN,
        comparisons=["model", ("model", "guesser_model")],
    )

    by_name = {r["comparison"]: r for _, r in result.iterrows()}
    main = next(v for k, v in by_name.items() if k.startswith("model ("))
    pair = next(v for k, v in by_name.items() if "guesser_model" in k)

    assert pair["mdd_first_guess_lift"] > main["mdd_first_guess_lift"]


def test_a_tuple_comparison_is_named_for_both_of_its_factors():
    result = comparison_power(
        _games(),
        candidate_ns=(5,),
        design_cols=DESIGN,
        comparisons=[("model", "guesser_model")],
    )

    name = result.iloc[0]["comparison"]
    assert "model" in name and "guesser_model" in name


def test_a_tuple_comparison_with_a_degenerate_factor_is_skipped():
    """One guesser means no pair axis to compare; emitting it would imply the
    run can answer a question it cannot."""
    result = comparison_power(
        _games(n_guessers=1),
        candidate_ns=(5,),
        design_cols=DESIGN,
        comparisons=[("model", "guesser_model")],
    )

    assert result.empty
