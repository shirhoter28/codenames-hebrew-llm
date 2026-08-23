import json

import pandas as pd
import pytest

from codenames_heb.analysis import (
    comparison_power,
    STOP_CLASSES,
    classify_stop,
    intended_overlap,
    load_run,
    scaling_projection,
    summarize,
    wilson_interval,
)


# --- classify_stop -------------------------------------------------------
#
# The taxonomy exists because `turn_outcome == "stopped_early"` conflates two
# opposite behaviours: stopping short of the codemaster's count (a real early
# stop) and stopping *at* it after declining the bonus guess (correct play).


def test_miss_before_reaching_the_count():
    assert (
        classify_stop("hit_opponent", n_correct=0, count=2, game_won_this_round=False)
        == "miss_before_quota"
    )


def test_miss_after_reaching_the_count_is_a_blown_bonus_guess():
    assert (
        classify_stop("hit_civilian", n_correct=2, count=2, game_won_this_round=False)
        == "miss_on_bonus_guess"
    )


def test_stopping_short_of_the_count_is_a_true_early_stop():
    assert (
        classify_stop("stopped_early", n_correct=1, count=2, game_won_this_round=False)
        == "early_stop_true"
    )


def test_stopping_at_the_count_is_declining_the_bonus_not_an_early_stop():
    assert (
        classify_stop("stopped_early", n_correct=1, count=1, game_won_this_round=False)
        == "stopped_at_quota"
    )


def test_all_correct_with_bonus_guess_taken():
    assert (
        classify_stop("all_correct", n_correct=3, count=2, game_won_this_round=False)
        == "bonus_taken_correct"
    )


def test_all_correct_because_the_last_target_was_revealed_is_not_a_choice():
    # The round ended because the game was won, not because the guesser
    # decided anything — it must not be scored as stop behaviour.
    assert (
        classify_stop("all_correct", n_correct=1, count=2, game_won_this_round=True)
        == "game_won_midround"
    )


def test_count_zero_has_no_quota_to_stop_at():
    assert (
        classify_stop("stopped_early", n_correct=1, count=0, game_won_this_round=False)
        == "no_quota"
    )


def test_guesser_failure_is_not_a_stop_decision():
    assert (
        classify_stop("guesser_failure", n_correct=1, count=2, game_won_this_round=False)
        == "guesser_failure"
    )


def test_every_classification_is_a_known_class():
    cases = [
        ("hit_opponent", 0, 2), ("hit_assassin", 2, 2), ("stopped_early", 1, 3),
        ("stopped_early", 2, 2), ("all_correct", 3, 2), ("all_correct", 1, 1),
        ("guesser_failure", 0, 1), ("hit_civilian", 0, 0),
    ]
    for outcome, n_correct, count in cases:
        for won in (True, False):
            assert classify_stop(outcome, n_correct, count, won) in STOP_CLASSES


# --- intended_overlap ----------------------------------------------------


def test_overlap_when_the_guesser_recovers_exactly_what_was_intended():
    result = intended_overlap(["t1", "t2"], ["t1", "t2"])

    assert result["intended_recall"] == 1.0
    assert result["intended_precision"] == 1.0
    assert result["intended_jaccard"] == 1.0
    assert result["n_lucky"] == 0


def test_overlap_counts_correct_words_the_codemaster_never_aimed_at():
    result = intended_overlap(["t1", "t2"], ["t1", "t3"])

    assert result["intended_recall"] == 0.5
    assert result["intended_precision"] == 0.5
    # union is {t1, t2, t3}, intersection is {t1}
    assert result["intended_jaccard"] == pytest.approx(1 / 3)
    assert result["n_lucky"] == 1


def test_overlap_with_no_correct_guesses():
    result = intended_overlap(["t1", "t2"], [])

    assert result["intended_recall"] == 0.0
    assert result["intended_precision"] is None
    assert result["intended_jaccard"] == 0.0
    assert result["n_lucky"] == 0


def test_overlap_is_undefined_without_intended_targets():
    result = intended_overlap([], ["t1"])

    assert result["intended_recall"] is None
    assert result["intended_jaccard"] is None
    assert result["n_lucky"] == 1


# --- wilson_interval -----------------------------------------------------


def test_wilson_interval_stays_inside_zero_one_at_a_degenerate_proportion():
    # The reason we report Wilson at all: at p=0 the Wald SE is 0, which reads
    # as certainty from 5 games.
    lo, hi = wilson_interval(0, 5)

    assert lo == 0.0
    assert 0.0 < hi < 1.0


