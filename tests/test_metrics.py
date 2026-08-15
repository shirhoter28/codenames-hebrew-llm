from codenames_heb.metrics import compute_round_metrics


def test_all_correct_outcome():
    result = compute_round_metrics(
        count=2, intended_targets=["t1", "t2"], correct=["t1", "t2"],
        outcome="all_correct", assassin_hit=False,
    )

    assert result["guesses_before_miss"] == 2
    assert result["turn_outcome"] == "all_correct"
    assert result["assassin_hit"] is False


def test_stopped_early_outcome():
    result = compute_round_metrics(
        count=2, intended_targets=["t1", "t2"], correct=["t1"],
        outcome="stopped_early", assassin_hit=False,
    )

    assert result["guesses_before_miss"] == 1
    assert result["turn_outcome"] == "stopped_early"


def test_hit_opponent_outcome():
    result = compute_round_metrics(
        count=2, intended_targets=["t1", "t2"], correct=["t1"],
        outcome="hit_opponent", assassin_hit=False,
    )

    assert result["guesses_before_miss"] == 1
    assert result["turn_outcome"] == "hit_opponent"
    assert result["assassin_hit"] is False


def test_flags_assassin_hit():
    result = compute_round_metrics(
        count=1, intended_targets=["t1"], correct=[],
        outcome="hit_assassin", assassin_hit=True,
    )

    assert result["turn_outcome"] == "hit_assassin"
    assert result["assassin_hit"] is True
    assert result["guesses_before_miss"] == 0


def test_target_recovery_rate_uses_count_when_positive():
    result = compute_round_metrics(
        count=2, intended_targets=["t1", "t2"], correct=["t1"],
        outcome="stopped_early", assassin_hit=False,
    )

    assert result["target_recovery_rate"] == 0.5


def test_target_recovery_rate_falls_back_to_intended_targets_when_count_zero():
    result = compute_round_metrics(
        count=0, intended_targets=["t1", "t2"], correct=["t1", "t2", "t3"],
        outcome="all_correct", assassin_hit=False,
    )

    # All 3 targets guessed / 2 intended targets = 1.5 (game-outcome metric, not intent-aware)
    assert result["target_recovery_rate"] == 1.5


def test_target_recovery_rate_is_none_when_count_zero_and_no_intended_targets():
    result = compute_round_metrics(
        count=0, intended_targets=[], correct=["t1"],
        outcome="stopped_early", assassin_hit=False,
    )

    assert result["target_recovery_rate"] is None


def test_intended_recall_and_precision_normal_case():
    result = compute_round_metrics(
        count=3, intended_targets=["t1", "t2"], correct=["t1", "t3", "t2"],
        outcome="all_correct", assassin_hit=False,
    )

    assert result["intended_recall"] == 1.0
    assert result["intended_precision"] == 2 / 3


def test_intended_recall_and_precision_none_when_no_intended_targets():
    result = compute_round_metrics(
        count=1, intended_targets=[], correct=["t1"],
        outcome="stopped_early", assassin_hit=False,
    )

    assert result["intended_recall"] is None
    assert result["intended_precision"] is None


def test_intended_precision_none_when_no_correct_guesses():
    result = compute_round_metrics(
        count=1, intended_targets=["t1"], correct=[],
        outcome="hit_opponent", assassin_hit=False,
    )

    assert result["intended_precision"] is None
