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
                            "first_guess_hit": 0.6, "first_guess_baseline": 0.3,
                            "first_guess_lift": 0.3,
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
                    "count_constraint": "free", "clue": None, "intended_targets": None,
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


def _boxes(ax):
    return [patch for patch in ax.patches if patch.get_label() == ""] and [
        line for line in ax.get_lines() if line.get_linestyle() == "-"
    ]


def test_bars_are_labelled_with_their_own_n_not_the_facet_total(games):
    # The facet holds 6 games (2 methods x 3), but each bar holds 3. Labelling
    # the panel would overstate what every bar rests on.
    fig = plots.fig_outcome_composition(games)

    assert set(_annotations(fig)) == {"3"}


def test_box_labels_track_the_split_between_wins_and_losses(games):
    fig = plots.fig_game_length(games)

    # A model x method x style cell holds 3 games: 2 wins against 1 loss. The
    # win and loss boxes must not both claim the cell's total.
    assert sorted(set(_annotations(fig))) == ["1", "2"]


def test_game_length_separates_the_two_prompt_methods(games):
    """Method is the other thing the codemaster side varies; pooling it here
    would make this the one game-level figure that hides it."""
    fig = plots.fig_game_length(games)

    # 2 models x 2 methods x 2 outcomes = 8 boxes to a panel, not 4.
    assert len(_annotations(fig)) == len(fig.axes) * 8


def test_facet_titles_name_the_style_without_a_misleading_total(games):
    fig = plots.fig_outcome_composition(games)

    assert [ax.get_title() for ax in fig.axes] == ["dual_0", "dual_100"]


@pytest.mark.parametrize("name", ["01_outcome_composition", "02_game_length",
                                  "09_first_guess_vs_chance"])