def test_wilson_interval_matches_known_values():
    lo, hi = wilson_interval(5, 10)

    assert lo == pytest.approx(0.2366, abs=1e-4)
    assert hi == pytest.approx(0.7634, abs=1e-4)


def test_wilson_interval_is_undefined_for_an_empty_sample():
    assert wilson_interval(0, 0) == (None, None)


# --- summarize -----------------------------------------------------------


def test_summarize_reports_mean_se_and_n_per_group():
    df = pd.DataFrame(
        {"model": ["a", "a", "a", "b"], "game_length": [2.0, 4.0, 6.0, 5.0]}
    )

    out = summarize(df, ["model"], ["game_length"]).set_index("model")

    assert out.loc["a", "game_length_mean"] == 4.0
    assert out.loc["a", "game_length_n"] == 3
    # sd = 2.0 over 3 observations
    assert out.loc["a", "game_length_se"] == pytest.approx(2.0 / 3**0.5)


def test_summarize_leaves_se_undefined_for_a_single_observation():
    df = pd.DataFrame({"model": ["b"], "game_length": [5.0]})

    out = summarize(df, ["model"], ["game_length"])

    assert pd.isna(out.loc[0, "game_length_se"])


def test_summarize_skips_nulls_so_per_metric_n_can_differ():
    # Round metrics are NaN when the round was not eligible (e.g. early-stop
    # rate on a count=1 round), so n must be counted per metric, not per group.
    df = pd.DataFrame(
        {"model": ["a"] * 3, "is_early_stop": [1.0, 0.0, None], "count": [2, 2, 1]}
    )

    out = summarize(df, ["model"], ["is_early_stop", "count"])

    assert out.loc[0, "is_early_stop_n"] == 2
    assert out.loc[0, "count_n"] == 3


def test_summarize_adds_wilson_bounds_for_proportions():
    df = pd.DataFrame({"model": ["a"] * 5, "is_loss": [0.0] * 5})

    out = summarize(df, ["model"], ["is_loss"], proportions=["is_loss"])

    assert out.loc[0, "is_loss_mean"] == 0.0
    assert out.loc[0, "is_loss_lo"] == 0.0
    assert out.loc[0, "is_loss_hi"] > 0.0


def test_summarize_without_group_columns_returns_one_row():
    df = pd.DataFrame({"game_length": [2.0, 4.0]})

    out = summarize(df, [], ["game_length"])

    assert len(out) == 1
    assert out.loc[0, "game_length_mean"] == 3.0


# --- loading -------------------------------------------------------------


def _write_run(tmp_path, rows, boards=None, config=None):
    run_dir = tmp_path / "20260101T000000000000Z"
    run_dir.mkdir()
    with (run_dir / "raw.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (run_dir / "boards.json").write_text(
        json.dumps(boards if boards is not None else []), encoding="utf-8"
    )
    (run_dir / "config.yaml").write_text(config or "models: [m]\n", encoding="utf-8")
    return run_dir


def _game(**overrides):
    game = {
        "model": "m", "method": "strong_hebrew", "guesser_model": "g",
        "board_seed": 0, "board_style": "natural", "trial": 0,
        "status": "ok", "outcome": "win", "game_length": 1,
        "targets_found": 9, "target_recovery_rate": 1.0, "assassin_hit": False,
        "terminal_error": None,
        "codemaster_attempts": 2, "codemaster_rejected": 0,
        "codemaster_compliance_rate": 1.0, "codemaster_call_failures": 0,
        "guesser_attempts": 3, "guesser_rejected": 0,
        "guesser_compliance_rate": 1.0, "guesser_call_failures": 0,
        "rejection_reasons": {},
        "rounds": [],
    }
    game.update(overrides)
    return game


def _round(**overrides):
    rnd = {
        "round": 1, "clue": "c", "count": 2, "intended_targets": ["t1", "t2"],
        "reasoning": None, "translation_map": None, "en_clue": None,
        "en_targets": None,
        "guess_sequence": [{"word": "t1", "role": "target"}],
        "error": None, "guesses_before_miss": 1, "turn_outcome": "stopped_early",
        "assassin_hit": False, "target_recovery_rate": 0.5,
        "intended_recall": 0.5, "intended_precision": 1.0,
    }
    rnd.update(overrides)
    return rnd


