"""The two ambiguity figures: which English sense each codemaster defaults to.

    python scripts/gloss_figures.py results/<run_id> [more runs...] [--out DIR]

Writes `gloss_sense_split.png` (the chart) and `gloss_table.png` (the table) to
`docs/figures/` by default. Both read `translation_map`, which only
`translate_pipeline` games carry, so they pool every such game across the runs
given.

They are a pair. The chart answers "which way does each model lean, and do the
models agree" in one look; the table keeps the English strings behind that lean,
which is what makes the claim checkable.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

from codenames_heb.glosses import SENSES, gloss_counts, sense_shares  # noqa: E402
from codenames_heb.plots import gloss_sense_split, gloss_table  # noqa: E402

# Ordered so the clearest disagreements lead.
WORDS = ["מטר", "קל", "אלים", "קניון", "אוגר", "בר",
         "הודו", "כבד", "תור", "סרט", "מלון", "מלח",
         "אלה", "פה", "זריקה", "שיח", "מטה", "בול"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "docs" / "figures")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    counts = gloss_counts(args.run_dirs, words=SENSES)
    if counts.empty:
        print("no translate_pipeline glosses in those runs", file=sys.stderr)
        return 1
    shares = sense_shares(counts)
    models = sorted(counts["model"].unique())
    words = [w for w in WORDS if w in set(counts["word"])]
    rounds = int(counts["n"].sum())

    chart = gloss_sense_split(
        shares, words, models,
        title="Which English sense does each codemaster reach for?",
        subtitle=f"Share of translate-pipeline rounds, {rounds:,} board-word glosses "
                 f"pooled over {len(args.run_dirs)} runs. Bars are short where the model "
                 f"named neither sense.",
    )
    chart.savefig(args.out / "gloss_sense_split.png", dpi=200,
                  facecolor=chart.get_facecolor())

    table = gloss_table(
        counts, words, models,
        title="The glosses behind the split",
        subtitle="Most frequent English gloss per model, with its share of that "
                 "model's rounds for the word.",
    )
    table.savefig(args.out / "gloss_table.png", dpi=200, facecolor=table.get_facecolor(),
                  bbox_inches="tight")
    print(f"wrote {args.out}/gloss_sense_split.png and {args.out}/gloss_table.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