def test_every_figure_builds(name, games, rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds, data.boards = games, rounds, {}

    assert plots.FIGURES[name](data) is not None


def test_save_all_writes_a_png_per_figure(tmp_path, games, rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds, data.boards = games, rounds, {}

    saved = plots.save_all(data, tmp_path)

    assert saved and all(path.exists() for path in saved.values())


# --- the first guess against its baseline --------------------------------


def test_first_guess_figure_draws_the_baseline_next_to_the_observed_rate(games):
    """The lift is a difference, and a difference cannot be read without the
    thing it is a difference from — the baseline moves with board style and
    with how long the game ran, so it is drawn rather than assumed."""
    fig = plots.fig_first_guess_vs_chance(games)

    labels = [text.get_text() for text in fig.legends[0].get_texts()]
    assert any("observed" in label for label in labels)
    assert any("chance" in label for label in labels)


def test_first_guess_figure_states_the_lift_over_each_pair(games):
    fig = plots.fig_first_guess_vs_chance(games)

    # 0.6 observed against a 0.3 pool.
    gaps = [t.get_text() for ax in fig.axes for t in ax.texts if "+" in t.get_text()]
    assert gaps and set(gaps) == {"+0.30"}


def test_first_guess_figure_is_skipped_without_its_baseline(games):
    """Runs logged before the baseline was recorded carry the lift but not its
    two halves; half the figure would be a bar of NaN."""
    older = games.drop(columns=["first_guess_baseline"])

    assert plots.fig_first_guess_vs_chance(older) is None


# --- the stratified grids ------------------------------------------------


@pytest.fixture
def grid_games():
    """A crossed run with both extra factors: 2 codemasters x 2 guessers x
    2 methods x 3 floors x 2 styles x 2 games, so every bar of a grid holds 2.
    """
    records = []
    for model in ("vendor/alpha", "vendor/beta"):
        for guesser in ("vendor/alpha", "vendor/beta"):
            for method in ("strong_hebrew", "translate_pipeline"):
                for floor in ("free", "min2", "min3"):
                    for style in ("dual_0", "dual_100"):
                        for trial in range(2):
                            win = trial < 1
                            records.append(
                                {
                                    "model": model, "guesser_model": guesser,
                                    "method": method, "count_constraint": floor,
                                    "board_style": style,
                                    "board_seed": trial, "trial": trial,
                                    "outcome": "win" if win else "loss",
                                    "completed": True,
                                    "is_win": float(win), "is_loss": float(not win),
                                    "game_length": 8.0 + trial,
                                    "first_guess_hit": 0.6,
                                    "first_guess_baseline": 0.3,
                                    "first_guess_lift": 0.3,
                                }
                            )
    return pd.DataFrame(records)


@pytest.mark.parametrize(
    "figure", ["fig_win_rate_grid", "fig_outcome_grid", "fig_game_length_grid"]
)
@pytest.mark.parametrize(
    "row_col, n_rows", [("count_constraint", 3), ("guesser_model", 2)]
)
def test_grid_has_one_panel_per_row_level_and_board_style(
    figure, row_col, n_rows, grid_games
):
    fig = getattr(plots, figure)(grid_games, row_col)

    # 2 board styles across, `n_rows` down.
    assert len(fig.axes) == n_rows * 2


@pytest.mark.parametrize(
    "figure", ["fig_win_rate_grid", "fig_outcome_grid", "fig_game_length_grid"]
)
def test_grid_is_skipped_when_the_row_factor_does_not_vary(figure, grid_games):
    """A one-row "grid" is the plain faceted figure under a heading promising a
    contrast the run cannot make. Every run before M4 has a single floor."""
    single = grid_games[grid_games["count_constraint"] == "free"]

    assert getattr(plots, figure)(single, "count_constraint") is None


def test_grid_orders_the_floors_numerically_not_alphabetically(grid_games):
    # `min10` sorts between `free` and `min2` as a string, which draws the
    # designed ladder out of sequence.
    renamed = grid_games.replace({"min3": "min10"})

    fig = plots.fig_win_rate_grid(renamed, "count_constraint")

    rows = [text.get_text() for ax in fig.axes for text in ax.texts
            if text.get_text() in {"free", "min2", "min10"}]
    assert rows == ["free", "min2", "min10"]


def test_grid_names_its_rows_and_keeps_the_columns_on_board_style(grid_games):
    fig = plots.fig_win_rate_grid(grid_games, "guesser_model")

    # Column titles are the styles, on the top row only — a row of repeated
    # titles down the grid would leave nothing naming the rows.
    assert [ax.get_title() for ax in fig.axes if ax.get_title()] == [
        "dual_0", "dual_100",
    ]
    rows = [t.get_text() for ax in fig.axes for t in ax.texts if "vendor" in t.get_text()
            or t.get_text() in {"alpha", "beta"}]
    assert rows == ["alpha", "beta"]


def test_grid_bars_are_labelled_with_the_games_behind_that_bar(grid_games):
    # A floor x style panel holds 16 games, but a codemaster x method bar in
    # it holds 4 — 2 guessers x 2 trials. Labelling the panel would overstate
    # what each bar rests on fourfold.
    fig = plots.fig_win_rate_grid(grid_games, "count_constraint")

    assert set(_annotations(fig)) == {"4"}


def test_win_rate_grid_uses_wilson_not_wald_intervals(grid_games):
    """A cell that went n-for-n has a Wald SE of exactly 0, which draws as
    certainty. Every bar here is 1-for-2, but the point is that the interval
    survives a cell with no variance at all."""
    swept = grid_games.copy()
    swept["outcome"] = "win"
    swept["is_win"] = 1.0

    fig = plots.fig_win_rate_grid(swept, "count_constraint")

    # The interval is drawn as a LineCollection of vertical segments, one per
    # bar. A Wald interval on a swept cell is a segment of zero length.
    spans = [
        abs(segment[1][1] - segment[0][1])
        for ax in fig.axes
        for collection in ax.collections
        for segment in collection.get_segments()
    ]
    assert spans and min(spans) > 0


def test_game_length_grid_keeps_outcome_and_method_apart(grid_games):
    """Halving the boxes by pooling the outcomes would hide whether a floor
    that shortens games is winning faster or dying sooner, which is the whole
    question length is asked to answer."""
    fig = plots.fig_game_length_grid(grid_games, "count_constraint")

    # 2 codemasters x 2 methods x 2 outcomes = 8 boxes in each of 6 panels.
    assert len(_annotations(fig)) == 6 * 8


def test_grids_hold_every_codemaster_slot_open_in_every_panel(grid_games):
    """A grid is read down a column. If a panel that happens to hold no games
    for one model dropped its slot, the panels would stop lining up."""
    starved = grid_games[
        ~((grid_games["model"] == "vendor/beta")
          & (grid_games["count_constraint"] == "min3"))
    ]

    fig = plots.fig_win_rate_grid(starved, "count_constraint")

    assert all(
        [t.get_text() for t in ax.get_xticklabels()] in ([], ["alpha", "beta"])
        for ax in fig.axes
    )
    # The empty cells read as an explicit 0 rather than silently vanishing.
    assert "0" in _annotations(fig)


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
                    "clue": None, "intended_targets": None,
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


def test_count_by_round_is_skipped_on_a_run_with_one_floor(floor_rounds):
    # Every run before M4 has a single arm; a one-line "comparison" implies a
    # contrast the run cannot make.
    single = floor_rounds[floor_rounds["count_constraint"] == "free"]

    assert plots.fig_count_by_round(single) is None


def test_save_all_writes_the_stratified_grids(tmp_path, grid_games, floor_rounds):
    class Data:
        pass

    data = Data()
    data.games, data.rounds, data.boards = grid_games, floor_rounds, {}

    saved = plots.save_all(data, tmp_path)

    assert {
        "03_win_rate_by_floor", "04_win_rate_by_guesser",
        "05_outcome_mix_by_floor", "06_outcome_mix_by_guesser",
        "07_game_length_by_floor", "08_game_length_by_guesser",
    } <= set(saved)
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


@pytest.fixture
def agreement_rounds():
    """Round-1 draws over 2 styles x 2 floors x 2 codemasters x 2 methods.

    Four guesser replicates per cell, which is what makes a cell a repeat draw
    from one identical prompt. `v/alpha` always repeats its clue; `v/beta`
    never does, but always aims at the same word — the case that separates
    unstable phrasing from an unstable strategy.
    """
    records = []
    for style in ("dual_0", "dual_100"):
        for floor in ("free", "min2"):
            for method in ("strong_hebrew", "translate_pipeline"):
                for i in range(4):
                    records.append({
                        "board_style": style, "board_seed": 0,
                        "model": "v/alpha", "guesser_model": f"g{i}",
                        "method": method, "count_constraint": floor,
                        "round": 1, "clue": "בית",
                        "intended_targets": ["א", "ב"], "count": 2,
                        "n_correct": 1, "stop_class": "stopped_at_quota",
                        "first_miss_role": None,
                    })
                    records.append({
                        "board_style": style, "board_seed": 0,
                        "model": "v/beta", "guesser_model": f"g{i}",
                        "method": method, "count_constraint": floor,
                        "round": 1, "clue": f"קלו{i}",
                        "intended_targets": ["א"], "count": 1,
                        "n_correct": 1, "stop_class": "stopped_at_quota",
                        "first_miss_role": None,
                    })
    return pd.DataFrame(records)


def test_self_consistency_grid_has_a_panel_per_style_and_floor(agreement_rounds):
    fig = plots.fig_self_consistency_grid(agreement_rounds, "count_constraint")

    # 2 styles across x 2 floors down.
    assert len(fig.axes) == 4
    assert [ax.get_title() for ax in fig.axes[:2]] == ["dual_0", "dual_100"]


def test_self_consistency_grid_separates_stable_from_unstable(agreement_rounds):
    fig = plots.fig_self_consistency_grid(agreement_rounds, "count_constraint")

    # alpha repeats its clue (unanimous 1.0), beta never does (0.0).
    heights = sorted(round(p.get_height(), 3) for p in fig.axes[0].patches)
    assert heights[0] == 0.0
    assert heights[-1] == 1.0


def test_self_consistency_grid_marks_target_set_agreement(agreement_rounds):
    # beta's clue changes every draw but its aim never does. Without the
    # self_jaccard marker the figure would call that pure instability.
    fig = plots.fig_self_consistency_grid(agreement_rounds, "count_constraint")

    markers = [line for line in fig.axes[0].get_lines()
               if line.get_linestyle() == "None"]
    assert markers
    assert max(max(m.get_ydata()) for m in markers) == 1.0


def test_cross_model_agreement_grid_builds(agreement_rounds):
    fig = plots.fig_cross_model_agreement_grid(agreement_rounds, "count_constraint")

    assert fig is not None
    assert len(fig.axes) == 4


def test_agreement_grids_are_skipped_when_the_row_factor_has_one_level(agreement_rounds):
    # facet_grid's contract: a one-row "grid" promises a contrast the run
    # cannot make.
    single = agreement_rounds[agreement_rounds["count_constraint"] == "free"]

    assert plots.fig_self_consistency_grid(single, "count_constraint") is None
    assert plots.fig_cross_model_agreement_grid(single, "count_constraint") is None
