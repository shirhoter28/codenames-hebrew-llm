import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from codenames_heb import plots  # noqa: E402


@pytest.fixture
def games():
    """Two models x two methods x two styles x 3 games, so every bar has n=3."""
    records = []
    for model in ("vendor/alpha", "vendor/beta"):
        for method in ("strong_hebrew", "translate_pipeline"):
            for style in ("dual_0", "dual_100"):
                for trial in range(3):
                    win = trial < 2
                    records.append(
                        {
                            "model": model, "method": method, "board_style": style,
                            "board_seed": trial, "trial": trial,
                            "outcome": "win" if win else "loss",
                            "completed": True,
                            "is_win": float(win), "is_loss": float(not win),
                            "game_length": 8.0 + trial,
                        }
                    )
    return pd.DataFrame(records)


@pytest.fixture
def rounds(games):
    records = []
    for row in games.itertuples(index=False):
        for rnd in range(2):
            records.append(
                {
                    "model": row.model, "method": row.method,
                    "board_style": row.board_style, "board_seed": row.board_seed,
                    "trial": row.trial, "round": rnd + 1,
                    "count": 2, "n_correct": 1, "yield_ratio": 0.5,
                    "intended_recall": 0.5, "intended_precision": 1.0,
                    "intended_jaccard": 0.5, "n_lucky": 0,
                    "stop_class": "early_stop_true" if rnd else "miss_before_quota",
                    "turn_outcome": "stopped_early" if rnd else "hit_civilian",
                    "first_miss_role": None if rnd else "civilian",
                    "first_miss_is_dual": None if rnd else float(row.board_style != "dual_0"),
                }
            )
    return pd.DataFrame(records)


def _annotations(fig):
    return [
        text.get_text()
        for ax in fig.axes
        for text in ax.texts
        if text.get_text().isdigit()
    ]


def test_bars_are_labelled_with_their_own_n_not_the_facet_total(games):
    # The facet holds 6 games (2 methods x 3), but each bar holds 3. Labelling
    # the panel would overstate what every bar rests on.
    fig = plots.fig_outcome_composition(games)

    assert set(_annotations(fig)) == {"3"}


def test_box_labels_track_the_split_between_wins_and_losses(games):
    fig = plots.fig_game_length(games)

    # Boxes pool both methods, so each model x style pair holds
    # 2 methods x 2 wins = 4 wins against 2 methods x 1 loss = 2 losses.
    # The win and loss boxes must not both claim the pair's total of 6.
    assert sorted(set(_annotations(fig))) == ["2", "4"]


def test_win_length_ladder_counts_only_the_wins(games):
    # Each model x method x style cell holds 3 games but only 2 wins. A point
    # labelled 3 would mean the losses — which end early by hitting the
    # assassin — were averaged into the cost of a win.
    fig = plots.fig_win_length_ladder(games)

    assert set(_annotations(fig)) == {"2"}


def test_win_length_ladder_marks_a_style_a_model_never_won(games):
    starved = games[~((games["model"] == "vendor/beta")
                      & (games["board_style"] == "dual_100")
                      & (games["is_win"] == 1.0))]

    fig = plots.fig_win_length_ladder(starved)

    # The model keeps its line and its colour slot; the empty style reads 0
    # rather than silently vanishing.
    assert "0" in _annotations(fig)


def test_round_figures_are_labelled_in_rounds(rounds):
    # Bars pool both methods here: 2 methods x 3 games x 2 rounds = 12.
    fig = plots.fig_intended_overlap(rounds)

    assert set(_annotations(fig)) == {"12"}


def test_facet_titles_name_the_style_without_a_misleading_total(games):
    fig = plots.fig_outcome_composition(games)

    assert [ax.get_title() for ax in fig.axes] == ["dual_0", "dual_100"]


@pytest.mark.parametrize(
    "name",
    ["01_outcome_composition", "02_game_length", "03_ambiguity_ladder",
     "04_stop_behaviour", "05_intended_overlap", "06_ambition_vs_yield",
     "09_win_length_ladder"],
)
def test_every_figure_builds(name, games, rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds, data.boards = games, rounds, {}

    assert plots.FIGURES[name](data) is not None


def test_dual_miss_figure_is_skipped_without_ambiguity_data(rounds):
    class Data:
        pass

    data = Data()
    data.rounds, data.boards = rounds, {}

    assert plots.FIGURES["07_dual_miss_lift"](data) is None


def test_save_all_writes_a_png_per_figure(tmp_path, games, rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds, data.boards = games, rounds, {}

    saved = plots.save_all(data, tmp_path)

    assert saved and all(path.exists() for path in saved.values())
