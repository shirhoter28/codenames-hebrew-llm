"""Emit Overleaf-ready LaTeX for the report's figures and its pair table.

Writes `docs/paper_figures.tex`. Paste the body into the paper and upload
`docs/paper_figures_bare/*.png` to a `figures/` folder in the Overleaf project
— the *bare* set, which carries no title or subtitle of its own, because the
caption below each figure says all of that in the document's own type.

`docs/paper_figures/` holds the same figures with their titles burnt in, for
reading in `paper.md`. Do not upload those: the title would then appear twice.

Usage: PYTHONPATH=src:. python scripts/paper_latex.py
"""

from __future__ import annotations

from pathlib import Path

from codenames_heb.analysis import load_runs
from scripts.paper_figures import FACTORIAL, english_pair_frame

OUT = Path("docs/paper_figures.tex")
OUT_HALF = Path("docs/paper_figures_half.tex")

# Half-width pairs: two subfigures side by side in one float. Each entry is
# (label, overall caption, [(stem, subcaption), (stem, subcaption)]).
PAIRS = [
    ("standing", "Where the models stand. (a) each model in each role, averaged over "
     "every other factor; (b) all 16 codemaster--guesser pairs, with self-play on the "
     "diagonal. Factorial run, 90 boards.",
     [("fig01_role_headline", "Performance by role"),
      ("fig03_pair_matrix", "Every pair")]),
    ("factors", "The two designed factors, each averaged over the other and over the "
     "clue-count floor and the guesser. Factorial run.",
     [("fig21a_method", "Prompt method"),
      ("fig21b_ambiguity", "Board ambiguity")]),
    ("factorssubset", "The same two factors for gemini-2.5-flash and gpt-4o-mini in both "
     "roles, pooled over both runs -- 150 boards behind each ambiguity bar.",
     [("fig25a_method_subset", "Prompt method"),
      ("fig25b_ambiguity_subset", "Board ambiguity")]),
    ("variation", "(a) every board's own win rate, both runs pooled; (b) mean clue "
     "number by round in the free-choice arm, where no floor is imposed.",
     [("fig22_board_variance", "Board-to-board variation"),
      ("fig24_ambition_free", "Clue ambition over a game")]),
    ("newpair", "(a) the pair grid with each model's overall performance on the margin; "
     "(b) three ambiguous Hebrew words and the English sense each codemaster assigned.",
     [("fig29_pair_matrix_margins", "Pairs with margins"),
      ("fig30_gloss_three_words", "Sense split, three words")]),
    ("firstguess", "First guess against the chance rate for the pool at that moment. "
     "(a) all four codemasters on the factorial; (b) the two-model grid on all 450 boards.",
     [("fig23_first_guess_labeled", "All four codemasters"),
      ("fig26_first_guess_subset", "Two-model grid")]),
]


