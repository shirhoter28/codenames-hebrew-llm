# Embedding experiment notes

Lab notes for branch `clean_embedding`. Fill this in as runs happen.
Do not copy old pilot tables here.

Transcripts: `results/embedding/` (gitignored JSON / JSONL).
Do not commit `data/model.bin` or `data/embeddings/wiki.he.vec`.

---

## Setup (code as of this document)

Single-team Hebrew Codenames: 9 red / 8 blue / 7 civilian / 1 assassin.

- **Codemaster** searches for a clue in an embedding table (cosine similarity).
- **Guesser** picks remaining board words by cosine to that clue, up to the clue number (no extra guess).
- Clue legality is **v2**: one token, number ≥ 0, not a remaining board word, no substring overlap with remaining board words. Candidates also need at least one Hebrew letter `א`–`ת`.
- A clue is **safe** if `min_target > max_bad` and `min_target >= threshold`.
- Candidate list: first 20,000 keys of the codemaster table (frequency-sorted dump).
- Out-of-vocabulary board words are not skipped. For **comparable** games
across Word2Vec and fastText, sample the **intersection** in-vocab list
(`--intersect-with`) so the same seed is the same 25 cards. Per-model
in-vocab subsets are a different condition. The CSVs are not edited.
- Default `threshold` in code is `0.4` (`--threshold` to override).
- **Concat** (`--concat`): codemaster uses `[L2(word2vec) | L2(fasttext)]`
  (400-d, equal weight). Guesser is still one table (`concat->word2vec` and
  `concat->fasttext`). Same intersection boards.
- **Concat guesser** (`--concat-guesser`): added condition on the same boards.
  Three more methods: `word2vec->concat`, `fasttext->concat`, `concat->concat`.
- Logs include seed, board, roles, model / `model_params`, clue, intended targets, `min_target`, `max_bad`, outcome, turns, Stephenson score (turns if win, else 25).

Wordpools: `regular`, `dual`, `union` (see `data/wordpools/README.md`).

Embedding files: `data/embeddings/README.md`.

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/model.bin
PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --seed 0
```

Inspect a log: `notebooks/inspect_embedding_game.ipynb`.

---



## Coverage (2026-08-27, after `r`/`s` vs `d` split)

Wordpools rebuilt from both spreadsheet tabs: `r`/`s` → regular (n=278),
`d` → dual (n=100), union n=378 (disjoint). Exact string match. CSVs not
edited for OOV.

Comparable games use **intersection** (same seed ⇒ same 25 cards):

```bash
PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --no-probes
PYTHONPATH=. python scripts/check_embedding_coverage.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --wordpool dual --no-probes
PYTHONPATH=. python scripts/run_embedding_game.py --model data/model.bin --intersect-with data/embeddings/wiki.he.vec --play-both --seed 0
```


| Model        | Wordpool | n   | In-vocab | OOV | Coverage |
| ------------ | -------- | --- | -------- | --- | -------- |
| Word2Vec     | regular  | 278 | 261      | 17  | 93.9%    |
| Word2Vec     | dual     | 100 | 100      | 0   | 100%     |
| Word2Vec     | union    | 378 | 361      | 17  | 95.5%    |
| fastText     | regular  | 278 | 266      | 12  | 95.7%    |
| fastText     | dual     | 100 | 100      | 0   | 100%     |
| fastText     | union    | 378 | 366      | 12  | 96.8%    |
| intersection | regular  | 278 | 260      | 18  | 93.5%    |
| intersection | dual     | 100 | 100      | 0   | 100%     |
| intersection | union    | 378 | 360      | 18  | 95.2%    |


**regular / union dropped from intersection (18):** hyphenated compounds,
Word2Vec-only misses (`מנוף`, `אפיקומן`, `לוויין`, `עכביש`, `קנגורו`, `אגודל`),
`נינג'ה` (fastText), and `תל-אביב` (both). Dual has no OOV in either table.

Playable sizes for matched boards: regular **260**, dual **100**, union **360**.

---



## Planned work

1. Same-model games; choose hyperparameters (threshold first). Vector **dimension** is a property of the pretrained file, not a free knob on the current 100-d Word2Vec / 300-d wiki fastText tables.
2. Three board types: `regular` (`r`/`s` tags), `dual` (`d` tags), `union`
  (mix). Sample each from the Word2Vec ∩ fastText in-vocab intersection so
   seed `k` is the same 25 cards across methods.
