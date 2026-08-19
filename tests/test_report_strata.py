"""The report's stratum list, which decides which tables get emitted.

`scripts/report.py` had no tests at all; these cover the part the guesser axis
changes, so the regrouping does not land unverified.
"""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_report_module():
    spec = importlib.util.spec_from_file_location(
        "report_script", PROJECT_ROOT / "scripts" / "report.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


report = _load_report_module()


def _games(models=("a", "b"), guessers=("a", "b"), methods=("strong_hebrew",),
           styles=("dual_0", "dual_50")):
    rows = [
        {"model": m, "guesser_model": g, "method": meth, "board_style": s}
        for m in models
        for g in guessers
        for meth in methods
        for s in styles
    ]
    return pd.DataFrame(rows)


def test_a_crossed_guesser_gets_its_own_stratum():
    strata = report._strata(_games())

    assert ["guesser_model"] in strata.values()


def test_the_codemaster_x_guesser_cell_is_stratified():
    """The 4x4 grid is the run's reason for existing; it needs its own table."""
    strata = report._strata(_games())

    assert ["model", "guesser_model"] in strata.values()


def test_a_single_level_factor_is_dropped_from_every_stratum():
    """One prompt method must not produce 'by codemaster x prompt method' — it
    would be the 'by codemaster' table again under a heading implying a
    comparison the run cannot make."""
    strata = report._strata(_games(methods=("strong_hebrew",)))

    assert all("method" not in cols for cols in strata.values())


def test_dropping_a_degenerate_factor_does_not_leave_duplicate_tables():
    strata = report._strata(_games(methods=("strong_hebrew",)))

    as_tuples = [tuple(cols) for cols in strata.values()]
    assert len(as_tuples) == len(set(as_tuples))


def test_a_fixed_guesser_run_gets_no_guesser_stratum():
    """Every run before M3 held the guesser fixed; those reports should look
    exactly as they did."""
    strata = report._strata(_games(guessers=("only",)))

    assert all("guesser_model" not in cols for cols in strata.values())


def test_stop_behaviour_follows_the_guesser_only_when_the_guesser_varies():
    """Grouping by a column that holds one value collapses the table to a
    single row and throws away the per-codemaster breakdown."""
    assert report._stop_group(_games(guessers=("only",))) == ["model", "board_style"]
    assert report._stop_group(_games()) == ["guesser_model", "board_style"]


def test_miss_lift_follows_the_guesser_only_when_the_guesser_varies():
    assert report._miss_group(_games(guessers=("only",))) == "model"
    assert report._miss_group(_games()) == "guesser_model"


def test_labels_name_the_role_not_the_bare_column():
    """'by model' is ambiguous once guessers are models too."""
    strata = report._strata(_games())

    label = next(k for k, v in strata.items() if v == ["model", "guesser_model"])
    assert "codemaster" in label and "guesser" in label