# (file stem, label, short caption for the list of figures, full caption)
FIGURES = [
    ("fig01_role_headline", "role",
     "Model performance in each role",
     "Each model as codemaster (top) and as guesser (bottom), over the "
     "factorial's 90 boards, averaged across every prompt method, clue-count "
     "floor, board style and partner model. The two roles do not rank alike."),
    ("fig03_pair_matrix", "pairs",
     "Every codemaster against every guesser",
     "All 16 codemaster--guesser pairs; the diagonal is self-play. Win rate "
     "(left) and rounds to win (right). Factorial, 90 boards."),
    ("fig21_factors_separately", "factors",
     "The two designed factors",
     "Left: prompt method, each bar pooling all three board styles. Right: "
     "board ambiguity, each bar pooling both prompt methods. Every bar also "
     "averages over the clue-count floor and the guesser. Factorial."),
    ("fig22_board_variance", "boards",
     "Board-to-board variation",
     "One dot per board: its win rate over every game any pair played on it. "
     "The thick bar is the style mean, the thin line its interquartile range. "
     "Both runs pooled, 150 boards per style."),
    ("fig23_first_guess_labeled", "firstguess",
     "First guess against chance",
     "Coloured bar: how often a round's first guess landed on a target. Grey "
     "bar: the chance of that, given the words still standing. The bold number "
     "is the gap. Factorial, 30 boards per column."),
    ("fig24_ambition_free", "ambition",
     "Clue ambition falls as the board empties",
     "Mean clue number by round, free-choice arm only, so nothing here is "
     "imposed by a floor. Each point rests on at least 30 rounds."),
    ("fig25_factors_subset", "factorssubset",
     "The two designed factors, two-model grid",
     "The same two panels as Fig.~\\ref{fig:factors}, for gemini-2.5-flash and "
     "gpt-4o-mini in both roles, pooled over both runs. Five times the boards "
     "behind each ambiguity bar."),
    ("fig26_first_guess_subset", "firstguesssubset",
     "First guess against chance, two-model grid",
     "The same grid at the round level, on 150 boards per column."),
    ("fig29_pair_matrix_margins", "pairsmargins",
     "Every pair, with each model's overall performance",
     "The 16 pairs, plus a margin: the last column is a codemaster's mean across all "
     "four guessers, the last row a guesser's mean across all four codemasters, and the "
     "corner cell the grand mean. Margins are painted on a separate grey ramp because "
     "they summarise a row or column rather than naming a pair that was played."),
    ("fig30_gloss_three_words", "glossshort",
     "Which English sense each codemaster reaches for",
     "Three ambiguous Hebrew words under English-Pivot: one the models agree on "
     "(\\texthebrew{מלח}), one they split on (\\texthebrew{מטר}), and one where the "
     "strongest model is the odd one out (\\texthebrew{אלים}). Grey is a gloss naming "
     "both senses; a bar short of full width means the model named neither."),
    ("fig28_gloss_sense_split", "gloss",
     "Which English sense each codemaster reaches for",
     "Six ambiguous Hebrew words and the English sense each codemaster assigned "
     "when translating the board under English-Pivot. Grey is a gloss naming "
     "both senses; a bar short of full width means the model named neither."),
]

# These are wide; in a two-column template they need the starred environment.
WIDE = {"fig03_pair_matrix", "fig21_factors_separately", "fig23_first_guess_labeled",
        "fig25_factors_subset", "fig26_first_guess_subset", "fig28_gloss_sense_split",
        "fig01_role_headline", "fig29_pair_matrix_margins", "fig30_gloss_three_words"}


def esc(text: str) -> str:
    """Escape the characters LaTeX treats specially in our cell values."""
    for a, b in [("\\", r"\textbackslash{}"), ("%", r"\%"), ("_", r"\_"),
                 ("&", r"\&"), ("#", r"\#"), ("$", r"\$")]:
        text = text.replace(a, b)
    return text.replace("–", "--")


def figure_block(stem, label, short, caption) -> str:
    env = "figure*" if stem in WIDE else "figure"
    return (
        f"\\begin{{{env}}}[t]\n"
        f"  \\centering\n"
        f"  \\includegraphics[width=\\linewidth]{{figures/{stem}.png}}\n"
        f"  \\caption[{short}]{{\\textbf{{{short}.}} {caption}}}\n"
        f"  \\label{{fig:{label}}}\n"
        f"\\end{{{env}}}\n"
    )


def pair_table_tex(frame) -> str:
    cols = list(frame.columns)
    # Left-align the pair name, right-align every number.
    spec = "l" + "r" * (len(cols) - 1)
    header = " & ".join(f"\\textbf{{{esc(c)}}}" for c in cols) + r" \\"
    lines = []
    for i, row in enumerate(frame.values):
        lines.append(" & ".join(esc(str(v)) for v in row) + r" \\")
        # A rule between codemaster blocks, as the reference table prints it.
        if (i + 1) % 4 == 0 and i + 1 < len(frame):
            lines.append(r"\midrule")
    body = "\n    ".join(lines)
    return (
        "\\begin{table*}[t]\n"
        "  \\centering\n"
        "  \\caption{Agent results for the single-team Hebrew version. One row per\n"
        "  codemaster--guesser pair, ordered by codemaster then guesser. Length\n"
        "  columns are rounds; Opponent and Civilian are words revealed per game;\n"
        "  Stop Early and Stop Late are over eligible rounds.}\n"
        "  \\label{tab:pairs}\n"
        "  \\scriptsize\n"
        # 14 columns will not fit a two-column page width on its own. resizebox
        # is the robust answer: it shrinks to fit whatever \textwidth is, so the
        # table survives a template change. Drop it and shorten the headers by
        # hand if the type gets too small to read.
        "  \\resizebox{\\textwidth}{!}{%\n"
        f"  \\begin{{tabular}}{{{spec}}}\n"
        "    \\toprule\n"
        f"    {header}\n"
        "    \\midrule\n"
        f"    {body}\n"
        "    \\bottomrule\n"
        "  \\end{tabular}}\n"
        "\\end{table*}\n"
    )


