import pytest

from codenames_heb.board import ROLE_COUNTS, generate_board


def _pool(n: int = 40) -> list[str]:
    return [f"word{i}" for i in range(n)]


def test_generate_board_has_25_unique_words():
    board = generate_board(_pool(), seed=1)

    assert len(board.words) == 25
    assert len(set(board.words)) == 25


def test_generate_board_role_counts_match_standard_distribution():
    board = generate_board(_pool(), seed=1)

    counts = {role: len(board.words_with_role(role)) for role in ROLE_COUNTS}

    assert counts == ROLE_COUNTS


def test_generate_board_role_of_matches_words_with_role():
    board = generate_board(_pool(), seed=1)

    for role in ROLE_COUNTS:
        for word in board.words_with_role(role):
            assert board.role_of(word) == role


def test_generate_board_is_deterministic_for_same_seed():
    board_a = generate_board(_pool(), seed=42)
    board_b = generate_board(_pool(), seed=42)

    assert board_a.words == board_b.words
    assert board_a.roles == board_b.roles


def test_generate_board_differs_for_different_seed():
    board_a = generate_board(_pool(), seed=1)
    board_b = generate_board(_pool(), seed=2)

    assert board_a.words != board_b.words


def test_generate_board_raises_when_pool_too_small():
    with pytest.raises(ValueError):
        generate_board(_pool(10), seed=1)
