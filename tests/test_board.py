import pytest

from codenames_heb.board import (
    dual_count,
    ALL_BOARD_STYLES,
    BOARD_SIZE,
    BOARD_STYLES,
    RETIRED_BOARD_STYLES,
    ROLE_COUNTS,
    generate_board,
)


def _regular(n: int = 40) -> list[str]:
    return [f"reg{i}" for i in range(n)]


def _dual(n: int = 40) -> list[str]:
    return [f"dual{i}" for i in range(n)]


def _board(seed: int = 1, style: str = "natural"):
    return generate_board(_regular(), _dual(), seed=seed, style=style)


def test_generate_board_has_25_unique_words():
    board = _board()

    assert len(board.words) == BOARD_SIZE
    assert len(set(board.words)) == BOARD_SIZE


def test_generate_board_role_counts_match_standard_distribution():
    board = _board()

    counts = {role: len(board.words_with_role(role)) for role in ROLE_COUNTS}

    assert counts == ROLE_COUNTS


def test_generate_board_role_of_matches_words_with_role():
    board = _board()

    for role in ROLE_COUNTS:
        for word in board.words_with_role(role):
            assert board.role_of(word) == role


def test_generate_board_is_deterministic_for_same_seed_and_style():
    board_a = _board(seed=42)
    board_b = _board(seed=42)

    assert board_a.words == board_b.words
    assert board_a.roles == board_b.roles
    assert board_a.dual_words == board_b.dual_words


def test_generate_board_differs_for_different_seed():
    assert _board(seed=1).words != _board(seed=2).words


def test_generate_board_differs_across_styles_at_same_seed():
    assert _board(seed=1, style="natural").words != _board(seed=1, style="dual_100").words


@pytest.mark.parametrize(
    "style,expected",
    [("dual_0", 0), ("dual_100", 25)],
)
def test_exact_styles_have_fixed_dual_counts(style, expected):
    for seed in range(6):
        board = generate_board(_regular(), _dual(), seed=seed, style=style)

        assert len(board.dual_words) == expected
        assert sum(board.is_dual(w) for w in board.words) == expected


def test_a_fractional_style_alternates_by_seed_parity_and_averages_its_share():
    # Only retired styles are fractional now, but the parity rule is what makes
    # them reproducible, so it has to keep working.
    counts = [
        len(generate_board(_regular(), _dual(), seed=seed, style="dual_50").dual_words)
        for seed in range(10)
    ]

    assert counts == [12, 13] * 5
    assert sum(counts) / len(counts) == BOARD_SIZE / 2


def test_dual_words_are_a_subset_of_board_words():
    board = _board(style="natural")

    assert board.dual_words <= set(board.words)
    assert all(w.startswith("dual") for w in board.dual_words)


def test_words_are_shuffled_rather_than_grouped_by_pool():
    # If the two pools were merely concatenated, every dual word would sit
    # before every regular word and the ordering would leak which words are
    # ambiguous — prompts render the board in exactly this order.
    # Exercised on a fixed fractional style because that is the only path that
    # concatenates the two pools; `natural` interleaves them as it draws.
    board = _board(style="dual_50")
    dual_positions = [i for i, w in enumerate(board.words) if board.is_dual(w)]

    assert max(dual_positions) > BOARD_SIZE - len(board.dual_words)


def test_generate_board_raises_on_unknown_style():
    with pytest.raises(ValueError, match="unknown board style"):
        generate_board(_regular(), _dual(), seed=1, style="standard")


def test_generate_board_raises_when_dual_pool_too_small_for_style():
    with pytest.raises(ValueError, match="dual_100"):
        generate_board(_regular(), _dual(10), seed=1, style="dual_100")


def test_generate_board_raises_when_regular_pool_too_small_for_style():
    with pytest.raises(ValueError, match="dual_0"):
        generate_board(_regular(10), _dual(), seed=1, style="dual_0")


def test_generate_board_records_its_style():
    for style in BOARD_STYLES:
        assert generate_board(_regular(), _dual(), seed=1, style=style).style == style


def test_board_words_roles_and_dual_words_are_genuinely_immutable():
    board = _board()

    assert isinstance(board.words, tuple)
    assert isinstance(board.dual_words, frozenset)
    with pytest.raises(TypeError):
        board.roles["reg0"] = "target"


def test_retired_styles_still_generate_the_boards_past_runs_recorded():
    # M1-M3 ran `dual_50` and `dual_80`. They are out of the design, but their
    # boards have to stay reproducible from (style, seed) or those results can't
    # be re-analysed.
    assert not set(RETIRED_BOARD_STYLES) & set(BOARD_STYLES)
    for style in RETIRED_BOARD_STYLES:
        board = generate_board(_regular(), _dual(), seed=1, style=style)

        assert len(board.dual_words) == dual_count(style, seed=1)
        assert len(board.words) == BOARD_SIZE


def test_every_style_the_loader_knows_can_be_generated():
    for style in ALL_BOARD_STYLES:
        assert generate_board(_regular(), _dual(), seed=1, style=style).style == style


def test_natural_draws_freely_instead_of_forcing_a_share():
    # The point of `natural` is that nothing fixes the count: it is whatever the
    # deck deals. Pinning it to a share would make it another controlled rung.
    counts = {
        len(generate_board(_regular(), _dual(), seed=seed, style="natural").dual_words)
        for seed in range(40)
    }

    assert len(counts) > 1
    with pytest.raises(ValueError, match="varies board to board"):
        dual_count("natural", seed=0)


def test_natural_draws_from_both_pools_without_replacement():
    board = _board(style="natural")

    assert len(set(board.words)) == BOARD_SIZE
    assert board.dual_words == {w for w in board.words if w.startswith("dual")}


def test_natural_dual_share_tracks_the_pool_composition():
    # A quarter of this fixture's combined pool is dual, so that is the share a
    # free draw should land on — the style has no share of its own.
    regular, dual = _regular(75), _dual(25)
    counts = [
        len(generate_board(regular, dual, seed=seed, style="natural").dual_words)
        for seed in range(300)
    ]

    assert 0.25 * BOARD_SIZE - 0.5 < sum(counts) / len(counts) < 0.25 * BOARD_SIZE + 0.5


def test_natural_raises_when_the_two_pools_together_are_too_small():
    with pytest.raises(ValueError, match="pools hold"):
        generate_board(_regular(10), _dual(10), seed=1, style="natural")