def test_load_run_rejects_the_pre_multi_round_schema(tmp_path):
    # Runs before 2026-08-15 logged one flat one-shot trial per row, with a
    # `guesses` list and no `rounds` — silently loading them would produce an
    # empty rounds table rather than an error.
    old_row = {"model": "m", "method": "strong_hebrew", "board_seed": 0,
               "trial": 0, "status": "ok", "clue": "c", "count": 2,
               "guesses": ["t1"], "turn_outcome": "stopped_early"}
    run_dir = _write_run(tmp_path, [old_row])

    with pytest.raises(ValueError, match="pre-multi-round schema"):
        load_run(run_dir)


def test_load_run_builds_game_and_round_tables(tmp_path):
    run_dir = _write_run(tmp_path, [_game(rounds=[_round(), _round(round=2)])])

    data = load_run(run_dir)

    assert len(data.games) == 1
    assert len(data.rounds) == 2
    assert data.games.loc[0, "n_rounds"] == 2


def test_round_table_marks_the_round_that_won_the_game(tmp_path):
    # Nine targets per board: the round that reveals the ninth ends because the
    # game is over, not because the guesser chose to stop.
    first = _round(
        round=1,
        count=8,
        intended_targets=[f"t{i}" for i in range(1, 9)],
        guess_sequence=[{"word": f"t{i}", "role": "target"} for i in range(1, 9)],
        turn_outcome="stopped_early",
    )
    second = _round(
        round=2,
        count=2,
        intended_targets=["t9", "t10"],
        guess_sequence=[{"word": "t9", "role": "target"}],
        turn_outcome="all_correct",
    )
    run_dir = _write_run(tmp_path, [_game(rounds=[first, second], game_length=2)])

    rounds = load_run(run_dir).rounds

    assert rounds.loc[0, "game_won_this_round"] == False  # noqa: E712
    assert rounds.loc[1, "game_won_this_round"] == True  # noqa: E712
    assert rounds.loc[1, "stop_class"] == "game_won_midround"


def test_early_stop_rate_excludes_rounds_where_stopping_early_was_impossible(tmp_path):
    # The guesser may not stop before its first correct guess, so a count=1
    # round can never contain an early stop. Counting it in the denominator
    # deflates the rate.
    impossible = _round(round=1, count=1, intended_targets=["t1"])
    real = _round(round=2, count=3, intended_targets=["t1", "t2", "t3"])
    run_dir = _write_run(tmp_path, [_game(rounds=[impossible, real], game_length=2)])

    rounds = load_run(run_dir).rounds

    assert pd.isna(rounds.loc[0, "is_early_stop"])
    assert rounds.loc[1, "is_early_stop"] == 1.0


def test_round_table_flags_whether_the_missed_word_was_ambiguous(tmp_path):
    missed = _round(
        guess_sequence=[
            {"word": "t1", "role": "target"},
            {"word": "x1", "role": "civilian"},
        ],
        turn_outcome="hit_civilian",
    )
    boards = [{"seed": 0, "style": "natural", "words": ["t1", "t2", "x1"],
               "roles": {"t1": "target", "t2": "target", "x1": "civilian"},
               "is_dual": {"t1": False, "t2": False, "x1": True}}]
    run_dir = _write_run(tmp_path, [_game(rounds=[missed])], boards=boards)

    rounds = load_run(run_dir).rounds

    assert rounds.loc[0, "first_miss_role"] == "civilian"
    assert rounds.loc[0, "first_miss_is_dual"] == 1.0


def test_boards_without_ambiguity_data_leave_the_dual_flag_missing(tmp_path):
    # Runs predating board styles wrote boards.json without `style`/`is_dual`.
    missed = _round(
        guess_sequence=[{"word": "x1", "role": "civilian"}],
        turn_outcome="hit_civilian",
    )
    boards = [{"seed": 0, "words": ["x1"], "roles": {"x1": "civilian"}}]
    game = _game(rounds=[missed])
    del game["board_style"]
    run_dir = _write_run(tmp_path, [game], boards=boards)

    data = load_run(run_dir)

    assert pd.isna(data.rounds.loc[0, "first_miss_is_dual"])
    assert data.games.loc[0, "board_style"] == "unspecified"


def test_games_table_separates_completed_games_from_failures(tmp_path):
    rows = [
        _game(outcome="win", trial=0),
        _game(outcome="loss", trial=1, assassin_hit=True),
        _game(outcome="codemaster_failure", trial=2, terminal_error="boom"),
    ]
    run_dir = _write_run(tmp_path, rows)

    games = load_run(run_dir).games

    assert list(games["completed"]) == [True, True, False]
    assert list(games["is_loss"]) == [0.0, 1.0, None] or pd.isna(games.loc[2, "is_loss"])