3. Four methods: W2V→FT, FT→W2V, concat→FT, concat→W2V. Concat is implemented (`--concat`); guesser stays a single table.

---



## Runs

Record for each batch: date, command, wordpool, models, threshold, seeds, and a short table (seed, outcome, turns, wrong guesses, assassin).

### 2026-08-27 / 2026-08-28 — same-model, seeds 0–4, threshold 0.4

```bash
PYTHONPATH=. python scripts/run_embedding_game.py \
  --model data/model.bin \
  --intersect-with data/embeddings/wiki.he.vec \
  --play-both --wordpool regular --seed 0 --threshold 0.4
PYTHONPATH=. python scripts/run_embedding_game.py \
  --model data/model.bin \
  --intersect-with data/embeddings/wiki.he.vec \
  --play-both --wordpool regular --seeds 1,2,3,4 --threshold 0.4
```

Intersection `regular` (260). Same 25 cards per seed for both models. `candidate_limit=20000`.
Recaps: `notebooks/inspect_embedding_game.ipynb` (last section) or
`PYTHONPATH=. python scripts/summarize_embedding_games.py --threshold 0.4`.

| Model    | Seed | Outcome | Turns | Wrong | Assassin | Clue numbers          |
| -------- | ---- | ------- | ----- | ----- | -------- | --------------------- |
| word2vec | 0    | win     | 3     | 0     | no       | 4, 3, 2               |
| word2vec | 1    | win     | 4     | 0     | no       | 4, 2, 2, 1            |
| word2vec | 2    | win     | 3     | 0     | no       | 4, 3, 2               |
| word2vec | 3    | win     | 4     | 0     | no       | 4, 2, 2, 1            |
| word2vec | 4    | win     | 4     | 0     | no       | 3, 3, 2, 1            |
| fasttext | 0    | win     | 8     | 0     | no       | 2, 1, 1, 1, 1, 1, 1, 1 |
| fasttext | 1    | win     | 8     | 0     | no       | 2, 1, 1, 1, 1, 1, 1, 1 |
| fasttext | 2    | win     | 8     | 0     | no       | 2, 1, 1, 1, 1, 1, 1, 1 |
| fasttext | 3    | win     | 9     | 0     | no       | 1×9                   |
| fasttext | 4    | win     | 7     | 0     | no       | 2, 2, 1, 1, 1, 1, 1   |

All 10 games won; no wrong guesses; no assassin. Word2Vec mean turns **3.6**; fastText mean **8.0**. Clue text is in the notebook recaps. The 0.2 / 0.6 comparison (next subsection) is why **0.4** is locked.

### 2026-08-28 — same-model threshold grid 0.2 / 0.6 (seeds 0–4)

Same intersection `regular` boards as the 0.4 batch. `candidate_limit=20000`.

```bash
PYTHONPATH=. python scripts/run_embedding_game.py \
  --model data/model.bin --intersect-with data/embeddings/wiki.he.vec \
  --play-both --wordpool regular --seeds 0,1,2,3,4 --threshold 0.2
```

**0.2** — 10/10 finished, all wins, 0 wrong, 0 assassin.

| Model    | Mean turns | Clue sizes (typical) |
| -------- | ---------- | -------------------- |
| word2vec | **2.2**    | 5–7 then remainder   |
| fasttext | **2.6**    | 4–6 then remainder   |

**0.6** — often **no safe clue** (runner raises; no JSON, not a Stephenson 25). FastText: **0/5** playable. Word2Vec: **3/5** playable (seeds 2, 3, 4 only; means **8.7** turns, mostly 1s). Unplayable: W2V seeds 0–1; FT seeds 0–4.

**Choice for a shared official threshold:** drop **0.6** (cannot even start many games). **0.2** is faster but uses huge groups (same-model twins still win). **0.4** is the compromise: always playable here, Word2Vec still multi-word, fastText conservative. Lock **0.4** unless you explicitly want the aggressive 0.2 clues. Confirm later on `--cross` (twins inflate win rate).

### 2026-08-28 — official starter (seeds 0–4)

5 seeds × 3 board types × 6 methods, threshold **0.4**, intersection,
`candidate_limit=20000`. Command: `caffeinate -dims bash scripts/run_official_starter.sh`.
Plots: `notebooks/inspect_official_experiments.ipynb` (no Stephenson).

