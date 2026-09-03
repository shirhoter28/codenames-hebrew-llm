"""Board construction checks. Run from repo root: PYTHONPATH=. python -m unittest tests.test_board"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import (
    ASSASSIN_COUNT,
    BLUE_COUNT,
    BOARD_SIZE,
    CIVILIAN_COUNT,
    RED_COUNT,
    ROLE_ASSASSIN,
    ROLE_BLUE,
    ROLE_CIVILIAN,
    ROLE_RED,
    create_board,
    load_wordpool,
)


class TestWordpools(unittest.TestCase):
    def test_regular_has_enough_unique_hebrew_words(self):
        words = load_wordpool("regular")
        self.assertGreaterEqual(len(words), BOARD_SIZE)
        self.assertEqual(len(words), len(set(words)))
        self.assertTrue(any("א" <= ch <= "ת" for w in words for ch in w))

    def test_hyphenated_and_apostrophe_forms_preserved(self):
        words = set(load_wordpool("regular"))
        self.assertIn("כדור-עף", words)
        self.assertIn("נינג'ה", words)

    def test_tag_split_puts_s_in_regular_and_d_in_dual(self):
        regular = set(load_wordpool("regular"))
        dual = set(load_wordpool("dual"))
        self.assertIn("לב", regular)
        self.assertIn("מלך", regular)
        self.assertIn("מאושר", dual)
        self.assertEqual(regular & dual, set())

    def test_union_contains_both_pools_without_duplicates(self):
        regular = set(load_wordpool("regular"))
        dual = set(load_wordpool("dual"))
        union = load_wordpool("union")
        self.assertEqual(len(union), len(set(union)))
        self.assertTrue(regular <= set(union))
        self.assertTrue(dual <= set(union))


class TestCreateBoard(unittest.TestCase):
    def test_role_counts(self):
        board = create_board(seed=0, wordpool="regular")
        counts = {
            ROLE_RED: len(board.red),
            ROLE_BLUE: len(board.blue),
            ROLE_CIVILIAN: len(board.civilian),
            ROLE_ASSASSIN: ASSASSIN_COUNT,
        }
        self.assertEqual(counts[ROLE_RED], RED_COUNT)
        self.assertEqual(counts[ROLE_BLUE], BLUE_COUNT)
        self.assertEqual(counts[ROLE_CIVILIAN], CIVILIAN_COUNT)
        self.assertEqual(board.assassin, board.words_for_role(ROLE_ASSASSIN)[0])
        self.assertEqual(len(board.words), BOARD_SIZE)
        self.assertEqual(len(set(board.words)), BOARD_SIZE)

    def test_same_seed_is_reproducible(self):
        a = create_board(seed=42, wordpool="regular")
        b = create_board(seed=42, wordpool="regular")
        self.assertEqual(a.words, b.words)
        self.assertEqual(a.key_grid, b.key_grid)

    def test_different_seeds_change_the_board(self):
        a = create_board(seed=0, wordpool="regular")
        b = create_board(seed=1, wordpool="regular")
        self.assertTrue(a.words != b.words or a.key_grid != b.key_grid)

    def test_grid_is_5x5_row_major(self):
        board = create_board(seed=7, wordpool="regular")
        self.assertEqual(len(board.grid), 5)
        self.assertEqual(board.grid[0][0], board.words[0])
        self.assertEqual(board.grid[1][0], board.words[5])
        self.assertEqual(board.role_of(board.assassin), ROLE_ASSASSIN)

    def test_does_not_mutate_global_random(self):
        import random

        random.seed(123)
        first = random.random()
        random.seed(123)
        create_board(seed=99, wordpool="regular")
        self.assertEqual(random.random(), first)

    def test_optional_pool_is_a_label_and_does_not_load_csv_name(self):
        custom = [f"א{i:02d}" for i in range(30)]
        board = create_board(
            seed=0, wordpool="regular_in_vocab_word2vec", pool=custom
        )
        self.assertEqual(board.wordpool, "regular_in_vocab_word2vec")
        self.assertTrue(set(board.words) <= set(custom))
        self.assertEqual(len(board.words), BOARD_SIZE)

    def test_same_pool_and_seed_are_the_same_board(self):
        """Intersection condition: model identity does not change sampling."""
        pool = [w for w in load_wordpool("regular") if "-" not in w][:40]
        a = create_board(seed=3, wordpool="regular_in_vocab_intersection_test", pool=pool)
        b = create_board(seed=3, wordpool="regular_in_vocab_intersection_test", pool=pool)
        self.assertEqual(a.words, b.words)
        self.assertEqual(a.key_grid, b.key_grid)

    def test_filtered_pool_never_contains_dropped_words(self):
        subset = [w for w in load_wordpool("regular") if "-" not in w]
        filtered = create_board(
            seed=0, wordpool="regular_no_hyphen_test", pool=subset
        )
        self.assertTrue(all("-" not in w for w in filtered.words))
        self.assertEqual(filtered.wordpool, "regular_no_hyphen_test")


if __name__ == "__main__":
    unittest.main()
