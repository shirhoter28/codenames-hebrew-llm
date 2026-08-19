"""The Guesser as a crossed experimental factor (M3, the 4x4 grid).

Until M3 the Guesser was one fixed model per run, so `guesser_model` was a
scalar and the dispatcher only had to keep concurrent games on distinct
*codemaster* providers. Crossing the guesser breaks both assumptions: a run now
names several guessers, and every game hits two providers rather than one.
"""

from collections import Counter

import pytest

from codenames_heb.experiment import (
    SAME_AS_CODEMASTER,
    ExperimentConfig,
    _ordered_tasks,
    load_config,
)


def _write(tmp_path, text: str):
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _complaint(excinfo, path) -> str:
    """The error text with the config path removed.

    `load_config` names the offending file, and pytest builds that path out of
    the test's own name — so a bare substring assertion can match the filename
    instead of the message and pass for the wrong reason.
    """
    return str(excinfo.value).replace(str(path), "<config>")


_BASE = (
    "models: [model-a, model-b]\n"
    "codemaster_prompt_methods: [strong_hebrew]\n"
    "board_styles: [dual_50]\n"
    "n_boards: 1\n"
    "n_trials: 1\n"
)


# --- config schema: the list form, and the scalar form that must keep working ---


def test_guesser_models_list_is_read_as_the_guesser_axis(tmp_path):
    path = _write(tmp_path, _BASE + "guesser_models: [g-one, g-two]\n")

    assert load_config(path).guesser_models == ["g-one", "g-two"]


def test_legacy_scalar_guesser_model_normalises_to_a_one_element_axis(tmp_path):
    """Five configs on disk predate the axis; none of them should need editing."""
    path = _write(tmp_path, _BASE + "guesser_model: only-guesser\n")

    assert load_config(path).guesser_models == ["only-guesser"]


def test_naming_both_guesser_keys_is_rejected(tmp_path):
    path = _write(tmp_path, _BASE + "guesser_model: a\nguesser_models: [b]\n")

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    message = _complaint(excinfo, path)
    assert "guesser_model" in message and "guesser_models" in message


def test_duplicate_guessers_are_rejected(tmp_path):
    """A repeated guesser silently doubles that column's games and unbalances the grid."""
    path = _write(tmp_path, _BASE + "guesser_models: [g-one, g-one]\n")

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    assert "g-one" in _complaint(excinfo, path)


def test_a_misspelled_self_play_sentinel_is_rejected(tmp_path):
    """`same_as_codemasters` used to pass validation and become a literal model id."""
    path = _write(tmp_path, _BASE + f"guesser_models: [{SAME_AS_CODEMASTER}s]\n")

    with pytest.raises(ValueError) as excinfo:
        load_config(path)

    assert SAME_AS_CODEMASTER in _complaint(excinfo, path)


def test_self_play_sentinel_is_accepted_inside_the_list(tmp_path):
    path = _write(tmp_path, _BASE + f"guesser_models: [{SAME_AS_CODEMASTER}, g-two]\n")

    assert load_config(path).guesser_models == [SAME_AS_CODEMASTER, "g-two"]


def test_a_narrow_guesser_axis_does_not_shrink_the_worker_cap(tmp_path):
    """The cap stays on the codemaster axis.

    Capping at min(codemasters, guessers) looks tidier but would forbid every
    config written before M3: those name one fixed guesser, so the cap would be
    1 and no run could be parallel at all — including the 4-worker run that
    completed fine on 2026-08-17. Crossing the guesser must only ever improve
    provider spread, never veto a config that already works.
    """
    path = _write(
        tmp_path,
        "models: [model-a, model-b, model-c]\n"
        "codemaster_prompt_methods: [strong_hebrew]\n"
        "guesser_model: only-guesser\n"
        "board_styles: [dual_50]\n"
        "n_boards: 1\n"
        "n_trials: 1\n"
        "max_workers: 3\n",
    )

    assert load_config(path).max_workers == 3


# --- dispatch order: the Latin square that keeps providers off each other ---


class _FakeBoard:
    def __init__(self, seed):
        self.seed = seed
        self.style = "dual_50"


def _grid_config(n_models=4, n_guessers=4, n_boards=5):
    return ExperimentConfig(
        models=[f"m{i}" for i in range(n_models)],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_models=[f"m{i}" for i in range(n_guessers)],
        board_styles=["dual_50"],
        n_boards=n_boards,
        n_trials=1,
        max_workers=min(n_models, n_guessers),
    )


def test_tasks_cover_the_full_grid_exactly_once():
    config = _grid_config()
    boards = [_FakeBoard(i) for i in range(5)]

    tasks = _ordered_tasks(config, boards)

    assert len(tasks) == 4 * 4 * 1 * 5 * 1
    pairs = {(model, guesser) for model, guesser, _, _, _ in tasks}
    assert len(pairs) == 16


def _windows(tasks, width):
    return [tasks[i : i + width] for i in range(len(tasks) - width + 1)]


def test_no_provider_is_asked_for_more_than_two_concurrent_calls_in_a_role():
    """The safety property the ordering exists for.

    A naive nested loop emits (m0,m0), (m0,m1), (m0,m2), (m0,m3) — four
    concurrent games all hitting m0 as codemaster, the burst that killed a
    180-game run with HTTP 429 (DECISIONS.md 2026-08-10).

    Note the *perfect* property — every sliding window of 4 distinct in both
    roles — is impossible for a 4x4 grid: requiring 4-distinct codemasters and
    4-distinct guessers in every window forces both indices to cycle with
    period 4, which yields only 4 of the 16 pairs. Two is the achievable bound.
    """
    config = _grid_config()
    tasks = _ordered_tasks(config, [_FakeBoard(i) for i in range(5)])

    for window in _windows(tasks, config.max_workers):
        for role in (0, 1):
            counts = Counter(t[role] for t in window)
            worst, n = counts.most_common(1)[0]
            assert n <= 2, f"{worst} appears {n}x in one window of {config.max_workers}"


def test_dispatch_is_perfectly_spread_except_at_round_boundaries():
    """Within a round of the Latin square every window is fully distinct; only
    the handover between rounds can double up, and only briefly."""
    config = _grid_config()
    tasks = _ordered_tasks(config, [_FakeBoard(i) for i in range(5)])

    width = config.max_workers
    imperfect = [
        w
        for w in _windows(tasks, width)
        if len({t[0] for t in w}) < width or len({t[1] for t in w}) < width
    ]

    n_boundaries = len(config.guesser_models) - 1
    assert len(imperfect) <= n_boundaries * (width - 1)


def test_every_pair_gets_the_same_number_of_games():
    """An unbalanced grid would confound the codemaster and guesser main effects."""
    config = _grid_config()
    tasks = _ordered_tasks(config, [_FakeBoard(i) for i in range(5)])

    counts = Counter((t[0], t[1]) for t in tasks)

    assert set(counts.values()) == {5}


def test_self_play_sentinel_resolves_to_each_codemaster_in_the_task_list():
    config = ExperimentConfig(
        models=["m0", "m1"],
        codemaster_prompt_methods=["strong_hebrew"],
        guesser_models=[SAME_AS_CODEMASTER],
        board_styles=["dual_50"],
        n_boards=1,
        n_trials=1,
    )

    tasks = _ordered_tasks(config, [_FakeBoard(0)])

    assert {(t[0], t[1]) for t in tasks} == {("m0", "m0"), ("m1", "m1")}