**88 / 90** games logged. Two skips (no JSON, not a Stephenson 25): **union
seed 3**, fastText codemaster (`fasttext` and `fasttext->word2vec`). Same board
was playable for Word2Vec CM and concat CM. All 10 losses among the 88 were
assassin hits (no other loss type).

Wins out of games logged, and mean turns **among wins**:

| Method     | regular     | dual        | union       |
| ---------- | ----------- | ----------- | ----------- |
| W2V→W2V    | 5/5, 3.60   | 5/5, 4.00   | 5/5, 3.20   |
| FT→FT      | 5/5, 8.00   | 5/5, 7.40   | 4/4, 7.75   |
| W2V→FT     | 3/5, 7.33   | 3/5, 8.00   | 4/5, 7.00   |
| FT→W2V     | 3/5, 8.33   | 4/5, 10.50  | 4/4, 9.25   |
| concat→FT  | 4/5, 6.50   | 5/5, 5.80   | 5/5, 6.40   |
| concat→W2V | 5/5, 6.00   | 4/5, 6.25   | 5/5, 6.20   |

Mean clue number on wins (larger = bigger groups): W2V twins ~2.3–2.9; concat
~1.5–1.7; fastText-as-CM ~1.1–1.2; W2V→FT ~1.9–2.7. Mixed methods lose more
to the assassin than twins or concat. This is a 5-board starter, not a
significance test.

### 2026-08-28 — official series, seeds 0–29

Same locked settings (threshold 0.4, intersection, six methods, three board
types). Command: `caffeinate -dims bash scripts/run_official_to_30.sh`.
Plots: `notebooks/inspect_official_experiments.ipynb`.

**534 / 540** games logged. Six skips (no JSON, not a Stephenson 25), all
fastText CM: regular seed 8 (`FT→FT`, `FT→W2V`); union seeds 3 and 29 (same
two methods). Dual was fully playable. All 45 losses among the 534 were
assassin hits.

Wins out of games logged, and mean turns **among wins**:

| Method     | regular      | dual         | union        |
| ---------- | ------------ | ------------ | ------------ |
| W2V→W2V    | 30/30, 3.37  | 30/30, 3.67  | 30/30, 3.40  |
| FT→FT      | 29/29, 7.93  | 30/30, 8.00  | 28/28, 8.00  |
| W2V→FT     | 23/30, 6.65  | 18/30, 6.50  | 23/30, 6.57  |
| FT→W2V     | 24/29, 9.33  | 24/30, 9.42  | 24/28, 8.96  |
| concat→FT  | 28/30, 6.21  | 29/30, 6.55  | 30/30, 6.27  |
| concat→W2V | 30/30, 6.07  | 29/30, 6.52  | 30/30, 6.23  |

Same-model Word2Vec still wins every playable board and is fastest. FastText
twins also win every playable board but take ~8 turns. Mixed methods take more
assassin hits (especially W2V→FT on dual). Concat stays between twins and
mixed on both win rate and turns.

### 2026-08-29 — Shir's fixed boards (`shir_v1`)

Separate from the official series. Her 90 boards (`data/boards/shirs_boards.json`:
30 × `dual_0` / `natural` / `dual_100`) are played as-is. OOV = missing from
Word2Vec or fastText (intersection). Logs: `results/embedding/shir/`.

- Red OOV → `oov_loss` (not played).
- Assassin OOV, no red OOV → play; **unfair** (assassin skipped in cosine, cannot be guessed).
- Blue or civilian OOV → play; those cards skipped in cosine; logged.

```bash
caffeinate -dims bash scripts/run_shir_official.sh
```

Notebook: `notebooks/shirs_boards_inspection_official_experiments.ipynb`.

**540 / 540** logged. Outcomes: 311 fair wins, 18 unfair assassin-OOV wins,
180 `oov_loss` (red OOV), 25 assassin hits, 6 `no_safe_clue`.

### 2026-08-31 — concat guesser add-on

Same boards, same locked 0.4 / `candidate_limit=20000`. Three more methods
per board: `word2vec->concat`, `fasttext->concat`, `concat->concat`. Does not
replay the original six.

```bash
caffeinate -dims bash scripts/run_concat_guesser.sh
caffeinate -dims bash scripts/run_shir_concat_guesser.sh
```

Official expected becomes **810** (9 × 3 × 30). Shir expected **810**
(9 × 90). Notebooks: `inspect_official_experiments.ipynb` and
`shirs_boards_inspection_official_experiments.ipynb`.