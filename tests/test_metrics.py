from codenames_heb.board import Board
from codenames_heb.metrics import compute_metrics


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


def test_all_correct_when_full_budget_used_and_all_targets():
    result = compute_metrics(
        _board(), count=2, intended_targets=["t1", "t2"], guesses=["t1", "t2", "t3"]
    )

    assert result["guesses_before_miss"] == 3
    assert result["turn_outcome"] == "all_correct"
    assert result["assassin_hit"] is False


def test_stopped_early_when_fewer_guesses_than_budget_all_correct():
    result = compute_metrics(
        _board(), count=2, intended_targets=["t1", "t2"], guesses=["t1"]
    )

    assert result["guesses_before_miss"] == 1
    assert result["turn_outcome"] == "stopped_early"


def test_truncates_and_flags_outcome_on_opponent_hit():
    result = compute_metrics(
        _board(), count=2, intended_targets=["t1", "t2"], guesses=["t1", "o1", "t2"]
    )

    assert result["guesses_before_miss"] == 1
    assert result["turn_outcome"] == "hit_opponent"
    assert result["assassin_hit"] is False


def test_flags_assassin_hit():
    result = compute_metrics(
        _board(), count=1, intended_targets=["t1"], guesses=["a1"]
    )

    assert result["turn_outcome"] == "hit_assassin"
    assert result["assassin_hit"] is True
    assert result["guesses_before_miss"] == 0


def test_target_recovery_rate_uses_count_when_positive():
    result = compute_metrics(
        _board(), count=2, intended_targets=["t1", "t2"], guesses=["t1"]
    )

    assert result["target_recovery_rate"] == 0.5


def test_target_recovery_rate_falls_back_to_intended_targets_when_count_zero():
    result = compute_metrics(
        _board(), count=0, intended_targets=["t1", "t2"], guesses=["t1", "t2", "t3"]
    )

    assert result["target_recovery_rate"] == 1.0


def test_target_recovery_rate_is_none_when_count_zero_and_no_intended_targets():
    result = compute_metrics(_board(), count=0, intended_targets=[], guesses=["t1"])

    assert result["target_recovery_rate"] is None


def test_intended_recall_and_precision_normal_case():
    result = compute_metrics(
        _board(), count=3, intended_targets=["t1", "t2"], guesses=["t1", "t3", "t2"]
    )

    assert result["intended_recall"] == 1.0
    assert result["intended_precision"] == 2 / 3


def test_intended_recall_and_precision_none_when_no_intended_targets():
    result = compute_metrics(_board(), count=1, intended_targets=[], guesses=["t1"])

    assert result["intended_recall"] is None
    assert result["intended_precision"] is None


def test_intended_precision_none_when_no_correct_guesses():
    result = compute_metrics(
        _board(), count=1, intended_targets=["t1"], guesses=["o1"]
    )

    assert result["intended_precision"] is None
