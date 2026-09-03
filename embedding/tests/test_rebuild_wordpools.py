"""Rebuild wordpool tag-split checks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rebuild_wordpools import assign


class TestAssign(unittest.TestCase):
    def test_r_and_s_are_regular_d_is_dual(self) -> None:
        regular, dual = assign(
            [
                [("מלך", "s"), ("מאושר", "d"), ("עץ", "r")],
                [("לב", "s"), ("עץ", "r")],
            ]
        )
        self.assertEqual(regular, ["מלך", "עץ", "לב"])
        self.assertEqual(dual, ["מאושר"])

    def test_conflicting_tags_raise(self) -> None:
        with self.assertRaises(ValueError):
            assign([[("עין", "r")], [("עין", "d")]])


if __name__ == "__main__":
    unittest.main()
