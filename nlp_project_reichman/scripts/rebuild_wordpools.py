#!/usr/bin/env python3
"""Rebuild regular.csv / dual.csv from labeled spreadsheet exports.

Both source tabs are read. Second-column tag:
- r or s → regular
- d → dual

Order: regular-tab file first, then dual-meaning-tab file.
First occurrence of a word wins. A word tagged both regular and dual is an error.

Usage (from repo root):

    python scripts/rebuild_wordpools.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORDPOOL_DIR = REPO_ROOT / "data" / "wordpools"
REGULAR_TAB = WORDPOOL_DIR / "source_regular_tab.csv"
DUAL_TAB = WORDPOOL_DIR / "source_dual_tab.csv"

REGULAR_TAGS = frozenset({"r", "s"})
DUAL_TAGS = frozenset({"d"})


def _parse_labeled(path: Path) -> list[tuple[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[tuple[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header or (header[0] or "").strip() != "מילה":
            raise ValueError(f"Expected מילה header in {path}, found {header}")
        for line_no, parts in enumerate(reader, start=2):
            if not parts or not any((p or "").strip() for p in parts):
                continue
            word = (parts[0] or "").strip()
            tag = (parts[1] if len(parts) > 1 else "").strip().lower()
            if not word:
                raise ValueError(f"{path}:{line_no} empty word")
            if tag not in REGULAR_TAGS | DUAL_TAGS:
                raise ValueError(f"{path}:{line_no} {word!r} has tag {tag!r}")
            rows.append((word, tag))
    return rows


def assign(sources: list[list[tuple[str, str]]]) -> tuple[list[str], list[str]]:
    regular: list[str] = []
    dual: list[str] = []
    seen: dict[str, str] = {}
    for rows in sources:
        for word, tag in rows:
            bucket = "regular" if tag in REGULAR_TAGS else "dual"
            if word in seen:
                if seen[word] != bucket:
                    raise ValueError(f"{word!r} labeled {seen[word]} and {bucket}")
                continue
            seen[word] = bucket
            if bucket == "regular":
                regular.append(word)
            else:
                dual.append(word)
    return regular, dual


def _write_words(path: Path, words: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["מילה"])
        for word in words:
            writer.writerow([word])


def main() -> None:
    regular_tab = _parse_labeled(REGULAR_TAB)
    dual_tab = _parse_labeled(DUAL_TAB)
    regular, dual = assign([regular_tab, dual_tab])
    overlap = set(regular) & set(dual)
    if overlap:
        raise SystemExit(f"regular and dual must be disjoint; overlap={sorted(overlap)}")
    _write_words(WORDPOOL_DIR / "regular.csv", regular)
    _write_words(WORDPOOL_DIR / "dual.csv", dual)
    print(
        f"regular n={len(regular)}  dual n={len(dual)}  "
        f"union n={len(regular) + len(dual)}"
    )


if __name__ == "__main__":
    main()
