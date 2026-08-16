import csv
import json
from pathlib import Path

import pytest
import yaml

from codenames_heb.board import Board, generate_board
from codenames_heb.experiment import (
    SAME_AS_CODEMASTER,
    ExperimentConfig,
    load_config,
    run_experiment,
    run_game,
)
from codenames_heb.llm_client import FormatFailure
from codenames_heb.words import WordLists


def _word_lists() -> WordLists:
    return WordLists(
        regular=[f"reg{i}" for i in range(40)],
        dual=[f"dual{i}" for i in range(40)],
    )


def _board() -> Board:
    """3 targets, 1 opponent, 1 civilian, 1 assassin — small, fully controllable."""
    return Board(
        seed=1,
        words=["t1", "t2", "t3", "o1", "c1", "a1"],
        roles={
            "t1": "target",
            "t2": "target",
            "t3": "target",
            "o1": "opponent",
            "c1": "civilian",
            "a1": "assassin",
        },
    )


def _two_target_board() -> Board:
    return Board(
        seed=2,
        words=["t1", "t2", "o1", "c1", "a1"],
        roles={"t1": "target", "t2": "target", "o1": "opponent", "c1": "civilian", "a1": "assassin"},
    )


class StubCodemaster:
    """Scripted responses; raises AssertionError if called more than scripted
    (a mismatch between the script and run_game's actual call count is a bug
    in the test, not something to hide)."""

    def __init__(self, responses=None, error=None):
        self.responses = list(responses) if responses is not None else []
        self.error = error

    def give_clue(self, board, required_count=None, revealed=None, stats=None):
        if self.responses:
            return self.responses.pop(0)
        if self.error:
            raise self.error
        raise AssertionError("StubCodemaster.give_clue called more times than scripted")


class StubGuesser:
    """Scripted per-call guesses; an entry of None means 'voluntarily stop'."""

    def __init__(self, guesses=None, error=None):
        self.guesses = list(guesses) if guesses is not None else []
        self.error = error

    def guess_one(self, words, clue, count, correct_so_far, revealed=None, stats=None):
        if self.guesses:
            nxt = self.guesses.pop(0)
            if isinstance(nxt, Exception):  # scripted failure for this one call
                raise nxt
            return nxt
        if self.error:
            raise self.error
        raise AssertionError("StubGuesser.guess_one called more times than scripted")


class AutoCodemaster:
    """Always gives the same trivial clue. run_game never validates a
    codemaster's response against the real board (only the real
    LLMCodemaster does), so this is enough to drive an arbitrary real
    (generate_board-produced) board to completion without scripting exact
    per-game sequences."""

    def give_clue(self, board, required_count=None, revealed=None, stats=None):
        return {"clue": "x", "count": 0, "intended_targets": [], "reasoning": "r"}


class AutoGuesser:
    """Guesses the first still-unrevealed word each round, and stops
    voluntarily the moment it's allowed to (after one correct guess).
    Reveals exactly one new word per round, so any real board is guaranteed
    to terminate (win/loss/max_rounds) within `len(board.words)` rounds."""

    def guess_one(self, words, clue, count, correct_so_far, revealed=None, stats=None):
        if correct_so_far:
            return None
        return words[0]


# --- run_game: single game, full control over board + scripted responses ---


def test_run_game_wins_when_all_targets_found_in_one_round():
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 3, "intended_targets": ["t1", "t2", "t3"], "reasoning": "r"}]
    )
    # count=3 leaves a 4th (bonus) guess in the budget, but the board's last
    # target falls on the 3rd — the round ends there and the guesser is never
    # asked for a 4th, so no voluntary stop is needed to close it out.
    guesser = StubGuesser(guesses=["t1", "t2", "t3"])

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["model"] == "m"
    assert row["method"] == "strong_hebrew"
    assert row["board_seed"] == 1
    assert row["trial"] == 0
    assert row["outcome"] == "win"
    assert row["game_length"] == 1
    assert row["targets_found"] == 3
    assert row["assassin_hit"] is False
    assert row["rounds"][0]["guess_sequence"] == [
        {"word": "t1", "role": "target"},
        {"word": "t2", "role": "target"},
        {"word": "t3", "role": "target"},
    ]
    assert row["rounds"][0]["turn_outcome"] == "all_correct"


