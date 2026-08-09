import csv
import json
from pathlib import Path

import pytest
import yaml

from codenames_heb.board import Board, generate_board
from codenames_heb.experiment import ExperimentConfig, load_config, run_experiment, run_trial
from codenames_heb.llm_client import FormatFailure


def _board() -> Board:
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


class StubCodemaster:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def give_clue(self, board, required_count=None):
        if self.error:
            raise self.error
        return self.response


class StubGuesser:
    def __init__(self, guesses=None, error=None):
        self.guesses = guesses if guesses is not None else []
        self.error = error

    def guess(self, words, clue, count):
        if self.error:
            raise self.error
        return self.guesses


def test_run_trial_returns_ok_status_with_metrics():
    codemaster = StubCodemaster(
        response={"clue": "x", "count": 2, "intended_targets": ["t1", "t2"], "reasoning": "r"}
    )
    guesser = StubGuesser(guesses=["t1", "t2"])

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "ok"
    assert row["model"] == "m"
    assert row["method"] == "strong_hebrew"
    assert row["board_seed"] == 1
    assert row["trial"] == 0
    assert row["guesses_before_miss"] == 2
    # Budget is count + 1 = 3; only 2 of 3 guesses were used (no wrong guess,
    # guesser just stopped), so per compute_metrics' established semantics
    # (see test_stopped_early_when_fewer_guesses_than_budget_all_correct in
    # test_metrics.py) this is "stopped_early", not "all_correct".
    assert row["turn_outcome"] == "stopped_early"


def test_run_trial_returns_format_failure_when_codemaster_fails():
    codemaster = StubCodemaster(error=FormatFailure("bad codemaster output"))
    guesser = StubGuesser()

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "format_failure"
    assert row["stage"] == "codemaster"


