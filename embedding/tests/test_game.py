"""Single-team game loop checks. PYTHONPATH=. python -m unittest tests.test_game"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from codenames.board import create_board
from codenames.game import (
    LOSS_SCORE,
    OUTCOME_ASSASSIN,
    OUTCOME_WIN,
    SingleTeamGame,
)
from codenames.logging_io import write_game_result
from codenames.players import AssassinGuesser, DummyCodemaster, DummyGuesser, OracleGuesser


class TestSingleTeamGame(unittest.TestCase):
    def test_oracle_wins_in_nine_turns(self):
        board = create_board(seed=0, wordpool="regular")
        guesser = OracleGuesser(board.role_of)
        result = SingleTeamGame(
            board, DummyCodemaster(), guesser, do_print=False
        ).run()
        self.assertEqual(result.outcome, OUTCOME_WIN)
        self.assertEqual(result.num_turns, 9)
        self.assertEqual(result.score, 9)
        self.assertEqual(result.red_revealed, 9)
        self.assertFalse(result.assassin_revealed)
        self.assertEqual(result.turns[0].clue, "בדיקה")
        self.assertEqual(result.turns[0].clue_num, 1)

    def test_assassin_guess_is_a_loss(self):
        board = create_board(seed=0, wordpool="regular")
        guesser = AssassinGuesser(board.assassin)
        result = SingleTeamGame(
            board, DummyCodemaster(), guesser, do_print=False
        ).run()
        self.assertEqual(result.outcome, OUTCOME_ASSASSIN)
        self.assertEqual(result.num_turns, 1)
        self.assertEqual(result.score, LOSS_SCORE)
        self.assertTrue(result.assassin_revealed)

    def test_dummy_game_finishes(self):
        board = create_board(seed=0, wordpool="regular")
        result = SingleTeamGame(
            board, DummyCodemaster(), DummyGuesser(), do_print=False
        ).run()
        self.assertIn(result.outcome, {OUTCOME_WIN, OUTCOME_ASSASSIN, "blue_cleared"})
        self.assertGreaterEqual(result.num_turns, 1)

    def test_same_seed_same_transcript(self):
        def play():
            board = create_board(seed=3, wordpool="regular")
            return SingleTeamGame(
                board, DummyCodemaster(), DummyGuesser(), do_print=False
            ).run()

        a, b = play(), play()
        self.assertEqual(a.board_words, b.board_words)
        self.assertEqual(a.key_grid, b.key_grid)
        self.assertEqual(
            [(t.clue, t.clue_num, [(g.word, g.role) for g in t.guesses]) for t in a.turns],
            [(t.clue, t.clue_num, [(g.word, g.role) for g in t.guesses]) for t in b.turns],
        )
        self.assertEqual(a.outcome, b.outcome)

    def test_write_game_result_appends_and_does_not_overwrite(self):
        board = create_board(seed=0, wordpool="regular")
        result = SingleTeamGame(
            board, DummyCodemaster(), OracleGuesser(board.role_of), do_print=False
        ).run()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            jsonl = tmp_path / "games.jsonl"
            with mock.patch("codenames.logging_io.RESULTS_DIR", tmp_path), mock.patch(
                "codenames.logging_io.GAMES_JSONL", jsonl
            ):
                path1 = write_game_result(result)
                path2 = write_game_result(result)
            self.assertNotEqual(path1, path2)
            self.assertTrue(path1.exists())
            self.assertTrue(path2.exists())
            lines = jsonl.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            payload = json.loads(path1.read_text(encoding="utf-8"))
            for key in (
                "seed",
                "wordpool",
                "board_words",
                "key_grid",
                "turns",
                "outcome",
                "num_turns",
                "score",
                "codemaster",
                "validity_version",
            ):
                self.assertIn(key, payload)
            self.assertIn("remaining_red", payload["turns"][0])


if __name__ == "__main__":
    unittest.main()
