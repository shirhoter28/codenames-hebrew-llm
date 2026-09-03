# Hebrew Codenames with word embeddings

NLP Final Project – Reichman University, 2026

Branch: **`clean_embedding`**. Embedding-only. LLM Codemaster code lives on
`main` / `embeddings_method`.

## Goal

Evaluate pretrained Hebrew embeddings as single-team Codenames agents
(codemaster + guesser), including same-model, cross-model, concatenation
(codemaster and, as an added condition, guesser), and board-type conditions.

## Wordpools

Hebrew lists live in `data/wordpools/`. They are **not** “one CSV per spreadsheet tab.”
Both tabs are tagged; the second column is the split:

- `r` or `s` → `regular.csv` (278 words)
- `d` → `dual.csv` (100 words)
- `union` = regular then dual (378; the two lists are disjoint)

Rebuild from the tagged source snapshots:

```bash
python scripts/rebuild_wordpools.py
```

## Comparable boards (OOV)

Word2Vec and fastText do not contain every card (exact string match). Do **not**
delete OOV from the CSVs. For games that should be comparable across models,
pass `--intersect-with` so seed `k` samples the same 25 cards from words in
**both** tables. Logged label:
`{wordpool}_in_vocab_intersection_fasttext_word2vec`.

Playable intersection sizes: regular **260**, dual **100**, union **360**.

Concat (`--concat` and `--concat-guesser`) uses that same intersection
(see **Concatenation** below).

Per-model in-vocab (no `--intersect-with`) is a different condition.

## Repository structure

- `data/wordpools/` — tagged sources plus derived `regular.csv` / `dual.csv`
- `scripts/rebuild_wordpools.py` — rebuild regular/dual from `r`/`s` vs `d`
- `codenames/board.py` — seedable 25-card board
- `codenames/game.py` — single-team game loop
- `codenames/validity.py` — clue rule set **v2** (see below)
- `codenames/embeddings.py` — load Word2Vec / fastText `.vec` + cosine + concat
- `codenames/embedding_codemaster.py` — safe embedding clue search
- `codenames/embedding_guesser.py` — rank remaining cards by cosine to the clue
- `scripts/print_board.py` — inspect a board in the terminal
- `scripts/run_dummy_game.py` — play one single-team dummy game (engine check)
- `scripts/check_embedding_coverage.py` — Codenames wordpool vs embedding vocab
- `scripts/run_embedding_game.py` — embedding agents
- `notebooks/inspect_board.ipynb` — colored 5×5 viewer
- `notebooks/inspect_embedding_game.ipynb` — read embedding game JSON; recaps by type
- `notebooks/inspect_official_experiments.ipynb` — official series plots (wins/losses, mean turns among wins)
- `notebooks/shirs_boards_inspection_official_experiments.ipynb` — same plots on Shir's fixed boards
- `scripts/run_official_starter.sh` — seeds 0–4 × 3 board types × 6 methods at 0.4
- `scripts/run_official_to_30.sh` — retry unplayable + seeds 5–29 (30 boards total)
- `scripts/run_concat_guesser.sh` — three concat-guesser methods × seeds 0–29
- `scripts/run_shir_official.sh` — six methods on Shir's 90 boards (`shir_v1` OOV)
- `scripts/run_shir_concat_guesser.sh` — concat-guesser add-on on Shir's boards
- `data/boards/` — Shir's JSON snapshot
- `scripts/summarize_embedding_games.py` — same recaps from the command line
- `tests/` — board, game, validity, and embedding checks
- `results/embedding/` — new embedding JSON logs (gitignored transcripts)
- `EMBEDDING_NOTES.md` — lab notes (coverage, planned runs)
- `data/embeddings/README.md` — where to put pretrained files

## Clue validity v2

Logged on every game as `validity_version`. A clue is legal if and only if:

1. After stripping ends, it is a **single token** (no whitespace).
2. The clue **number** is an integer ≥ 0 (this is the count, not “the word cannot be a numeral”).
3. It is **not exactly** a remaining board word.
4. It does **not contain**, and is **not contained in**, any remaining board word.

Examples: `חתולים` is illegal if `חתול` is still on the board; `כדור` is illegal if `כדור-עף` is still on the board.