def test_run_game_records_a_voluntary_stop_with_targets_still_unfound():
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 3, "intended_targets": ["t1", "t2", "t3"], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["t1", None])

    row = run_game(
        codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0, max_rounds=1
    )

    assert row["rounds"][0]["turn_outcome"] == "stopped_early"
    assert row["targets_found"] == 1


def test_run_game_loses_on_assassin_guess():
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["a1"])

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["outcome"] == "loss"
    assert row["assassin_hit"] is True
    assert row["game_length"] == 1
    assert row["rounds"][0]["turn_outcome"] == "hit_assassin"


def test_run_game_wins_across_multiple_rounds():
    codemaster = StubCodemaster(
        responses=[
            {"clue": "x", "count": 2, "intended_targets": ["t1", "t2"], "reasoning": "r"},
            {"clue": "y", "count": 1, "intended_targets": ["t3"], "reasoning": "r"},
        ]
    )
    guesser = StubGuesser(guesses=["t1", "t2", None, "t3", None])

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["outcome"] == "win"
    assert row["game_length"] == 2
    assert [r["clue"] for r in row["rounds"]] == ["x", "y"]


def test_run_game_round_stops_at_budget_cap_without_voluntary_stop():
    # count=1 -> budget is 2 guesses; both happen to be correct, so the round
    # ends because the budget ran out, not because the guesser chose to stop.
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["t1", "t2"])

    row = run_game(
        codemaster, guesser, _two_target_board(), model="m", method="strong_hebrew", trial=0
    )

    assert row["rounds"][0]["turn_outcome"] == "all_correct"
    assert row["outcome"] == "win"
    assert row["game_length"] == 1


def test_run_game_round_ends_when_all_targets_found_even_with_budget_left():
    # count=2 -> a 3-guess budget, but the board only holds 2 targets. Once
    # both are revealed the game is already won, and any further guess can
    # only turn over a non-target — here, the assassin.
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 2, "intended_targets": ["t1", "t2"], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["t1", "t2", "a1"])

    row = run_game(
        codemaster, guesser, _two_target_board(), model="m", method="strong_hebrew", trial=0
    )

    assert row["outcome"] == "win"
    assert row["assassin_hit"] is False
    assert row["rounds"][0]["guess_sequence"] == [
        {"word": "t1", "role": "target"},
        {"word": "t2", "role": "target"},
    ]


def test_run_game_round_ends_when_all_targets_found_under_unlimited_budget():
    # count=0 means no guess cap, so the all-targets-found check is the only
    # thing that can end this round before a wrong guess does.
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 0, "intended_targets": [], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["t1", "t2", "c1"])

    row = run_game(
        codemaster, guesser, _two_target_board(), model="m", method="strong_hebrew", trial=0
    )

    assert row["outcome"] == "win"
    assert row["rounds"][0]["turn_outcome"] == "all_correct"
    assert [g["word"] for g in row["rounds"][0]["guess_sequence"]] == ["t1", "t2"]


def test_run_game_reports_max_rounds_reached_when_capped():
    codemaster = StubCodemaster(
        responses=[
            {"clue": "x", "count": 0, "intended_targets": [], "reasoning": "r"},
            {"clue": "y", "count": 0, "intended_targets": [], "reasoning": "r"},
        ]
    )
    guesser = StubGuesser(guesses=["c1", "o1"])

    row = run_game(
        codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0, max_rounds=2
    )

    assert row["status"] == "ok"
    assert row["outcome"] == "max_rounds_reached"
    assert row["game_length"] == 2


def test_run_game_codemaster_failure_ends_game_without_discarding_data():
    codemaster = StubCodemaster(error=FormatFailure("bad codemaster output"))
    guesser = StubGuesser()

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    # No clue means no playable round, but the game still reports a real
    # outcome rather than being discarded as a failure.
    assert row["status"] == "ok"
    assert row["outcome"] == "codemaster_failure"
    assert row["game_length"] == 0
    assert row["rounds"] == []
    assert "bad codemaster output" in row["terminal_error"]