# --- first-guess lift ----------------------------------------------------
#
# The sharpest signal in the data: whether the round's first guess — the one
# the clue is most responsible for — beat blind chance.


def test_first_guess_lift_scores_the_opening_board_against_nine_of_twenty_five(tmp_path):
    hit = _round(guess_sequence=[{"word": "t1", "role": "target"}])
    run_dir = _write_run(tmp_path, [_game(rounds=[hit])])

    rounds = load_run(run_dir).rounds

    assert rounds.loc[0, "first_guess_hit"] == 1.0
    assert rounds.loc[0, "first_guess_baseline"] == pytest.approx(9 / 25)
    assert rounds.loc[0, "first_guess_lift"] == pytest.approx(1 - 9 / 25)


def test_baseline_follows_the_pool_as_the_board_is_revealed(tmp_path):
    # Targets are found faster than non-targets, so the pool sours as a game
    # goes on. Scoring later rounds against the opening 9/25 would credit every
    # model with a lift it did not earn.
    first = _round(
        round=1,
        count=3,
        intended_targets=["t1", "t2", "t3"],
        guess_sequence=[
            {"word": "t1", "role": "target"},
            {"word": "t2", "role": "target"},
            {"word": "x1", "role": "civilian"},
        ],
        turn_outcome="hit_civilian",
    )
    second = _round(round=2, guess_sequence=[{"word": "x2", "role": "opponent"}],
                    turn_outcome="hit_opponent")
    run_dir = _write_run(tmp_path, [_game(rounds=[first, second], game_length=2)])

    rounds = load_run(run_dir).rounds

    # 2 targets and 3 words gone: 7 targets left among 22 unrevealed words.
    assert rounds.loc[1, "first_guess_baseline"] == pytest.approx(7 / 22)
    assert rounds.loc[1, "first_guess_hit"] == 0.0
    assert rounds.loc[1, "first_guess_lift"] == pytest.approx(-7 / 22)


def test_first_guess_is_unscored_when_the_guesser_never_guessed(tmp_path):
    stalled = _round(guess_sequence=[], turn_outcome="guesser_failure")
    run_dir = _write_run(tmp_path, [_game(rounds=[stalled])])

    rounds = load_run(run_dir).rounds

    assert pd.isna(rounds.loc[0, "first_guess_hit"])
    assert pd.isna(rounds.loc[0, "first_guess_lift"])


def test_game_level_lift_averages_within_the_game_first(tmp_path):
    # Rounds share a board and a revealed set, so they are not independent.
    # Averaging within the game first stops a long game outweighing a short one.
    hit = _round(round=1, guess_sequence=[{"word": "t1", "role": "target"}])
    miss = _round(round=2, guess_sequence=[{"word": "x1", "role": "civilian"}],
                  turn_outcome="hit_civilian")
    run_dir = _write_run(tmp_path, [_game(rounds=[hit, miss], game_length=2)])

    data = load_run(run_dir)
    expected = ((1 - 9 / 25) + (0 - 8 / 24)) / 2

    assert data.games.loc[0, "first_guess_lift"] == pytest.approx(expected)


# --- scaling_projection --------------------------------------------------


def test_parallel_runner_telemetry_is_loaded_when_present(tmp_path):
    run_dir = _write_run(
        tmp_path, [_game(rounds=[_round()], started_at="2026-08-16T03:56:09Z",
                         duration_s=41.2)]
    )
    (run_dir / "run_meta.json").write_text('{"max_workers": 4}', encoding="utf-8")

    data = load_run(run_dir)

    assert data.games.loc[0, "duration_s"] == 41.2
    # duration_s cannot be read without knowing how many games competed for
    # bandwidth alongside it.
    assert data.meta[run_dir.name]["max_workers"] == 4


def test_runs_without_telemetry_still_load(tmp_path):
    # Every run written before the parallel runner existed.
    run_dir = _write_run(tmp_path, [_game(rounds=[_round()])])

    data = load_run(run_dir)

    assert pd.isna(data.games.loc[0, "duration_s"])
    assert data.meta[run_dir.name] == {}


