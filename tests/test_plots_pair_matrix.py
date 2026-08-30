"""The codemaster x guesser figure, and the guesser-aware regrouping.

The 4x4 grid's headline deliverable is a pair matrix: it is the only figure
that shows an interaction, which is what crossing the guesser buys.
"""

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from codenames_heb import plots  # noqa: E402

MODELS = ("vendor/alpha", "vendor/beta")


@pytest.fixture
def grid_games():
    """A crossed run: every codemaster paired with every guesser."""
    records = []
    for model in MODELS:
        for guesser in MODELS:
            for style in ("dual_0", "dual_100"):
                for trial in range(3):
                    win = trial < 2
                    records.append(
                        {
                            "model": model,
                            "guesser_model": guesser,
                            "method": "strong_hebrew",
                            "board_style": style,
                            "board_seed": trial,
                            "trial": trial,
                            "outcome": "win" if win else "loss",
                            "completed": True,
                            "is_win": float(win),
                            "is_loss": float(not win),
                            "game_length": 8.0 + trial,
                            "first_guess_lift": 0.2 if guesser == model else 0.5,
                        }
                    )
    return pd.DataFrame(records)


@pytest.fixture
def fixed_guesser_games(grid_games):
    """The pre-M3 shape: one guesser for the whole run."""
    return grid_games[grid_games["guesser_model"] == MODELS[0]].copy()


def test_pair_matrix_has_one_cell_per_codemaster_guesser_pair(grid_games):
    fig = plots.fig_pair_matrix(grid_games)

    assert fig is not None
    # One image per metric panel, each a 2x2 grid of pairs.
    images = [im for ax in fig.axes for im in ax.get_images()]
    assert images, "expected a heatmap image"
    assert all(im.get_array().shape == (2, 2) for im in images)


def test_pair_matrix_is_skipped_when_the_guesser_is_fixed(fixed_guesser_games):
    """With one guesser there is no interaction to show, and a 4x1 strip would
    imply a comparison the run cannot make."""
    assert plots.fig_pair_matrix(fixed_guesser_games) is None


def test_pair_matrix_reports_the_metric_the_run_is_powered_on(grid_games):
    fig = plots.fig_pair_matrix(grid_games)

    titles = " ".join(ax.get_title().lower() for ax in fig.axes)
    assert "lift" in titles


def test_pair_matrix_orients_codemasters_and_guessers_on_named_axes(grid_games):
    """A matrix whose axes are unlabelled cannot be read in either direction."""
    fig = plots.fig_pair_matrix(grid_games)

    labels = " ".join(
        (ax.get_xlabel() + " " + ax.get_ylabel()).lower() for ax in fig.axes
    )
    assert "codemaster" in labels and "guesser" in labels


def test_pair_matrix_prints_a_margin_mean_per_row_and_column(grid_games):
    """The docstring's advice is to read the margins, so they have to be on the
    figure. A 4x4 grid splits a run sixteen ways and a single cell running hot
    or cold is usually not evidence."""
    fig = plots.fig_pair_matrix(grid_games)

    ax = fig.axes[0]
    ticks = [label.get_text() for label in ax.get_xticklabels()]
    assert ticks[-1] == "all guessers"
    assert [label.get_text() for label in ax.get_yticklabels()][-1] == "all codemasters"
    # 2x2 pairs + a row margin, a column margin and the overall cell.
    assert len([t for t in ax.texts if "n=" in t.get_text()]) == 4 + 2 + 2 + 1


def test_pair_matrix_margins_come_from_the_games_not_the_cell_means(grid_games):
    """Averaging the row of cell means only agrees with the model's own mean
    when every cell holds the same number of games. A pooled or partially-run
    design breaks that, and the margin must still report the true mean."""
    lopsided = grid_games.drop(
        grid_games[
            (grid_games["model"] == MODELS[0])
            & (grid_games["guesser_model"] == MODELS[1])
        ].index[:5]
    )
    fig = plots.fig_pair_matrix(lopsided)

    win_panel = fig.axes[-1] if "win" in fig.axes[-1].get_title() else fig.axes[1]
    expected = lopsided[lopsided["model"] == MODELS[0]]["is_win"].mean()
    margins = [t.get_text() for t in win_panel.texts if "n=" in t.get_text()]
    assert f"{expected:.2f}" in " ".join(margins)


def test_pair_matrix_outlines_the_self_play_diagonal(grid_games):
    """"Did the model do better with itself" is a different question from the
    rest of the grid, and should not have to be found by counting."""
    fig = plots.fig_pair_matrix(grid_games)

    outlines = [
        patch for patch in fig.axes[0].patches if not patch.get_fill()
    ]
    assert len(outlines) == len(MODELS)


def test_the_registry_offers_the_pair_matrix():
    assert any("pair_matrix" in name for name in plots.FIGURES)


def test_guesser_side_figures_group_by_guesser_when_it_varies(grid_games):
    assert plots._actor_column(grid_games) == "guesser_model"


def test_guesser_side_figures_fall_back_to_codemaster_when_it_does_not(
    fixed_guesser_games,
):
    assert plots._actor_column(fixed_guesser_games) == "model"