def test_run_game_codemaster_failure_mid_game_preserves_completed_rounds():
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 0, "intended_targets": [], "reasoning": "r"}],
        error=FormatFailure("bad codemaster output"),
    )
    guesser = StubGuesser(guesses=["c1"])

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["outcome"] == "codemaster_failure"
    assert row["game_length"] == 1
    assert row["rounds"][0]["turn_outcome"] == "hit_civilian"


def test_run_game_guesser_failure_ends_round_but_not_the_game():
    codemaster = StubCodemaster(
        responses=[
            {"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"},
            {"clue": "y", "count": 1, "intended_targets": ["t1"], "reasoning": "r"},
        ]
    )
    # Round 1's guesser dies; round 2 recovers, scores a target, then ends
    # the game on the assassin.
    guesser = StubGuesser(guesses=[FormatFailure("bad guesser output"), "t1", "a1"])

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["outcome"] == "loss"
    assert row["game_length"] == 2
    assert row["rounds"][0]["turn_outcome"] == "guesser_failure"
    assert "bad guesser output" in row["rounds"][0]["error"]
    assert row["rounds"][0]["guess_sequence"] == []
    # The game carried on and the second round's guesses still counted.
    assert row["rounds"][1]["guess_sequence"] == [
        {"word": "t1", "role": "target"},
        {"word": "a1", "role": "assassin"},
    ]
    assert row["targets_found"] == 1


def test_run_game_stalls_out_after_repeated_guesser_failures():
    codemaster = StubCodemaster(
        responses=[
            {"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}
        ]
        * 5
    )
    guesser = StubGuesser(guesses=[FormatFailure("bad guesser output")] * 5)

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["outcome"] == "stalled"
    # Bailed out after the stall threshold instead of burning all 6 rounds.
    assert row["game_length"] == 2


def test_run_game_error_status_when_codemaster_raises_unexpected_exception():
    codemaster = StubCodemaster(error=RuntimeError("connection reset"))
    guesser = StubGuesser()

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "error"
    assert row["stage"] == "codemaster"
    assert "connection reset" in row["error"]
    assert row["board_seed"] == 1


def test_run_game_error_status_when_guesser_raises_unexpected_exception():
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}]
    )
    guesser = StubGuesser(error=KeyError("choices"))

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "error"
    assert row["stage"] == "guesser"
    assert "choices" in row["error"]
    assert row["clue"] == "x"


def test_run_game_error_status_is_distinct_from_format_failure():
    row_error = run_game(
        StubCodemaster(error=RuntimeError("infra")),
        StubGuesser(),
        _board(),
        model="m",
        method="strong_hebrew",
        trial=0,
    )
    row_format = run_game(
        StubCodemaster(error=FormatFailure("bad")),
        StubGuesser(),
        _board(),
        model="m",
        method="strong_hebrew",
        trial=0,
    )

    assert row_error["status"] != row_format["status"]


def test_run_game_records_codemaster_failure_message_as_terminal_error():
    codemaster = StubCodemaster(error=FormatFailure("bad", raw_response="I refuse."))

    row = run_game(
        codemaster, StubGuesser(), _board(), model="m", method="strong_hebrew", trial=0
    )

    assert row["outcome"] == "codemaster_failure"
    assert "bad" in row["terminal_error"]


def test_run_game_records_guesser_failure_message_on_the_round():
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}] * 2
    )
    guesser = StubGuesser(error=FormatFailure("bad", raw_response="hmm..."))

    row = run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["rounds"][0]["turn_outcome"] == "guesser_failure"
    assert "bad" in row["rounds"][0]["error"]


def test_run_game_sleeps_after_every_llm_call(mocker):
    sleep = mocker.patch("codenames_heb.experiment.time.sleep")
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 3, "intended_targets": ["t1", "t2", "t3"], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["t1", None])

    run_game(
        codemaster,
        guesser,
        _board(),
        model="m",
        method="strong_hebrew",
        trial=0,
        call_delay=2.5,
        max_rounds=1,
    )

    # 1 codemaster call + 2 guesser calls (1 guess + 1 voluntary stop) = 3 LLM calls.
    assert sleep.call_count == 3
    assert all(c.args[0] == 2.5 for c in sleep.call_args_list)