def test_tables_are_sorted_so_completion_order_does_not_leak_in(tmp_path):
    # Under max_workers > 1 raw.jsonl is written in completion order, which is
    # non-deterministic. Reports must not change shape between reruns.
    shuffled = [
        _game(board_seed=2, trial=0, rounds=[_round()]),
        _game(board_seed=0, trial=1, rounds=[_round()]),
        _game(board_seed=0, trial=0, rounds=[_round()]),
    ]
    run_dir = _write_run(tmp_path, shuffled)

    games = load_run(run_dir).games

    assert list(zip(games["board_seed"], games["trial"])) == [(0, 0), (0, 1), (2, 0)]


def test_power_tables_report_every_outcome_variable_a_run_can_be_sized_against():
    # Sizing a run against win rate rather than first-guess lift changes the
    # answer by a large factor, so both must be visible side by side.
    games = pd.DataFrame(
        {
            "model": ["a"] * 4 + ["b"] * 4,
            "method": ["strong_hebrew"] * 8,
            "board_style": ["dual_0"] * 8,
            "completed": [True] * 8,
            "is_win": [1.0, 0.0, 1.0, 0.0] * 2,
            "first_guess_lift": [0.5, 0.3, 0.4, 0.2] * 2,
            "game_length": [4.0, 6.0, 8.0, 10.0] * 2,
            "total_api_calls": [20.0] * 8,
        }
    )

    out = comparison_power(games, candidate_ns=(5,))

    assert {"mdd_win_rate", "mdd_first_guess_lift", "mdd_game_length"} <= set(out.columns)
    # Lift varies far less within a cell than a win/loss coin flip does, so it
    # needs a much smaller run to resolve the same-sized effect.
    assert out.loc[0, "mdd_first_guess_lift"] < out.loc[0, "mdd_win_rate"]


def test_scaling_projection_narrows_the_interval_as_games_per_cell_grow():
    games = pd.DataFrame(
        {
            "model": ["a"] * 4 + ["b"] * 4,
            "method": ["strong_hebrew"] * 8,
            "board_style": ["dual_0"] * 8,
            "completed": [True] * 8,
            "is_win": [1.0, 0.0, 1.0, 0.0] * 2,
            "game_length": [4.0, 6.0, 8.0, 10.0] * 2,
            "total_api_calls": [20.0] * 8,
        }
    )

    out = scaling_projection(games, candidate_ns=(5, 20)).set_index("games_per_cell")

    assert out.loc[5, "win_rate_ci_halfwidth"] > out.loc[20, "win_rate_ci_halfwidth"]
    assert out.loc[20, "api_calls_total"] > out.loc[5, "api_calls_total"]
    # 2 cells (a, b) x 20 games x 20 calls
    assert out.loc[20, "api_calls_total"] == pytest.approx(800.0)


# --- re-scoring pre-2026-08-22 runs --------------------------------------
#
# Runs played before the opposing team could win carry no `loss_reason`. The
# reveal sequence is unaffected by a terminal rule the players were never
# told about, so those games can be re-scored from their own logs — but the
# rounds after the opposition ran out of words did not happen under the new
# rule and must be dropped.


def _opponent_round(n_opponents: int, **overrides):
    rnd = _round(
        guess_sequence=[{"word": f"o{i}", "role": "opponent"} for i in range(n_opponents)],
        turn_outcome="hit_opponent",
        guesses_before_miss=0,
    )
    rnd.update(overrides)
    return rnd


def _board_json(n_opponents=8, seed=0, style="natural"):
    roles = {f"o{i}": "opponent" for i in range(n_opponents)}
    roles.update({f"t{i}": "target" for i in range(9)})
    return [{"seed": seed, "style": style, "words": list(roles), "roles": roles,
             "is_dual": {w: False for w in roles}}]


def test_exhausting_the_opponent_words_rescores_an_old_win_as_a_loss(tmp_path):
    rounds = [
        _opponent_round(8, round=1),
        _round(round=2, guess_sequence=[{"word": "t1", "role": "target"}]),
    ]
    row = _game(outcome="win", game_length=2, targets_found=9, rounds=rounds)
    run_dir = _write_run(tmp_path, [row], boards=_board_json())

    games = load_run(run_dir).games

    assert games.loc[0, "outcome"] == "loss"
    assert games.loc[0, "loss_reason"] == "opponent_words"
    assert bool(games.loc[0, "rescored"]) is True


