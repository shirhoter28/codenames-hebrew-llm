"""Render every curated example in `docs/examples/manifest.json` as a full game.

    python scripts/render_examples.py results/<run_id> [more runs...]

Writes `docs/examples/full_games.md`: one complete transcript per game — board
with roles, every round, and the per-round gloss — with a heading per point the
game illustrates and the `show_game.py` command that reproduces it.

The other files in `docs/examples/` argue from round-level excerpts. This is the
evidence behind them, in full, so a claim can be checked without going back to
`raw.jsonl`.

To add an example: append an entry to `manifest.json` and re-run. A game listed
more than once (several points on one board) is rendered once, under all of its
headings. `python scripts/show_game.py <run> --list` finds the identifying keys.
"""

import argparse
import importlib.util
import json
import sys
from collections import OrderedDict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

MANIFEST = PROJECT_ROOT / "docs" / "examples" / "manifest.json"
OUT = PROJECT_ROOT / "docs" / "examples" / "full_games.md"

_spec = importlib.util.spec_from_file_location(
    "show_game", Path(__file__).resolve().parent / "show_game.py"
)
show_game = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(show_game)

KEY_FIELDS = ("run", "cm", "guesser", "method", "style", "seed", "cc")


def game_key(entry):
    return tuple(entry[f] for f in KEY_FIELDS)


def find_game(games, entry):
    for run_id, game in games:
        if (
            run_id == entry["run"]
            and game["model"] == entry["cm"]
            and game["guesser_model"] == entry["guesser"]
            and game["method"] == entry["method"]
            and game["board_style"] == entry["style"]
            and game["board_seed"] == entry["seed"]
            and str(game.get("count_constraint")) == entry["cc"]
        ):
            return game
    return None


def command_for(entry):
    cc = entry["cc"]
    return (
        f"python scripts/show_game.py results/{entry['run']} \\\n"
        f"    --style {entry['style']} --seed {entry['seed']} "
        f"--method {entry['method'].split('_')[0]} \\\n"
        f"    --cm {entry['cm'].split('/')[-1]} --guesser {entry['guesser'].split('/')[-1]}"
        + (f" --cc {cc}" if cc and cc != "None" else "")
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    entries = json.loads(args.manifest.read_text())
    grouped = OrderedDict()
    for entry in entries:
        grouped.setdefault(game_key(entry), []).append(entry)

    games = list(show_game.iter_games(args.run_dirs))
    boards = show_game.load_boards(args.run_dirs)

    sections = OrderedDict()
    for entry in entries:
        sections.setdefault(entry["section"], []).append(entry)

    lines = [
        "# Full games behind the examples",
        "",
        f"{len(entries)} curated examples across {len(grouped)} games, rendered whole.",
        "The excerpt-level arguments live in "
        "[`codemaster_translation_drift.md`](codemaster_translation_drift.md) and "
        "[`guesser_behaviour.md`](guesser_behaviour.md); this is the evidence behind them.",
        "",
        "Board key: `T` your words · `O` opponent · `-` civilian · `X` assassin.",
        "",
        "Regenerate with `python scripts/render_examples.py results/<run_id> ...` after "
        "editing [`manifest.json`](manifest.json).",
        "",
        "## Contents",
        "",
    ]
    for section, items in sections.items():
        lines.append(f"- **{section}** — {len(items)} examples")
    lines.append("")

    missing, rendered = [], set()
    body = []
    for section, items in sections.items():
        body += [f"\n---\n", f"# {section}", ""]
        for entry in items:
            key = game_key(entry)
            body += [f"## {entry['title']}", "", entry["note"], ""]
            if key in rendered:
                body += ["_Same game as above; see the transcript there._", ""]
                continue
            game = find_game(games, entry)
            if game is None:
                missing.append(entry)
                body += ["_Game not found in the supplied runs._", ""]
                continue
            rendered.add(key)
            board = boards.get((game["board_style"], game["board_seed"]))
            body += ["```", command_for(entry), "```", ""]
            body += show_game.render(entry["run"], game, board, plain=False)

    args.out.write_text("\n".join(lines + body) + "\n")
    print(f"wrote {args.out} — {len(entries)} examples, {len(rendered)} games rendered")
    if missing:
        print(f"WARNING: {len(missing)} not found:", file=sys.stderr)
        for entry in missing:
            print(f"  {entry['title']} :: {game_key(entry)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