def test_run_game_does_not_sleep_when_call_delay_is_zero(mocker):
    sleep = mocker.patch("codenames_heb.experiment.time.sleep")
    codemaster = StubCodemaster(
        responses=[{"clue": "x", "count": 0, "intended_targets": [], "reasoning": "r"}]
    )
    guesser = StubGuesser(guesses=["c1"])

    run_game(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert sleep.call_count == 0


def test_load_config_reads_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "models: [model-a, model-b]\n"
        "codemaster_prompt_methods: [strong_hebrew, translate_pipeline]\n"
        "guesser_model: guesser-model\n"
        "board_styles: [dual_50]\n"
        "n_boards: 2\n"
        "n_trials: 1\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config == ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew", "translate_pipeline"],
        guesser_model="guesser-model",
        board_styles=["dual_50"],
        n_boards=2,
        n_trials=1,
    )


def _stub_factories():
    def make_codemaster(model, method):
        return AutoCodemaster()

    def make_guesser(model):
        return AutoGuesser()

    return make_codemaster, make_guesser


def test_run_experiment_writes_expected_number_of_rows(tmp_path):
    config = ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_styles=["dual_50"],
        n_boards=2,
        n_trials=2,
    )
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=config,
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    raw_lines = (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    # 2 models x 1 method x 2 boards x 2 trials
    assert len(raw_lines) == 8
    for line in raw_lines:
        json.loads(line)  # each line is valid JSON

    with (run_dir / "metrics.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == [
            "model",
            "method",
            "guesser_model",
            "board_seed",
            "board_style",
            "trial",
            "status",
            "stage",
            "outcome",
            "game_length",
            "targets_found",
            "target_recovery_rate",
            "assassin_hit",
            "codemaster_attempts",
            "codemaster_rejected",
            "codemaster_compliance_rate",
            "codemaster_call_failures",
            "guesser_attempts",
            "guesser_rejected",
            "guesser_compliance_rate",
            "guesser_call_failures",
            "terminal_error",
            "error",
        ]
        csv_rows = list(reader)
    assert len(csv_rows) == 8
    assert all(row["status"] == "ok" for row in csv_rows)


def test_run_experiment_reuses_same_boards_across_models(tmp_path):
    config = ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_styles=["dual_50"],
        n_boards=1,
        n_trials=1,
    )
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=config,
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    rows = [json.loads(line) for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()]
    board_seeds = {row["board_seed"] for row in rows}
    assert board_seeds == {0}


def test_run_experiment_generates_n_boards_for_every_style(tmp_path):
    config = _tiny_config(
        board_styles=["dual_0", "dual_80", "dual_100"], n_boards=2, n_trials=1
    )
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=config,
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    boards = json.loads((run_dir / "boards.json").read_text(encoding="utf-8"))
    assert [(b["style"], b["seed"]) for b in boards] == [
        ("dual_0", 0), ("dual_0", 1),
        ("dual_80", 0), ("dual_80", 1),
        ("dual_100", 0), ("dual_100", 1),
    ]
    # The style label has to match the board's actual composition, or the
    # independent variable is mislabelled in every downstream analysis.
    expected_dual = {"dual_0": 0, "dual_80": 20, "dual_100": 25}
    for entry in boards:
        assert sum(entry["is_dual"].values()) == expected_dual[entry["style"]]


def test_run_experiment_tags_every_result_row_with_its_board_style(tmp_path):
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=_tiny_config(board_styles=["dual_0", "dual_100"], n_boards=1, n_trials=1),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    rows = [
        json.loads(line)
        for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]
    assert [row["board_style"] for row in rows] == ["dual_0", "dual_100"]

    with (run_dir / "metrics.csv").open(encoding="utf-8") as f:
        assert [row["board_style"] for row in csv.DictReader(f)] == ["dual_0", "dual_100"]


# --- Fix 7: config validation happens before a run starts ---

_VALID_CONFIG_TEXT = (
    "models: [model-a]\n"
    "codemaster_prompt_methods: [strong_hebrew]\n"
    "guesser_model: guesser-model\n"
    "board_styles: [dual_50]\n"
    "n_boards: 2\n"
    "n_trials: 1\n"
)


