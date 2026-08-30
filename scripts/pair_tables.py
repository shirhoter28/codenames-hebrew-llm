"""Codemaster x guesser summary tables, in the shape of the English benchmark's
Table I.

    python scripts/pair_tables.py results/<run_id> [more runs...] [--out DIR]

Writes `pair_tables.md` (formatted for reading, one table per stratum) and
`pair_tables.csv` (every table stacked tidily, for a spreadsheet) next to the
run. Deliberately *not* part of `report.py`: the report answers "what does this
run say", one section per stratification; this answers "how does each pair
compare with the published English results", in their layout.

`docs/previous_results_english.png` is the table being matched — Stephenson,
Sidji & Ronval, Table I, "Agent Results for Single Team Codenames Version".

Every table carries all codemaster x guesser pairs. The first pools every arm;
the rest cut by one factor at a time (prompt method, clue-count floor, board
style) and average over the other two. Because the design crosses every pair
with every level of every factor, a cut changes what is averaged over without
ever dropping a pair.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd  # noqa: E402

from codenames_heb.analysis import PAIR_STRATA, load_runs, pair_table, style_order  # noqa: E402
from codenames_heb.plots import count_floor_order, short_model  # noqa: E402

# Column label -> how to build the cell from a row. Ordered as the paper orders
# them, with `games` / `rounds` added: the paper's cells all hold the same
# number of games and ours do not.
COLUMNS = (
    ("Model Pair (codemaster - guesser)",
     lambda r: f"{short_model(r['model'])} - {short_model(r['guesser_model'])}"),
    ("Games", lambda r: _int(r["games"])),
    ("Rounds", lambda r: _int(r["rounds"])),
    ("Mean", lambda r: _num(r["length_mean"])),
    ("Median", lambda r: _int(r["length_median"])),
    ("Min", lambda r: _int(r["length_min"])),
    ("Std Dev", lambda r: _num(r["length_sd"])),
    ("Loss", lambda r: _pct(r["loss_rate"])),
    ("Mean (without loss)", lambda r: _num(r["length_mean_wins"])),
    ("Opponent avg(stdev)", lambda r: _spread(r, "opponent")),
    ("Civilian avg(stdev)", lambda r: _spread(r, "civilian")),
    ("Clues avg(stdev)", lambda r: _spread(r, "clue_count")),
    ("Guesses avg(stdev)", lambda r: _spread(r, "guesses")),
    ("Stop Early", lambda r: _pct(r["stop_early_rate"])),
    ("Stop Late", lambda r: _pct(r["stop_late_rate"])),
)

# How each stratum's levels are ordered, and what to call the section.
STRATUM_TITLES = {
    "method": "By prompt method",
    "count_constraint": "By clue-count floor",
    "board_style": "By board style",
}


def _missing(value) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value))


def _int(value) -> str:
    return "—" if _missing(value) else str(int(round(float(value))))


def _num(value, places: int = 2) -> str:
    return "—" if _missing(value) else f"{float(value):.{places}f}"


def _pct(value) -> str:
    return "—" if _missing(value) else f"{float(value) * 100:.1f}%"


def _spread(row, label: str) -> str:
    """`2.51 (1.67)` — the paper's avg(stdev) cell."""
    mean, sd = row.get(f"{label}_mean"), row.get(f"{label}_sd")
    if _missing(mean):
        return "—"
    return f"{float(mean):.2f} ({_num(sd)})"


def level_order(column: str, values) -> list:
    """Levels in their designed order, not alphabetical.

    The floors are a ladder (`min10` sorts between `free` and `min2` as a
    string) and the board styles are one too; only the two prompt methods have
    no order of their own.
    """
    values = [v for v in pd.Series(list(values)).dropna().unique()]
    if column == "count_constraint":
        return count_floor_order(values)
    if column == "board_style":
        return style_order(values)
    return sorted(values)


