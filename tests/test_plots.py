import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from codenames_heb import plots  # noqa: E402


@pytest.fixture(autouse=True)
def close_figures():
    """Figures built through pyplot are retained until closed, and matplotlib
    warns once the session passes 20 open ones. Every test here builds at least
    one, so they are closed as they go rather than left to accumulate."""
    yield
    matplotlib.pyplot.close("all")


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


# --- the clue-count floor axis (M4) --------------------------------------


@pytest.fixture
def floor_games():
    """2 models x 3 floors x 2 styles x 4 games, 3 wins and 1 loss per cell."""
    records = []
    for model in ("vendor/alpha", "vendor/beta"):
        for floor in ("free", "min2", "min3"):
            for style in ("dual_0", "dual_100"):
                for trial in range(4):
                    win = trial < 3
                    records.append(
                        {
                            "model": model, "method": "strong_hebrew",
                            "guesser_model": model, "board_style": style,
                            "count_constraint": floor,
                            "board_seed": trial, "trial": trial,
                            "outcome": "win" if win else "loss",
                            "completed": True,
                            "is_win": float(win), "is_loss": float(not win),
                            "game_length": 8.0 + trial,
                        }
                    )
    return pd.DataFrame(records)


@pytest.fixture
def floor_rounds(floor_games):
    """Three rounds per game, so every (model, floor, round) point holds 8.

    One game gets a fourth round on its own, which is the point below the
    minimum the figure has to drop.
    """
    ambition = {"free": 1.0, "min2": 2.0, "min3": 3.0}
    records = []
    for row in floor_games.itertuples(index=False):
        for rnd in (1, 2, 3):
            floor = row.count_constraint
            required = None if floor == "free" else int(floor.removeprefix("min"))
            # The endgame cap: by round 3 there are fewer targets left hidden
            # than the nominal floor, so the floor actually in force is lower.
            if required == 3 and rnd == 3:
                required = 2
            records.append(
                {
                    "model": row.model, "method": row.method,
                    "guesser_model": row.guesser_model,
                    "board_style": row.board_style,
                    "count_constraint": floor,
                    "board_seed": row.board_seed, "trial": row.trial,
                    "round": rnd,
                    "count": ambition[floor],
                    "required_count": required,
                    "n_correct": 1, "yield_ratio": 1.0 / ambition[floor],
                    "intended_recall": 0.5, "intended_precision": 1.0,
                    "intended_jaccard": 0.5, "n_lucky": 0,
                    "stop_class": "stopped_at_quota" if rnd < 3 else "miss_before_quota",
                    "turn_outcome": "stopped_early" if rnd < 3 else "hit_civilian",
                    "first_miss_role": None if rnd < 3 else "civilian",
                    "first_miss_is_dual": None if rnd < 3 else 1.0,
                }
            )
    records.append({**records[0], "round": 4})
    return pd.DataFrame(records)


def _lines(ax, style: str):
    return [line for line in ax.get_lines() if line.get_linestyle() == style]


def test_count_floor_order_sorts_numerically_not_alphabetically():
    # `sorted()` puts min10 between free and min2, which draws the ladder in
    # the wrong order the moment a run carries a two-digit floor.
    assert plots.count_floor_order(["min3", "min10", "free", "min2"]) == [
        "free", "min2", "min3", "min10",
    ]


def test_win_rate_by_floor_puts_the_floor_on_the_x_axis(floor_games):
    fig = plots.fig_win_rate_by_count_floor(floor_games)

    assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == [
        "free", "min2", "min3",
    ]


def test_win_rate_by_floor_labels_each_bar_with_its_own_n(floor_games):
    # A floor x style panel holds 8 games, but each bar is one model's 4.
    fig = plots.fig_win_rate_by_count_floor(floor_games)

    assert set(_annotations(fig)) == {"4"}


def test_length_by_floor_keeps_wins_and_losses_apart(floor_games):
    # Models are pooled, so a floor x style cell holds 2 x 3 = 6 wins against
    # 2 x 1 = 2 losses. Pooling them would hide which one the floor moved.
    fig = plots.fig_game_length_by_count_floor(floor_games)

    assert sorted(set(_annotations(fig))) == ["2", "6"]


def test_count_by_round_draws_a_line_per_floor_in_every_model_panel(floor_rounds):
    fig = plots.fig_count_by_round(floor_rounds)

    assert [ax.get_title() for ax in fig.axes] == ["alpha", "beta"]
    assert all(len(_lines(ax, "-")) == 3 for ax in fig.axes)


