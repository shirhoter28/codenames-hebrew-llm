"""Clue validity v2. PYTHONPATH=. python -m unittest tests.test_validity"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import create_board
from codenames.game import OUTCOME_ASSASSIN, SingleTeamGame
from codenames.players import AssassinGuesser, ScriptedCodemaster
from codenames.validity import (
    FALLBACK_CLUE,
    FALLBACK_CLUE_NUM,
    MAX_INVALID_CLUES,
    VALIDITY_VERSION,
    check_clue,
)


class TestCheckClue(unittest.TestCase):
    def test_legal_hebrew_token(self):
        result = check_clue("בדיקה", 1, ["חתול", "עיר"])
        self.assertTrue(result.ok)
        self.assertEqual(result.clue, "בדיקה")
        self.assertEqual(result.version, VALIDITY_VERSION)

    def test_strips_edges_but_rejects_internal_space(self):
        self.assertTrue(check_clue("  בדיקה  ", 2, []).ok)
        self.assertFalse(check_clue("שתי מילים", 1, []).ok)

    def test_rejects_empty_and_negative_number(self):
        self.assertFalse(check_clue("", 1, []).ok)
        self.assertFalse(check_clue("בדיקה", -1, []).ok)

    def test_rejects_board_word_and_containing_forms(self):
        remaining = ["חתול", "כדור-עף"]
        self.assertFalse(check_clue("חתול", 1, remaining).ok)
        self.assertFalse(check_clue("חתולים", 1, remaining).ok)
        self.assertFalse(check_clue("כדור-עף", 1, remaining).ok)
        self.assertFalse(check_clue("כדור", 1, remaining).ok)
        unrelated = check_clue("בדיקה", 1, remaining)
        self.assertTrue(unrelated.ok)


class TestClueRetryInGame(unittest.TestCase):
    def test_retries_then_accepts_valid_clue(self):
        board = create_board(seed=0, wordpool="regular")
        illegal = board.words[0]
        cm = ScriptedCodemaster([(illegal, 1), ("בדיקה", 1)])
        result = SingleTeamGame(
            board, cm, AssassinGuesser(board.assassin), do_print=False
        ).run()
        self.assertEqual(result.turns[0].clue, "בדיקה")
        self.assertEqual(len(result.turns[0].invalid_clue_attempts), 1)
        self.assertFalse(result.turns[0].used_clue_fallback)
        self.assertIn("remaining board word", result.turns[0].invalid_clue_attempts[0].reason)
        self.assertEqual(cm.invalid_reasons[0], result.turns[0].invalid_clue_attempts[0].reason)

    def test_fallback_after_too_many_invalid_clues(self):
        board = create_board(seed=0, wordpool="regular")
        cm = ScriptedCodemaster([(board.words[0], 1)])
        result = SingleTeamGame(
            board, cm, AssassinGuesser(board.assassin), do_print=False
        ).run()
        self.assertEqual(result.outcome, OUTCOME_ASSASSIN)
        self.assertTrue(result.turns[0].used_clue_fallback)
        self.assertEqual(result.turns[0].clue, FALLBACK_CLUE)
        self.assertEqual(result.turns[0].clue_num, FALLBACK_CLUE_NUM)
        self.assertEqual(len(result.turns[0].invalid_clue_attempts), MAX_INVALID_CLUES)
        self.assertEqual(result.validity_version, VALIDITY_VERSION)


if __name__ == "__main__":
    unittest.main()
