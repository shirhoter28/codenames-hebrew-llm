## Research question

How well can pretrained Hebrew word embeddings play single-team Codenames:
produce a legal clue and number, and recover the intended red cards, while
avoiding blue, civilian, and assassin words?

This branch (`clean_embedding`) is **embedding-only**. LLM Codemaster work
lives on `main` / `embeddings_method`. Do not reintroduce LLM clients here.

## Why Hebrew?

Hebrew introduces several phenomena that may affect embedding neighborhoods:

- lexical ambiguity in unvocalized Hebrew
- morphology and inflection
- shared roots
- spelling variation
- Israeli/Jewish cultural associations
- translation-sensitive meanings
- broad semantic associations that may create dangerous distractors

Dual-meaning word lists (`dual.csv`, tag `d`) vs standard cards
(`regular.csv`, tags `r`/`s`) are a later board-type condition, not the
default yet. Comparable embedding games use the in-vocab **intersection**.

## Experimental philosophy

Games are **complete single-team games** (play until all 9 reds are found or
the assassin is hit). Target selection is part of the embedding Codemaster’s
search, so different models may choose different target sets from the same
board. Log that choice.

Inspired by Kim et al. (2019); this is not a full paper reproduction.

## Current board structure

A normal board contains:

- 9 red words
- 8 blue words
- 7 civilians
- 1 assassin

Same seed + same wordpool (and the same filtered pool contents/order) ⇒
identical board. Embedding games sample an in-vocab subset and log a distinct
wordpool label; they do not edit the CSV files.

## Current work

Pipeline is in place (boards, validity v2, embedding agents, concat
codemaster/guesser, logging under `results/embedding/`). Hyperparameter checks
locked **threshold 0.4**. Official series: 30 seeds × 3 board types × 9
methods (`scripts/run_official_starter.sh` then
`scripts/run_official_to_30.sh`, then `scripts/run_concat_guesser.sh` for
the three concat-guesser methods); plots in
`notebooks/inspect_official_experiments.ipynb`. Shir's fixed boards are a
separate condition (`scripts/run_shir_official.sh` then
`scripts/run_shir_concat_guesser.sh`,
`notebooks/shirs_boards_inspection_official_experiments.ipynb`).

Do not redesign the experiment without explicitly discussing the
methodological consequences first.