def test_count_by_round_traces_the_capped_floor_only_where_one_was_set(floor_rounds):
    fig = plots.fig_count_by_round(floor_rounds)

    dashed = _lines(fig.axes[0], "--")
    # Free-choice rounds have no floor to trace, so only min2 and min3 do.
    assert len(dashed) == 2
    # min3's floor is capped to 2 by round 3 — the dashed line has to show
    # that, or a flat line at 3 would claim the floor still bound at the end.
    assert [list(line.get_ydata()) for line in dashed] == [[2, 2, 2], [3, 3, 2]]


def test_count_by_round_drops_points_below_the_minimum_rounds(floor_rounds):
    # Round 4 exists in exactly one game. Plotting it would end every panel
    # on a point that is one game's noise.
    fig = plots.fig_count_by_round(floor_rounds)

    assert max(max(line.get_xdata()) for line in _lines(fig.axes[0], "-")) == 3


@pytest.mark.parametrize(
    "figure, frame_name",
    [
        ("fig_win_rate_by_count_floor", "floor_games"),
        ("fig_game_length_by_count_floor", "floor_games"),
        ("fig_count_by_round", "floor_rounds"),
    ],
)
def test_floor_figures_are_skipped_on_a_run_with_one_floor(
    figure, frame_name, floor_games, floor_rounds, request
):
    # Every run before M4 has a single arm; a one-bar "comparison" implies a
    # contrast the run cannot make.
    frame = request.getfixturevalue(frame_name)
    single = frame[frame["count_constraint"] == "free"]

    assert getattr(plots, figure)(single) is None


def test_save_all_writes_the_floor_figures(tmp_path, floor_games, floor_rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds, data.boards = floor_games, floor_rounds, {}

    saved = plots.save_all(data, tmp_path)

    assert {"11_win_rate_by_count_floor", "12_game_length_by_count_floor",
            "13_count_by_round"} <= set(saved)
    assert all(path.exists() for path in saved.values())


@pytest.fixture
def long_floor_rounds(floor_rounds):
    """M4's real shape: four codemasters whose games run to different lengths.

    Both the panel count and the *spread* of panel lengths matter. Panels are
    not x-shared, so each one gets its own automatic tick step — 2 rounds at
    14, but 2.5 at 19 and 5 at 20. A fixture where every panel is the same
    length cannot see that, because one step then suits all four.
    """
    lengths = {
        "vendor/alpha": 14, "vendor/beta": 15,
        "vendor/gamma": 19, "vendor/delta": 20,
    }
    seed = floor_rounds[
        (floor_rounds["round"] == 1) & (floor_rounds["model"] == "vendor/alpha")
    ]
    records = []
    for model, last in lengths.items():
        for row in seed.itertuples(index=False):
            for rnd in range(1, last + 1):
                records.append({**row._asdict(), "model": model, "round": rnd})
    return pd.DataFrame(records)


def _digit_labels(ax):
    return [t for t in ax.texts if t.get_text().isdigit()]


def test_count_by_round_thins_the_n_row_on_a_long_game(long_floor_rounds):
    # 20 rounds x 3 floors is 60 three-digit labels across three rows in a
    # panel a few inches wide — they overprint into an unreadable smear.
    fig = plots.fig_count_by_round(long_floor_rounds)

    per_floor = len(_digit_labels(fig.axes[0])) / 3
    assert per_floor <= 10


def test_count_by_round_ticks_rounds_as_whole_numbers(long_floor_rounds):
    # Rounds are counts. Left to itself matplotlib ticks the 19-round panel
    # every 2.5 rounds, which invites reading a half-round off the axis.
    fig = plots.fig_count_by_round(long_floor_rounds)

    ticks = [float(t) for ax in fig.axes for t in ax.get_xticks()]
    assert ticks and all(t.is_integer() for t in ticks)


def test_count_by_round_ticks_every_panel_the_same_way(long_floor_rounds):
    # Panels are read against each other. Automatic ticks give the four M4
    # panels steps of 2, 2, 2.5 and 5, so the same horizontal distance means
    # a different number of rounds in each.
    fig = plots.fig_count_by_round(long_floor_rounds)

    steps = {
        round(float(ax.get_xticks()[1]) - float(ax.get_xticks()[0]), 6)
        for ax in fig.axes
    }
    assert len(steps) == 1
