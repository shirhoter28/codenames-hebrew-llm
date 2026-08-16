import pytest

from codenames_heb.board import BOARD_SIZE, BOARD_STYLES, ROLE_COUNTS, generate_board


def _regular(n: int = 40) -> list[str]:
    return [f"reg{i}" for i in range(n)]


def _dual(n: int = 40) -> list[str]:
    return [f"dual{i}" for i in range(n)]


def _board(seed: int = 1, style: str = "dual_50"):
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
    assert _board(seed=1, style="dual_50").words != _board(seed=1, style="dual_80").words


@pytest.mark.parametrize(
    "style,expected",
    [("dual_0", 0), ("dual_80", 20), ("dual_100", 25)],
)
def test_exact_styles_have_fixed_dual_counts(style, expected):
    for seed in range(6):
        board = generate_board(_regular(), _dual(), seed=seed, style=style)

        assert len(board.dual_words) == expected
        assert sum(board.is_dual(w) for w in board.words) == expected


def test_dual_50_alternates_by_seed_parity_and_averages_exactly_half():
    counts = [
        len(generate_board(_regular(), _dual(), seed=seed, style="dual_50").dual_words)
        for seed in range(10)
    ]

    assert counts == [12, 13] * 5
    assert sum(counts) / len(counts) == BOARD_SIZE / 2


def test_dual_words_are_a_subset_of_board_words():
    board = _board(style="dual_80")

    assert board.dual_words <= set(board.words)
    assert all(w.startswith("dual") for w in board.dual_words)


def test_words_are_shuffled_rather_than_grouped_by_pool():
    # If the two pools were merely concatenated, every dual word would sit
    # before every regular word and the ordering would leak which words are
    # ambiguous — prompts render the board in exactly this order.
    board = _board(style="dual_80")
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