v2 does **not** require Hebrew, and does **not** ban digits, English, or proper names. The embedding codemaster additionally keeps tokens that contain at least one letter `א`–`ת`. Changing the legal-clue rules would be a new version, not a silent edit of v2.

## Embedding clue scores (`min_target`, `max_bad`, `threshold`)

These are **cosine similarities** between the clue and board words (about −1 to 1; higher = more similar). They are logged on embedding turns (`notebooks/inspect_embedding_game.ipynb`).

- **`min_target`**: among the red words the codemaster *intends*, the **weakest** similarity to the clue. If five targets are close and one is only 0.21, `min_target` is 0.21.
- **`max_bad`**: among remaining **non-targets** (blue, civilian, assassin), the **strongest** similarity to the clue. That is the most dangerous distractor.
- **`threshold`**: minimum allowed `min_target` (default **0.4**, set with `--threshold`).

A candidate clue is used only if both hold:

```text
min_target > max_bad          # every intended red beats every bad card
min_target >= threshold       # even the weakest intended red is “related enough”
```

**0.4** is the locked shared default. Same-model grid on intersection `regular`,
seeds 0–4, `candidate_limit=20000` (2026-08-28). Twins still win at 0.2, so
turns and playability matter more than win rate. Full per-seed logs:
`EMBEDDING_NOTES.md` and `notebooks/inspect_embedding_game.ipynb`.

| Model    | Threshold | Playable / 5 | Mean turns (playable) | Notes |
| -------- | --------- | ------------ | --------------------- | ----- |
| word2vec | 0.2       | 5            | 2.2                   | Large groups (often 5–7) |
| fasttext | 0.2       | 5            | 2.6                   | Large groups (often 4–6) |
| word2vec | **0.4**   | **5**        | **3.6**               | Multi-word clues, always playable |
| fasttext | **0.4**   | **5**        | **8.0**               | Mostly 1s; always playable |
| word2vec | 0.6       | 3            | 8.7                   | Seeds 0–1: no safe clue |
| fasttext | 0.6       | 0            | —                     | No safe clue on any seed |

**Why 0.4:** 0.6 cannot start many games (not a Stephenson 25 — the search
raises). 0.2 is faster but glues large, weak groups; same-model win rate
overstates how well that would work on `--cross`. 0.4 is the only value that
was always playable on that **regular** grid for **both** tables. The official
starter later had two unplayable games (fastText CM, union seed 3). One shared
threshold; do not give each model a different default. Override with
`--threshold` only for a new labeled condition.

Official series (2026-08-28): seeds **0–29**, **534/540** playable games
(six fastText-CM boards had no safe clue). Tables:
`EMBEDDING_NOTES.md`. Plots: `notebooks/inspect_official_experiments.ipynb`.

## Concatenation

Inspired by Kim, Ruzmaykin, Truong & Summerville (2019), *Cooperation and
Codenames*. That paper is **not** a recipe we copy. This section records what
they wrote, what they left unspecified, and the choices locked here.

### What Kim et al. actually do

Their codemaster and guesser are the same for every vector method. Similarity
is cosine (they write it as cosine **distance** `1 - cos`, so smaller is
closer). Concatenation is not a second search and not a vote. It is a
**longer vector** for the same word: Word2Vec’s numbers followed by GloVe’s
(e.g. 300 + 300 = 600). The bot then measures **one** cosine in that combined
space.

They motivate this with Rücklé et al. (2018): concatenating Word2Vec and GloVe
can help on other NLP tasks, “so we too consider them.” They do **not** give a
formula, do **not** say to L2-normalize each table first, and do **not** define
a special vocabulary or candidate list for concat.

In their tournament, concat is used as **codemaster and as guesser**, including
twins (concat–concat) and mixed pairs (concat CM with a GloVe guesser, and so
on). Twins win 100% of the time, as expected when both sides share a space.
Concat Word2Vec + 300-d GloVe was their strongest vectorial **codemaster**
against other vectorial guessers (≥ 90% win rate). High-dimensional concat
codemasters won more games; low-dimensional concat codemasters were faster
when they won. Higher-dimensional concat **guessers** were both more accurate
and faster.