def test_rescoring_drops_the_rounds_that_would_not_have_been_played(tmp_path):
    rounds = [
        _opponent_round(8, round=1),
        _round(round=2, guess_sequence=[{"word": "t1", "role": "target"}]),
        _round(round=3, guess_sequence=[{"word": "t2", "role": "target"}]),
    ]
    row = _game(outcome="win", game_length=3, targets_found=9, rounds=rounds)
    run_dir = _write_run(tmp_path, [row], boards=_board_json())

    data = load_run(run_dir)

    assert data.games.loc[0, "game_length"] == 1
    assert data.games.loc[0, "targets_found"] == 0
    assert len(data.rounds) == 1


def test_a_game_that_never_exhausts_the_opponent_words_is_left_alone(tmp_path):
    rounds = [_opponent_round(3, round=1)]
    row = _game(outcome="win", game_length=1, targets_found=9, rounds=rounds)
    run_dir = _write_run(tmp_path, [row], boards=_board_json())

    games = load_run(run_dir).games

    assert games.loc[0, "outcome"] == "win"
    assert games.loc[0, "loss_reason"] is None
    assert bool(games.loc[0, "rescored"]) is False
    assert games.loc[0, "opponent_words_revealed"] == 3


def test_a_run_that_already_records_a_loss_reason_is_not_re_derived(tmp_path):
    # A post-2026-08-22 run is authoritative: the runner ended the game itself,
    # so re-deriving could only disagree with what was actually played.
    rounds = [_opponent_round(8, round=1)]
    row = _game(
        outcome="loss", loss_reason="assassin", game_length=1, targets_found=0,
        assassin_hit=True, opponent_words_revealed=8, rounds=rounds,
    )
    run_dir = _write_run(tmp_path, [row], boards=_board_json())

    games = load_run(run_dir).games

    assert games.loc[0, "loss_reason"] == "assassin"
    assert bool(games.loc[0, "rescored"]) is False


def test_rescoring_falls_back_to_the_standard_count_without_board_data(tmp_path):
    # Pre-style runs wrote boards.json without roles; 8 is the only opponent
    # count `generate_board` has ever produced.
    rounds = [_opponent_round(8, round=1)]
    row = _game(outcome="win", game_length=1, targets_found=9, rounds=rounds)
    run_dir = _write_run(tmp_path, [row], boards=[])

    games = load_run(run_dir).games

    assert games.loc[0, "outcome"] == "loss"
    assert games.loc[0, "loss_reason"] == "opponent_words"


def test_an_old_loss_that_kept_its_opponent_words_is_labelled_an_assassin_loss(tmp_path):
    # Pre-2026-08-22 the assassin was the only way to lose, so the outcome
    # alone identifies the reason.
    row = _game(outcome="loss", game_length=1, targets_found=2, assassin_hit=True,
                rounds=[_round(turn_outcome="hit_assassin")])
    run_dir = _write_run(tmp_path, [row], boards=_board_json())

    games = load_run(run_dir).games

    assert games.loc[0, "loss_reason"] == "assassin"
    assert bool(games.loc[0, "rescored"]) is False


# --- the clue-count constraint axis --------------------------------------


def test_runs_without_a_count_constraint_backfill_as_free(tmp_path):
    # Everything played before M4 was free choice; the column must be a stable
    # string, because a column mixing None and int breaks _sort_by_game.
    run_dir = _write_run(tmp_path, [_game(rounds=[_round()])])

    games = load_run(run_dir).games

    assert games.loc[0, "count_constraint"] == "free"


def test_the_recorded_count_constraint_is_kept(tmp_path):
    run_dir = _write_run(tmp_path, [_game(count_constraint="min3", rounds=[_round()])])

    games = load_run(run_dir).games

    assert games.loc[0, "count_constraint"] == "min3"


def test_games_differing_only_by_constraint_are_distinct_rows(tmp_path):
    rows = [
        _game(count_constraint="free", rounds=[_round()]),
        _game(count_constraint="min2", rounds=[_round()]),
        _game(count_constraint="min3", rounds=[_round()]),
    ]
    run_dir = _write_run(tmp_path, rows)

    games = load_run(run_dir).games

    assert sorted(games["count_constraint"]) == ["free", "min2", "min3"]


def test_the_round_table_carries_the_effective_floor(tmp_path):
    # Capped rounds must be separable from rounds where the full floor applied.
    rounds = [_round(round=1, required_count=3), _round(round=2, required_count=1)]
    run_dir = _write_run(tmp_path, [_game(count_constraint="min3", game_length=2, rounds=rounds)])

    table = load_run(run_dir).rounds

    assert list(table["required_count"]) == [3, 1]