PREAMBLE = r"""% ---------------------------------------------------------------
% Preamble additions this file needs
% ---------------------------------------------------------------
% \usepackage{graphicx}   % \includegraphics
% \usepackage{booktabs}   % \toprule \midrule \bottomrule
% \usepackage{graphbox}   % (optional) nothing here needs it
% \graphicspath{{figures/}}
%
% Upload docs/paper_figures_bare/*.png as figures/ -- that set has no title or
% subtitle drawn on it, because \caption supplies both. Its type is scaled up
% 1.45x so it stays legible after the figure is shrunk to \linewidth.
%
% HEBREW: the discussion quotes Hebrew words. pdfLaTeX cannot set them.
% Compile with XeLaTeX or LuaLaTeX (Overleaf: Menu -> Compiler) and add:
%   \usepackage{polyglossia}
%   \setmainlanguage{english}
%   \setotherlanguage{hebrew}
%   \newfontfamily\hebrewfont{Noto Sans Hebrew}[Script=Hebrew]
% then write a Hebrew word as \texthebrew{...}. The figures themselves need
% none of this -- their Hebrew is already pixels.
%
% Every figure below is \linewidth. In a two-column template (IEEE, ACM) the
% wide ones use figure*/table*, which float to the top of a page and cannot be
% placed with [h]. Reference them as Fig.~\ref{fig:role}, Table~\ref{tab:pairs}.
% ---------------------------------------------------------------

"""


def pair_block(label, caption, subs) -> str:
    parts = ["\\begin{figure}[ht]\n    \\centering\n"]
    for i, (stem, sub) in enumerate(subs):
        if i:
            parts.append("    \\hfill\n")
        parts.append(
            "    \\begin{subfigure}{0.48\\linewidth}\n"
            "        \\centering\n"
            f"        \\includegraphics[width=\\linewidth]{{figures/{stem}.png}}\n"
            f"        \\caption{{{sub}}}\n"
            f"        \\label{{fig:{label}-{'ab'[i]}}}\n"
            "    \\end{subfigure}\n")
    parts.append(f"\n    \\caption{{{caption}}}\n    \\label{{fig:{label}}}\n"
                 "\\end{figure}\n")
    return "".join(parts)


HALF_PREAMBLE = r"""% ---------------------------------------------------------------
% Half-width subfigure pairs. Needs, in addition to graphicx/booktabs:
%   \usepackage{subcaption}
%
% Upload docs/paper_figures_half/*.png as figures/. That set is drawn on a
% canvas half as wide as the full-width set, so at 0.48\linewidth its type
% lands at the same size on the page -- do not mix the two directories.
%
% Two figures have no half-width version and stay full width: the pair table
% (14 columns) and the gloss chart (six panels). Take those from
% docs/paper_figures_bare/ and paper_figures.tex.
% ---------------------------------------------------------------

"""


def main() -> None:
    data = load_runs([f"results/{FACTORIAL}"])
    frame = english_pair_frame(data.games, data.rounds)
    parts = [PREAMBLE, "% === Table 1 " + "=" * 55 + "\n\n", pair_table_tex(frame), "\n"]
    for stem, label, short, caption in FIGURES:
        parts.append(f"% === {short} " + "=" * max(4, 60 - len(short)) + "\n\n")
        parts.append(figure_block(stem, label, short, caption))
        parts.append("\n")
    OUT.write_text("".join(parts))
    print(f"wrote {OUT} — {len(FIGURES)} figures + 1 table")

    half = [HALF_PREAMBLE]
    for label, caption, subs in PAIRS:
        half.append(pair_block(label, caption, subs))
        half.append("\n")
    OUT_HALF.write_text("".join(half))
    print(f"wrote {OUT_HALF} — {len(PAIRS)} subfigure pairs")


if __name__ == "__main__":
    main()