Their tables were English Google-News Word2Vec (300-d) and GloVe at 50 / 100 /
200 / 300-d. Cosine already L2-normalizes the **full** concatenated vector. If
one block is much longer than the other, that block can dominate the angle
unless each table is normalized on its own first. Kim mostly joined 300-d with
300-d, so that imbalance is smaller than in this project.

### What this project does, and why

This is a Hebrew analogue, not a reproduction. Tables here are NLPL Word2Vec
**100-d** and Wikipedia fastText **300-d** (no standard Hebrew GloVe). Dimension
is a property of those files, not a knob on `--concat`.

**Vector.** For a word in both vocabs:

```text
concat(w) = [ L2(word2vec(w))  |  L2(fastText(w)) ]     # 100 + 300 = 400
```

Layout is always Word2Vec then fastText, independent of CLI order. Vocabulary
is the exact-string intersection (same list as matched boards). Candidate clues
are the first 20,000 intersection keys in Word2Vec dump order. Cosine is then
the usual clue-search / guesser ranking on that 400-d vector.

**Why L2 each table first (not in Kim).** Without it, the 300-d fastText block
would dominate the concatenated cosine, and “concat” would mostly be fastText
with a 100-d appendix. After per-table L2, cosine in concat space is the
**average** of the two tables’ unit cosines, so both methods get equal weight.
That is a methodological lock for this repo, logged as
`concat_normalize_each`. Raw concat (no per-table L2) would be a different
condition.

**Concat as codemaster (original six).** Kim’s round-robin includes concat
guessers. The first locked official set was same-model twins plus mixed, with
concat as **codemaster only**:

- Word2Vec CM → Word2Vec guesser
- fastText CM → fastText guesser
- Word2Vec CM → fastText guesser
- fastText CM → Word2Vec guesser
- concat CM → fastText guesser
- concat CM → Word2Vec guesser

`--concat` therefore plays `concat->word2vec` and `concat->fasttext` on
intersection boards. The codemaster still restricts clues to tokens the
guesser table can look up.

**Concat as guesser (added condition).** A later condition adds the three
codemasters against a concatenated guesser, on the **same** intersection
boards and locked threshold:

- Word2Vec CM → concat guesser (`word2vec->concat`)
- fastText CM → concat guesser (`fasttext->concat`)
- concat CM → concat guesser (`concat->concat`)

`--concat-guesser` plays those three. It does not replay the original six.
Clues from a single-table codemaster are still restricted to concat vocab
(the intersection), so the concat guesser can look them up. `concat->concat`
logs that arrow name even though both sides are named `concat`.

**What concat is not.** It is not a dimension sweep, not a vote between two
clues, and not a third pretrained file to download. It is built at run time
from the two tables already on disk.

```bash
PYTHONPATH=. python scripts/run_embedding_game.py \
  --model data/model.bin \
  --intersect-with data/embeddings/wiki.he.vec \
  --concat --wordpool regular --seed 0
PYTHONPATH=. python scripts/run_embedding_game.py \
  --model data/model.bin \
  --intersect-with data/embeddings/wiki.he.vec \
  --concat-guesser --wordpool regular --seed 0
```

Logs: `model=concat->word2vec` / `concat->fasttext` for `--concat`, and
`word2vec->concat` / `fasttext->concat` / `concat->concat` for
`--concat-guesser`, plus `concat_parts`, `concat_dims`, and
`concat_normalize_each` in `model_params`.

## Commands

```bash
PYTHONPATH=. python scripts/print_board.py --seed 0
PYTHONPATH=. python scripts/run_dummy_game.py --seed 0
PYTHONPATH=. python scripts/rebuild_wordpools.py
PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --no-probes
PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --play-both --wordpool regular --seed 0
PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --cross --wordpool dual --seeds 0,1,2,3,4,5
PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --concat --wordpool regular --seed 0
PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --concat-guesser --wordpool regular --seed 0
caffeinate -dims bash scripts/run_official_starter.sh
caffeinate -dims bash scripts/run_official_to_30.sh
caffeinate -dims bash scripts/run_concat_guesser.sh
caffeinate -dims bash scripts/run_shir_official.sh
caffeinate -dims bash scripts/run_shir_concat_guesser.sh
PYTHONPATH=. python scripts/summarize_embedding_games.py --threshold 0.4
PYTHONPATH=. python -m unittest discover -s tests -v
```