def to_markdown(table: pd.DataFrame) -> str:
    """The pair table as a fixed-width markdown table.

    Rows are grouped by codemaster, as the paper groups them, so a block reads
    as "this codemaster against each partner in turn".
    """
    if table.empty:
        return "_(no completed games in this stratum)_"

    ordered = table.sort_values(["model", "guesser_model"])
    header = [label for label, _ in COLUMNS]
    rows = [[build(row) for _, build in COLUMNS] for _, row in ordered.iterrows()]
    widths = [
        max(len(header[i]), *(len(row[i]) for row in rows)) for i in range(len(header))
    ]

    def line(cells):
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    return "\n".join(
        [line(header), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
        + [line(row) for row in rows]
    )


def build_document(data, run_label: str) -> tuple:
    """The markdown document, and the tidy frame behind it."""
    games, rounds = data.games, data.rounds
    pooled = pair_table(games, rounds)

    lines = [
        f"# Codemaster x guesser pair results — {run_label}",
        "",
        "Laid out like Table I of Stephenson, Sidji & Ronval (`docs/"
        "previous_results_english.png`) so the Hebrew results can be read "
        "against the published English ones.",
        "",
        f"- Completed games: **{int(games['completed'].sum())}** of {len(games)}",
        f"- Pairs: {len(pooled)} ({games['model'].nunique()} codemasters x "
        f"{games['guesser_model'].nunique()} guessers)",
        "",
        "### How to read these columns",
        "",
        "- `Mean` / `Median` / `Min` / `Std Dev` are the game length in rounds, "
        "over **completed games only**. `Mean (without loss)` is the same over "
        "won games alone — a lost game is short because it ended on the "
        "assassin, so pooling the two makes a pair that dies early look "
        "efficient.",
        "- `Opponent` and `Civilian` are words of that role revealed per game. "
        "The English table calls the first one `Blue`; revealing one ends the "
        "turn *and* advances the opposing team, where a civilian only ends the "
        "turn.",
        "- `Clues` is the count the codemaster commits each clue to; `Guesses` "
        "is how many the guesser actually made. Both are per round.",
        "- `Stop Early` / `Stop Late` are over **eligible** rounds, not all "
        "rounds. A guesser may not stop before its first correct guess, so an "
        "early stop is impossible when the clue named a count of 1; counting "
        "those rounds would deflate the rate for reasons unrelated to the "
        "guesser's judgement. `Stop Late` is the bonus (count + 1) guess being "
        "taken.",
        "- `Games` and `Rounds` are printed because our cells are not all the "
        "same size, unlike the paper's. A mean over 30 games is not the same "
        "evidence as one over 500.",
        "",
        "## All arms pooled",
        "",
        "Every prompt method, clue-count floor and board style averaged "
        "together. This is the row-for-row analogue of the published table.",
        "",
        to_markdown(pooled),
        "",
    ]

    tidy = [pooled.assign(stratum="all", level="all")]

    for column in PAIR_STRATA:
        if column not in games.columns or games[column].nunique(dropna=False) < 2:
            continue
        lines += [f"## {STRATUM_TITLES[column]}", "",
                  f"One table per {column.replace('_', ' ')}, each averaging over "
                  "the other two factors. Every pair appears in every table.", ""]
        for level in level_order(column, games[column]):
            subset_games = games[games[column].astype(str) == str(level)]
            subset_rounds = rounds[rounds[column].astype(str) == str(level)]
            table = pair_table(subset_games, subset_rounds)
            lines += [f"### {column} = `{level}`", "", to_markdown(table), ""]
            tidy.append(table.assign(stratum=column, level=str(level)))

    frame = pd.concat(tidy, ignore_index=True)
    lead = ["stratum", "level", "model", "guesser_model"]
    frame = frame[lead + [c for c in frame.columns if c not in lead]]
    return "\n".join(lines), frame


def main(argv=None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path, help="results/<run_id> directories")
    parser.add_argument("--out", type=Path, default=None,
                        help="output directory (defaults to the single run's directory)")
    args = parser.parse_args(argv)

    try:
        data = load_runs(args.run_dirs)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, f"error: {exc}\n")

    out_dir = args.out or (
        args.run_dirs[0] if len(args.run_dirs) == 1 else PROJECT_ROOT / "results"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    document, frame = build_document(data, ", ".join(data.run_ids))
    md_path = out_dir / "pair_tables.md"
    csv_path = out_dir / "pair_tables.csv"
    md_path.write_text(document, encoding="utf-8")
    frame.to_csv(csv_path, index=False)

    print(f"Tables written to {md_path}")
    print(f"{len(frame)} rows written to {csv_path}")
    return md_path


if __name__ == "__main__":
    main()
