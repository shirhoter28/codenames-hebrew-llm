_OUTCOME_BY_ROLE = {
    "opponent": "hit_opponent",
    "civilian": "hit_civilian",
    "assassin": "hit_assassin",
}


def compute_round_metrics(
    count: int,
    intended_targets: list[str],
    correct: list[str],
    outcome: str,
    assassin_hit: bool,
) -> dict:
    """Roll up a single round's already-resolved guessing into metrics.

    `correct`, `outcome`, and `assassin_hit` are produced live by the
    interactive guess-by-guess loop (see `experiment.run_game`) — this
    function only derives the recovery/recall/precision numbers from them,
    it does not re-walk or truncate a raw guess list.
    """
    if count > 0:
        target_recovery_rate = len(correct) / count
    elif intended_targets:
        target_recovery_rate = len(correct) / len(intended_targets)
    else:
        target_recovery_rate = None

    if intended_targets:
        recovered_intended = [w for w in correct if w in intended_targets]
        intended_recall = len(recovered_intended) / len(intended_targets)
        intended_precision = (
            len(recovered_intended) / len(correct) if correct else None
        )
    else:
        intended_recall = None
        intended_precision = None

    return {
        "guesses_before_miss": len(correct),
        "turn_outcome": outcome,
        "assassin_hit": assassin_hit,
        "target_recovery_rate": target_recovery_rate,
        "intended_recall": intended_recall,
        "intended_precision": intended_precision,
    }
