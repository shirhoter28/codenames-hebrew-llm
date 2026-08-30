"""The codemaster x guesser pair table, in the shape of the English Table I.

The point of the layout is that a codemaster's numbers are not a property of
the codemaster alone — the guesser it was handed to moves all of them — so the
grid of pairs has to stay complete no matter which arm the table is cut by.
"""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from codenames_heb.analysis import pair_table

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "pair_tables_script", PROJECT_ROOT / "scripts" / "pair_tables.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


script = _load_script()

MODELS = ("vendor/alpha", "vendor/beta")


@pytest.fixture
def games():
    """Every pair against every arm: 2 codemasters x 2 guessers x 2 methods x
    2 floors x 2 styles x 2 games. Trial 0 wins, trial 1 loses."""
    records = []
    for model in MODELS:
        for guesser in MODELS:
            for method in ("strong_hebrew", "translate_pipeline"):
                for floor in ("free", "min2"):
                    for style in ("dual_0", "dual_100"):
                        for trial in range(2):
                            win = trial == 0
                            records.append({
                                "run_id": "r", "model": model, "method": method,
                                "guesser_model": guesser, "count_constraint": floor,
                                "board_style": style, "board_seed": trial,
                                "trial": trial,
                                "outcome": "win" if win else "loss",
                                "completed": True,
                                "is_win": float(win), "is_loss": float(not win),
                                # Wins run long, losses end on the assassin.
                                "game_length": 10.0 if win else 4.0,
                                "opponent_words_revealed": 2,
                                "civilian_words_revealed": 3,
                            })
    return pd.DataFrame(records)


@pytest.fixture
def rounds(games):
    """Two rounds a game. The first is bonus-eligible but not early-stop
    eligible; the second is the reverse."""
    records = []
    for row in games.itertuples(index=False):
        for rnd in (1, 2):
            records.append({
                "run_id": row.run_id, "model": row.model, "method": row.method,
                "guesser_model": row.guesser_model,
                "count_constraint": row.count_constraint,
                "board_style": row.board_style, "board_seed": row.board_seed,
                "trial": row.trial, "round": rnd,
                "count": 2.0, "n_guesses": 3 if rnd == 1 else 1,
                "is_early_stop": None if rnd == 1 else 1.0,
                "is_bonus_taken": 1.0 if rnd == 1 else None,
            })
    return pd.DataFrame(records)


def test_pair_table_has_a_row_per_codemaster_guesser_pair(games, rounds):
    table = pair_table(games, rounds)

    assert len(table) == len(MODELS) ** 2
    assert set(table["model"]) == set(MODELS)
    assert set(table["guesser_model"]) == set(MODELS)


def test_pair_table_keeps_every_pair_when_cut_by_an_arm(games, rounds):
    """A cut re-weights what is averaged over; it must never drop a pair. The
    design crosses every pair with every level of every factor."""
    for column in ("method", "count_constraint", "board_style"):
        for level in games[column].unique():
            table = pair_table(
                games[games[column] == level], rounds[rounds[column] == level]
            )
            assert len(table) == len(MODELS) ** 2, f"{column}={level}"


def test_mean_without_loss_counts_only_the_wins(games, rounds):
    """A lost game is short because it ended on the assassin. Pooling the two
    makes a pair that dies early look efficient."""
    table = pair_table(games, rounds)

    # Wins run 10 rounds, losses 4, half and half.
    assert set(table["length_mean"].round(2)) == {7.0}
    assert set(table["length_mean_wins"].round(2)) == {10.0}


def test_stop_rates_are_over_eligible_rounds_only(games, rounds):
    """A guesser may not stop before its first correct guess, so an early stop
    is impossible when the clue named a count of 1. Counting those rounds would
    deflate the rate for reasons unrelated to the guesser's judgement."""
    table = pair_table(games, rounds)

    # Every game has 2 rounds, but only one of each kind is eligible.
    assert (table["rounds"] == 2 * table["games"]).all()
    assert (table["n_early_eligible"] == table["games"]).all()
    assert (table["n_late_eligible"] == table["games"]).all()
    assert set(table["stop_early_rate"]) == {1.0}


def test_rounds_of_a_game_that_never_played_out_are_dropped(games, rounds):
    """An abandoned game contributes clue counts from a board its pair never
    finished, and every game-level column here is over completed games."""
    abandoned = games.copy()
    abandoned.loc[abandoned["trial"] == 1, "completed"] = False

    table = pair_table(abandoned, rounds)

    assert (table["games"] == 8).all()
    assert (table["rounds"] == 16).all()


def test_pair_table_is_empty_rather_than_wrong_without_completed_games(games, rounds):
    table = pair_table(games.assign(completed=False), rounds)

    assert table.empty


# --- the document ---------------------------------------------------------


def test_document_carries_a_pooled_table_and_one_section_per_arm(games, rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds = games, rounds

    document, frame = script.build_document(data, "test-run")

    assert "## All arms pooled" in document
    for title in ("By prompt method", "By clue-count floor", "By board style"):
        assert f"## {title}" in document
    # 1 pooled + 2 methods + 2 floors + 2 styles, each a full grid of 4 pairs.
    assert len(frame) == 7 * len(MODELS) ** 2
    assert set(frame["stratum"]) == {"all", "method", "count_constraint", "board_style"}


def test_document_skips_an_arm_the_run_held_fixed(games, rounds):
    """A single-level "cut" repeats the pooled table under a heading that
    implies a contrast the run cannot make."""
    class Data:
        pass

    data = Data()
    data.games = games[games["method"] == "strong_hebrew"]
    data.rounds = rounds[rounds["method"] == "strong_hebrew"]

    document, frame = script.build_document(data, "test-run")

    assert "By prompt method" not in document
    assert "method" not in set(frame["stratum"])


def test_document_orders_the_floors_numerically_not_alphabetically(games, rounds):
    # `min10` sorts between `free` and `min2` as a string, drawing the designed
    # ladder out of sequence.
    assert script.level_order("count_constraint", ["min3", "min10", "free"]) == [
        "free", "min3", "min10",
    ]


def test_document_renders_the_paper_s_columns(games, rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds = games, rounds

    document, _ = script.build_document(data, "test-run")

    for label in ("Mean (without loss)", "Std Dev", "Loss", "Opponent avg(stdev)",
                  "Civilian avg(stdev)", "Clues avg(stdev)", "Guesses avg(stdev)",
                  "Stop Early", "Stop Late"):
        assert label in document
    # Pairs are named as the paper names them.
    assert "alpha - beta" in document


def test_empty_stratum_says_so_instead_of_rendering_a_headerless_table():
    assert "no completed games" in script.to_markdown(pd.DataFrame())