def _write_config(tmp_path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_config_raises_value_error_naming_missing_key_and_path(tmp_path):
    path = _write_config(
        tmp_path,
        "models: [model-a]\n"
        "codemaster_prompt_methods: [strong_hebrew]\n"
        "n_boards: 2\n"
        "n_trials: 1\n",
    )

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    message = str(excinfo.value)
    assert "guesser_model" in message
    assert str(path) in message


def test_load_config_names_all_missing_keys(tmp_path):
    path = _write_config(tmp_path, "models: [model-a]\n")

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    message = str(excinfo.value)
    for key in (
        "codemaster_prompt_methods",
        "guesser_model",
        "board_styles",
        "n_boards",
        "n_trials",
    ):
        assert key in message


def test_load_config_rejects_empty_yaml_file(tmp_path):
    path = _write_config(tmp_path, "")

    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_rejects_unknown_prompt_method(tmp_path):
    path = _write_config(
        tmp_path, _VALID_CONFIG_TEXT.replace("[strong_hebrew]", "[strong_hebrw]")
    )

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    message = str(excinfo.value)
    assert "strong_hebrw" in message
    assert "strong_hebrew" in message  # valid options are listed
    assert "translate_pipeline" in message


def test_load_config_rejects_empty_prompt_method_list(tmp_path):
    path = _write_config(tmp_path, _VALID_CONFIG_TEXT.replace("[strong_hebrew]", "[]"))

    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_rejects_non_list_prompt_methods(tmp_path):
    path = _write_config(
        tmp_path, _VALID_CONFIG_TEXT.replace("[strong_hebrew]", "strong_hebrew")
    )

    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_rejects_non_positive_n_boards(tmp_path):
    path = _write_config(tmp_path, _VALID_CONFIG_TEXT.replace("n_boards: 2", "n_boards: 0"))

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    assert "n_boards" in str(excinfo.value)


def test_load_config_rejects_non_positive_n_trials(tmp_path):
    path = _write_config(tmp_path, _VALID_CONFIG_TEXT.replace("n_trials: 1", "n_trials: -3"))

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    assert "n_trials" in str(excinfo.value)


def test_load_config_rejects_unknown_board_style(tmp_path):
    path = _write_config(
        tmp_path, _VALID_CONFIG_TEXT.replace("[dual_50]", "[standard]")
    )

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    message = str(excinfo.value)
    assert "standard" in message
    assert "dual_50" in message  # valid options are listed
    assert "dual_100" in message


def test_load_config_rejects_empty_board_style_list(tmp_path):
    path = _write_config(tmp_path, _VALID_CONFIG_TEXT.replace("[dual_50]", "[]"))

    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_rejects_non_list_board_styles(tmp_path):
    path = _write_config(tmp_path, _VALID_CONFIG_TEXT.replace("[dual_50]", "dual_50"))

    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_accepts_all_four_board_styles(tmp_path):
    path = _write_config(
        tmp_path,
        _VALID_CONFIG_TEXT.replace("[dual_50]", "[dual_0, dual_50, dual_80, dual_100]"),
    )

    config = load_config(path)

    assert config.board_styles == ["dual_0", "dual_50", "dual_80", "dual_100"]


def test_load_config_accepts_the_real_m2_config():
    config = load_config(
        Path(__file__).resolve().parents[1] / "configs" / "m2_board_styles.yaml"
    )

    assert config.board_styles == ["dual_0", "dual_50", "dual_80", "dual_100"]


def test_load_config_accepts_the_real_pilot_config():
    config = load_config(Path(__file__).resolve().parents[1] / "configs" / "m1_pilot.yaml")

    assert config.n_boards > 0
    assert config.codemaster_prompt_methods


# --- Fix 2: a small delay between LLM calls, gentle on free-tier rate limits ---


def _tiny_config(**overrides) -> ExperimentConfig:
    defaults = dict(
        models=["model-a"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_styles=["dual_50"],
        n_boards=2,
        n_trials=1,
    )
    defaults.update(overrides)
    return ExperimentConfig(**defaults)


def test_run_experiment_sleeps_between_llm_calls_by_default(tmp_path, mocker):
    sleep = mocker.patch("codenames_heb.experiment.time.sleep")
    make_codemaster, make_guesser = _stub_factories()

    run_experiment(
        config=_tiny_config(n_boards=2, n_trials=2),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
    )

    # Exact count depends on how many rounds each game takes (not scripted
    # here); what matters is pacing is wired through at all, at the right value.
    assert sleep.call_count > 0
    assert all(c.args[0] == 3.0 for c in sleep.call_args_list)


def test_run_experiment_trial_delay_is_overridable(tmp_path, mocker):
    sleep = mocker.patch("codenames_heb.experiment.time.sleep")
    make_codemaster, make_guesser = _stub_factories()

    run_experiment(
        config=_tiny_config(n_boards=1, n_trials=1),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    assert sleep.call_count == 0


# --- Fix 8: runs are self-describing (boards + config persisted) ---


def test_run_experiment_writes_boards_json(tmp_path):
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=_tiny_config(n_boards=2),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    boards = json.loads((run_dir / "boards.json").read_text(encoding="utf-8"))
    assert isinstance(boards, list)
    assert [b["seed"] for b in boards] == [0, 1]
    words = _word_lists()
    for entry, seed in zip(boards, [0, 1]):
        expected = generate_board(words.regular, words.dual, seed=seed, style="dual_50")
        assert entry["words"] == list(expected.words)
        assert entry["roles"] == dict(expected.roles)
        assert entry["style"] == "dual_50"
        assert entry["is_dual"] == {w: expected.is_dual(w) for w in expected.words}
        assert len(entry["words"]) == 25


def test_run_experiment_copies_source_config_verbatim(tmp_path):
    config_path = _write_config(tmp_path, _VALID_CONFIG_TEXT)
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=load_config(config_path),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path / "results",
        config_path=config_path,
        trial_delay=0,
    )

    assert (run_dir / "config.yaml").read_text(encoding="utf-8") == _VALID_CONFIG_TEXT


def test_run_experiment_serializes_config_when_no_source_path_given(tmp_path):
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=_tiny_config(),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    written = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    assert written["models"] == ["model-a"]
    assert written["n_boards"] == 2


# --- Self-play: guesser_model: same_as_codemaster ---


def test_run_experiment_self_play_uses_each_codemaster_as_its_own_guesser(tmp_path):
    built_guessers = []

    def make_codemaster(model, method):
        return AutoCodemaster()

    def make_guesser(model):
        built_guessers.append(model)
        return AutoGuesser()

    run_dir = run_experiment(
        config=_tiny_config(
            models=["model-a", "model-b"],
            guesser_model=SAME_AS_CODEMASTER,
            n_boards=1,
        ),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    # One guesser per codemaster model, each matching its codemaster.
    assert built_guessers == ["model-a", "model-b"]

    rows = [
        json.loads(line)
        for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]
    # Each row records the guesser that actually played it, which under
    # self-play differs per row and can't be recovered from the config alone.
    assert all(row["guesser_model"] == row["model"] for row in rows)


def test_run_experiment_fixed_guesser_is_shared_across_codemaster_models(tmp_path):
    built_guessers = []

    def make_codemaster(model, method):
        return AutoCodemaster()

    def make_guesser(model):
        built_guessers.append(model)
        return AutoGuesser()

    run_dir = run_experiment(
        config=_tiny_config(
            models=["model-a", "model-b"],
            guesser_model="fixed/guesser",
            n_boards=1,
        ),
        word_lists=_word_lists(),
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    assert built_guessers == ["fixed/guesser", "fixed/guesser"]
    rows = [
        json.loads(line)
        for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]
    assert all(row["guesser_model"] == "fixed/guesser" for row in rows)


def test_load_config_accepts_same_as_codemaster_sentinel(tmp_path):
    path = _write_config(
        tmp_path,
        _VALID_CONFIG_TEXT.replace("guesser_model: guesser-model", f"guesser_model: {SAME_AS_CODEMASTER}"),
    )

    assert load_config(path).guesser_model == SAME_AS_CODEMASTER
