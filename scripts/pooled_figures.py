"""Figures 1 and 2 over M4 + M5 pooled, restricted to the comparable design.

    python scripts/pooled_figures.py results/<m4> results/<m5> --out results/<m5>/figures_pooled

M5 tops M4 up with 360 new boards (seeds 30-149) but on a narrower design:
2 codemasters x 2 guessers x 2 methods x min2. Pooling is only meaningful on
the slice the two runs share, so M4 is filtered to that same subset before the
two are concatenated. Boards are deterministic from (style, seed) and the seed
ranges are disjoint, so no game appears twice.

Safe to run while M5 is still going: raw.jsonl is flushed per game.
"""

import argparse
import dataclasses
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt  # noqa: E402

from codenames_heb import plots  # noqa: E402
from codenames_heb.analysis import load_runs  # noqa: E402

# The design M5 runs. M4 is cut down to this before pooling.
MODELS = ["google/gemini-2.5-flash", "openai/gpt-4o-mini"]
ARM = "min2"


def comparable(data):
    """Both runs reduced to the cells they have in common.

    Cleanest for comparing models to each other, because every model then
    carries the same mix of arms and partners.
    """
    keep = (
        data.games["model"].isin(MODELS)
        & data.games["guesser_model"].isin(MODELS)
        & (data.games["count_constraint"] == ARM)
    )
    games = data.games[keep].copy()
    key = ["run_id", "model", "guesser_model", "method",
           "count_constraint", "board_style", "board_seed", "trial"]
    rounds = data.rounds.merge(games[key].drop_duplicates(), on=key, how="inner")
    return dataclasses.replace(data, games=games, rounds=rounds)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--scope", choices=("comparable", "all"), default="comparable",
        help="'comparable' cuts both runs to the cells they share; 'all' keeps "
             "every game. 'all' is the fuller picture but the runs have "
             "different designs, so a model's arm/partner mix differs between "
             "them and model-to-model comparisons become confounded.",
    )
    args = ap.parse_args(argv)

    data = load_runs(args.runs)
    if args.scope == "comparable":
        data = comparable(data)
    g = data.games
    if g.empty:
        print("no games in the comparable subset yet")
        return 0

    per_run = g.groupby("run_id").size().to_dict()
    boards = g.groupby("board_style")["board_seed"].nunique().to_dict()
    print(f"scope={args.scope}: pooled {len(g):,} games from {len(per_run)} run(s): {per_run}")
    print(f"boards per style: {boards}  (total {sum(boards.values())})")
    if args.scope == "all":
        mix = g.groupby(["model", "count_constraint"]).size().unstack(fill_value=0)
        print("games per codemaster x arm — uneven rows mean model comparisons "
              "are confounded by arm mix:")
        print(mix.to_string())
    print(f"models: {sorted(g['model'].unique())}")
    print(f"methods: {sorted(g['method'].unique())}   arm: {sorted(g['count_constraint'].unique())}")

    args.out.mkdir(parents=True, exist_ok=True)
    for name, build in (("01_outcome_composition", plots.fig_outcome_composition),
                        ("02_game_length", plots.fig_game_length)):
        fig = build(g)
        if fig is None:
            print(f"  {name}: skipped (not enough data yet)")
            continue
        path = args.out / f"{name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