def test_run_trial_returns_format_failure_when_guesser_fails():
    codemaster = StubCodemaster(
        response={"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}
    )
    guesser = StubGuesser(error=FormatFailure("bad guesser output"))

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "format_failure"
    assert row["stage"] == "guesser"


# --- Fix 1.3: any unexpected exception is a harness "error", not a format_failure ---


def test_run_trial_returns_error_status_when_codemaster_raises_unexpected_exception():
    codemaster = StubCodemaster(error=RuntimeError("connection reset"))
    guesser = StubGuesser()

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "error"
    assert row["stage"] == "codemaster"
    assert "connection reset" in row["error"]
    assert row["board_seed"] == 1


def test_run_trial_returns_error_status_when_guesser_raises_unexpected_exception():
    codemaster = StubCodemaster(
        response={"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}
    )
    guesser = StubGuesser(error=KeyError("choices"))

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["status"] == "error"
    assert row["stage"] == "guesser"
    assert "choices" in row["error"]
    assert row["clue"] == "x"


def test_run_trial_error_status_is_distinct_from_format_failure():
    codemaster = StubCodemaster(error=RuntimeError("infra"))
    row_error = run_trial(
        codemaster, StubGuesser(), _board(), model="m", method="strong_hebrew", trial=0
    )
    row_format = run_trial(
        StubCodemaster(error=FormatFailure("bad")),
        StubGuesser(),
        _board(),
        model="m",
        method="strong_hebrew",
        trial=0,
    )

    assert row_error["status"] != row_format["status"]


# --- Fix 6.4: format_failure rows log the raw model response ---


def test_run_trial_logs_raw_response_on_codemaster_format_failure():
    codemaster = StubCodemaster(error=FormatFailure("bad", raw_response="I refuse."))

    row = run_trial(
        codemaster, StubGuesser(), _board(), model="m", method="strong_hebrew", trial=0
    )

    assert row["status"] == "format_failure"
    assert row["raw_response"] == "I refuse."


def test_run_trial_logs_raw_response_on_guesser_format_failure():
    codemaster = StubCodemaster(
        response={"clue": "x", "count": 1, "intended_targets": ["t1"], "reasoning": "r"}
    )
    guesser = StubGuesser(error=FormatFailure("bad", raw_response="hmm..."))

    row = run_trial(codemaster, guesser, _board(), model="m", method="strong_hebrew", trial=0)

    assert row["raw_response"] == "hmm..."


def test_run_trial_raw_response_key_present_even_when_absent_on_exception():
    codemaster = StubCodemaster(error=FormatFailure("bad"))

    row = run_trial(
        codemaster, StubGuesser(), _board(), model="m", method="strong_hebrew", trial=0
    )

    assert "raw_response" in row
    assert row["raw_response"] is None


def test_load_config_reads_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "models: [model-a, model-b]\n"
        "codemaster_prompt_methods: [strong_hebrew, translate_pipeline]\n"
        "guesser_model: guesser-model\n"
        "board_style: standard\n"
        "n_boards: 2\n"
        "n_trials: 1\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config == ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew", "translate_pipeline"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=2,
        n_trials=1,
    )


def test_run_experiment_writes_expected_number_of_rows(tmp_path):
    config = ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=2,
        n_trials=2,
    )
    word_pool = [f"word{i}" for i in range(40)]

    def make_codemaster(model, method):
        return StubCodemaster(
            response={"clue": "x", "count": 1, "intended_targets": [], "reasoning": "r"}
        )

    def make_guesser(model):
        return StubGuesser(guesses=[])

    run_dir = run_experiment(
        config=config,
        word_pool=word_pool,
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
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 8


def test_run_experiment_reuses_same_boards_across_models(tmp_path):
    config = ExperimentConfig(
        models=["model-a", "model-b"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=1,
        n_trials=1,
    )
    word_pool = [f"word{i}" for i in range(40)]

    def make_codemaster(model, method):
        return StubCodemaster(
            response={"clue": "x", "count": 1, "intended_targets": [], "reasoning": "r"}
        )

    def make_guesser(model):
        return StubGuesser(guesses=[])

    run_dir = run_experiment(
        config=config,
        word_pool=word_pool,
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    rows = [json.loads(line) for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()]
    board_seeds = {row["board_seed"] for row in rows}
    assert board_seeds == {0}


# --- Fix 7: config validation happens before a run starts ---

_VALID_CONFIG_TEXT = (
    "models: [model-a]\n"
    "codemaster_prompt_methods: [strong_hebrew]\n"
    "guesser_model: guesser-model\n"
    "board_style: standard\n"
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
    for key in ("codemaster_prompt_methods", "guesser_model", "n_boards", "n_trials"):
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


def test_load_config_accepts_the_real_pilot_config():
    config = load_config(Path(__file__).resolve().parents[1] / "configs" / "m1_pilot.yaml")

    assert config.n_boards > 0
    assert config.codemaster_prompt_methods


# --- Fix 2: a small delay between trials, gentle on free-tier rate limits ---


def _tiny_config(**overrides) -> ExperimentConfig:
    defaults = dict(
        models=["model-a"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_model="guesser-model",
        board_style="standard",
        n_boards=2,
        n_trials=1,
    )
    defaults.update(overrides)
    return ExperimentConfig(**defaults)


def _stub_factories():
    def make_codemaster(model, method):
        return StubCodemaster(
            response={"clue": "x", "count": 1, "intended_targets": [], "reasoning": "r"}
        )

    def make_guesser(model):
        return StubGuesser(guesses=[])

    return make_codemaster, make_guesser


def test_run_experiment_sleeps_between_trials_by_default(tmp_path, mocker):
    sleep = mocker.patch("codenames_heb.experiment.time.sleep")
    make_codemaster, make_guesser = _stub_factories()

    run_experiment(
        config=_tiny_config(n_boards=2, n_trials=2),
        word_pool=[f"word{i}" for i in range(40)],
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
    )

    assert sleep.call_count == 4  # 1 model x 1 method x 2 boards x 2 trials
    assert sleep.call_args_list[0].args[0] == 0.5


def test_run_experiment_trial_delay_is_overridable(tmp_path, mocker):
    sleep = mocker.patch("codenames_heb.experiment.time.sleep")
    make_codemaster, make_guesser = _stub_factories()

    run_experiment(
        config=_tiny_config(n_boards=1, n_trials=1),
        word_pool=[f"word{i}" for i in range(40)],
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
        word_pool=[f"word{i}" for i in range(40)],
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    boards = json.loads((run_dir / "boards.json").read_text(encoding="utf-8"))
    assert isinstance(boards, list)
    assert [b["seed"] for b in boards] == [0, 1]
    for entry, seed in zip(boards, [0, 1]):
        expected = generate_board([f"word{i}" for i in range(40)], seed=seed)
        assert entry["words"] == list(expected.words)
        assert entry["roles"] == dict(expected.roles)
        assert len(entry["words"]) == 25


def test_run_experiment_copies_source_config_verbatim(tmp_path):
    config_path = _write_config(tmp_path, _VALID_CONFIG_TEXT)
    make_codemaster, make_guesser = _stub_factories()

    run_dir = run_experiment(
        config=load_config(config_path),
        word_pool=[f"word{i}" for i in range(40)],
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
        word_pool=[f"word{i}" for i in range(40)],
        make_codemaster=make_codemaster,
        make_guesser=make_guesser,
        results_dir=tmp_path,
        trial_delay=0,
    )

    written = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    assert written["models"] == ["model-a"]
    assert written["n_boards"] == 2
