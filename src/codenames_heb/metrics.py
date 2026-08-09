from codenames_heb.board import Board

_OUTCOME_BY_ROLE = {
    "opponent": "hit_opponent",
    "civilian": "hit_civilian",
    "assassin": "hit_assassin",
}


def compute_metrics(
    board: Board, count: int, intended_targets: list[str], guesses: list[str]
) -> dict:
    max_guesses = None if count == 0 else count + 1

    correct: list[str] = []
    outcome: str | None = None
    for word in guesses:
        if max_guesses is not None and len(correct) >= max_guesses:
            break
        role = board.role_of(word)
        if role == "target":
            correct.append(word)
            continue
        outcome = _OUTCOME_BY_ROLE[role]
        break

    assassin_hit = outcome == "hit_assassin"

    if outcome is None:
        full_budget_used = max_guesses is not None and len(correct) >= max_guesses
        outcome = "all_correct" if full_budget_used else "stopped_early"

    # Compute target_recovery_rate (game-outcome metric, counts all correct guesses)
    if count > 0:
        target_recovery_rate = len(correct) / count
    elif intended_targets:
        target_recovery_rate = len(correct) / len(intended_targets)
    else:
        target_recovery_rate = None

    # Compute intended_recall and intended_precision
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
