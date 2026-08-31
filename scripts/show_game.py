"""Print a whole game — board, roles, and every round — for qualitative work.

    python scripts/show_game.py results/<run_id> [more runs...] --seed 10 --style dual_100
    python scripts/show_game.py results/<run_id> --list --style dual_100 --seed 10
    python scripts/show_game.py results/<run_id> --seed 10 --cm gemini --md >> notes.md

`report.py` and `pair_tables.py` answer "what do these runs say" in aggregate.
This answers "what actually happened in one game", which is what the error
taxonomy and the qualitative write-up in `docs/examples/` are built from.

Filters are substring matches on the model/method names, so `--cm gemini` and
`--method translate` are enough. Every filter is optional; with none, the first
matching game in the file order is shown. `--list` prints one line per matching
game instead of the transcripts, to find the game worth reading.

`--md` emits the same content as markdown tables, for pasting into a doc.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

ROLE_MARK = {"target": "T", "opponent": "O", "civilian": "-", "assassin": "X"}
ROLE_NAME = {
    "target": "YOUR WORDS",
    "opponent": "OPPONENT",
    "civilian": "CIVILIAN",
    "assassin": "ASSASSIN",
}


def load_boards(run_dirs):
    boards = {}
    for run_dir in run_dirs:
        path = Path(run_dir) / "boards.json"
        if not path.exists():
            continue
        for board in json.loads(path.read_text()):
            boards[(board["style"], board["seed"])] = board
    return boards


def iter_games(run_dirs):
    for run_dir in run_dirs:
        path = Path(run_dir) / "raw.jsonl"
        if not path.exists():
            continue
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if line:
                    yield Path(run_dir).name, json.loads(line)


def matches(game, args):
    def sub(value, needle):
        return needle is None or needle.lower() in str(value).lower()

    return (
        sub(game["model"], args.cm)
        and sub(game["guesser_model"], args.guesser)
        and sub(game["method"], args.method)
        and sub(game["board_style"], args.style)
        and (args.seed is None or game["board_seed"] == args.seed)
        and (args.trial is None or game["trial"] == args.trial)
        and sub(game.get("count_constraint"), args.cc)
        and sub(game.get("outcome"), args.outcome)
        and (args.round is None or any(r["round"] == args.round for r in game["rounds"]))
    )


def game_line(run_id, game):
    return (
        f"{run_id}  {game['board_style']:9s} seed {game['board_seed']:<4d} trial {game['trial']} "
        f"{str(game.get('count_constraint')):5s} {game['method']:18s} "
        f"cm={game['model'].split('/')[-1]:26s} g={game['guesser_model'].split('/')[-1]:26s} "
        f"{game['outcome']}/{game.get('loss_reason') or '-'} len={game['game_length']}"
    )


def render_board(board, plain):
    words, roles = board["words"], board["roles"]
    out = []
    if plain:
        out.append("BOARD  (T=yours  O=opponent  -=civilian  X=assassin)")
        for row in range(0, len(words), 5):
            cells = [f"{ROLE_MARK[roles[w]]} {w}" for w in words[row : row + 5]]
            out.append("  " + "".join(f"{c:<18s}" for c in cells))
        out.append("")
    else:
        out.append("| | | | | |")
        out.append("|---|---|---|---|---|")
        for row in range(0, len(words), 5):
            cells = [f"{ROLE_MARK[roles[w]]} {w}" for w in words[row : row + 5]]
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
    for role in ("target", "opponent", "civilian", "assassin"):
        listed = [w for w in words if roles[w] == role]
        out.append(f"{ROLE_NAME[role]} ({len(listed)}): " + ", ".join(listed))
    out.append("")
    return out


def render_rounds(game, plain):
    out = []
    for rnd in game["rounds"]:
        guesses = [(g["word"], g["role"]) for g in (rnd.get("guess_sequence") or [])]
        shown = ", ".join(f"{w} [{ROLE_MARK.get(r, r)}]" for w, r in guesses) or "—"
        clue = rnd["clue"]
        if rnd.get("en_clue"):
            clue = f"{clue} ({rnd['en_clue']})"
        targets = ", ".join(rnd.get("intended_targets") or [])
        if rnd.get("en_targets"):
            targets += "  /  " + ", ".join(str(t) for t in rnd["en_targets"])
        if plain:
            out.append(f"  round {rnd['round']}  clue {clue}  count {rnd['count']}"
                       f"  [{rnd.get('turn_outcome')}]")
            out.append(f"    intended: {targets}")
            out.append(f"    guesses : {shown}")
            if rnd.get("error"):
                out.append(f"    error   : {rnd['error']}")
            tmap = rnd.get("translation_map")
            if isinstance(tmap, dict):
                pairs = ", ".join(f"{h}={e}" for h, e in tmap.items())
                out.append(f"    gloss   : {pairs}")
            out.append("")
        else:
            out.append(f"| {rnd['round']} | {clue} | {rnd['count']} | {targets} | {shown} "
                       f"| {rnd.get('turn_outcome')} |")
    if not plain:
        out = ["| r | clue | count | intended targets | guesses | turn |",
               "|---|---|---|---|---|---|"] + out + [""]
    return out


def render_glosses(game):
    """One row per board word: how each round glossed it. Only for translate games."""
    rows = {}
    rounds = []
    for rnd in game["rounds"]:
        tmap = rnd.get("translation_map")
        if not isinstance(tmap, dict):
            continue
        rounds.append(rnd["round"])
        for heb, eng in tmap.items():
            rows.setdefault(heb, {})[rnd["round"]] = eng
    if not rounds:
        return []
    drifted = {h: v for h, v in rows.items() if len({str(x) for x in v.values()}) > 1}
    if not drifted:
        return ["_Every board word was glossed the same way in every round._", ""]
    out = ["Board words glossed more than one way across rounds:", "",
           "| word | " + " | ".join(f"r{r}" for r in rounds) + " |",
           "|---" * (len(rounds) + 1) + "|"]
    for heb, per_round in sorted(drifted.items(), key=lambda kv: -len(kv[1])):
        cells = [str(per_round.get(r, "")) for r in rounds]
        out.append(f"| **{heb}** | " + " | ".join(cells) + " |")
    out.append("")
    return out


def render(run_id, game, board, plain):
    head = (
        f"{game['model']} (codemaster, {game['method']}) vs "
        f"{game['guesser_model']} (guesser) · board {game['board_style']} seed "
        f"{game['board_seed']} trial {game['trial']} · count {game.get('count_constraint')} · "
        f"{game['outcome']}"
        + (f" ({game['loss_reason']})" if game.get("loss_reason") else "")
        + f", {game['game_length']} rounds · {run_id}"
    )
    out = ["=" * 100, head, "=" * 100, ""] if plain else [f"### {head}", ""]
    if board:
        out += render_board(board, plain)
    out += render_rounds(game, plain)
    if not plain:
        out += render_glosses(game)
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dirs", nargs="+", type=Path, help="results/<run_id> directories")
    parser.add_argument("--cm", help="codemaster model, substring match")
    parser.add_argument("--guesser", help="guesser model, substring match")
    parser.add_argument("--method", help="prompt method, substring match")
    parser.add_argument("--style", help="board style, substring match")
    parser.add_argument("--seed", type=int, help="board seed")
    parser.add_argument("--trial", type=int, help="trial index")
    parser.add_argument("--cc", help="count constraint, e.g. min2 or free")
    parser.add_argument("--outcome", help="win or loss")
    parser.add_argument("--round", type=int, help="only games that reached this round")
    parser.add_argument("--list", action="store_true", help="list matching games, one per line")
    parser.add_argument("--md", action="store_true", help="markdown output instead of plain text")
    parser.add_argument("-n", "--limit", type=int, default=1, help="how many games to print")
    args = parser.parse_args(argv)

    boards = load_boards(args.run_dirs)
    shown = 0
    for run_id, game in iter_games(args.run_dirs):
        if not matches(game, args):
            continue
        if args.list:
            print(game_line(run_id, game))
            shown += 1
            continue
        board = boards.get((game["board_style"], game["board_seed"]))
        print("\n".join(render(run_id, game, board, plain=not args.md)))
        shown += 1
        if shown >= args.limit:
            break
    if not shown:
        print("no games matched those filters", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
