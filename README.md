# Codenames in Hebrew: Benchmarking LLM Codemasters and Guessers

NLP final project — Sharon & Shir.

This repository holds the code, data, run artifacts and report for a study of
how well large language models play [Codenames](https://en.wikipedia.org/wiki/Codenames_(board_game))
**in Hebrew**. Models play both seats: the **codemaster**, who sees the key and
gives a one-word clue with a number, and the **guesser**, who sees only the
board and the clue. The design follows the English-language benchmark of
Stephenson, Sidji & Ronval, *"Codenames as a Benchmark for Large Language
Models"*, and asks what changes when the board is Hebrew.

The final report is [`paper.md`](paper.md). The reasoning behind each design
decision, including the dead ends, lives in [`DECISIONS.md`](DECISIONS.md).

## What the experiment varies

The main run is a full factorial over five factors:

| Factor | Levels |
| --- | --- |
| Codemaster model | `gemini-2.5-flash`, `llama-3.3-70b`, `gpt-4o-mini`, `qwen3.5-9b` |
| Guesser model | the same four |
| Prompt method | `strong_hebrew` (reason natively in Hebrew), `translate_pipeline` (translate to English, solve, translate back) |
| Clue-count floor | free choice, `min2`, `min3` |
| Board ambiguity | `dual_0`, `natural`, `dual_100` — share of words drawn from the hand-tagged ambiguous list |

Every model is reached through a single provider-agnostic gateway,
[OpenRouter](https://openrouter.ai), so adding or dropping a model is a config
change rather than a code change.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Model access needs an OpenRouter key. Copy the template and fill it in:

```bash
cp .env.example .env
# then edit .env and set OPENROUTER_API_KEY=...
```

`.env` is gitignored and no key is ever committed.

## Running an experiment

Every run is driven by a YAML config in [`configs/`](configs). Nothing about
the design is hardcoded, so reproducing a run means pointing the runner at that
run's config:

```bash
python scripts/run_m1_pilot.py configs/m4_full.yaml
```

This writes a self-describing directory `results/<run_id>/` containing the
resolved config, the generated boards, per-game metrics, figures and a report.
A run that is interrupted continues where it stopped, replaying only the missing
games under the design it started with:

```bash
python scripts/run_m1_pilot.py --resume results/<run_id>
```

**A full run is expensive.** `configs/m4_full.yaml` is 8,640 games across 288
cells — roughly 200,000 API calls, several days of wall clock, and real money.
Use `configs/m3_guesser_grid_smoke.yaml` or `configs/m4_count_smoke.yaml` to
check the pipeline end to end before committing to a full one.

Concurrency is capped at the number of models on purpose: games are dispatched
in Latin-square order so the games in flight use distinct codemasters *and*
distinct guessers, spreading load across providers instead of concentrating it
on one and triggering rate limits.

## Analysis and figures

Rebuild the rolled-up report and figures for one or more runs:

```bash
python scripts/report.py results/<run_id>
python scripts/paper_figures.py     # figures as they appear in the report
python scripts/show_game.py results/<run_id> --help   # replay a single game
```

`notebooks/analysis.ipynb` is for exploration only; all reusable logic lives in
the package.

## Tests

```bash
pytest
```

The suite runs offline — no API key and no network calls.

## Layout

```
src/codenames_heb/     core package — boards, OpenRouter client, prompt
                       builders (prompts/), the experiment runner, metrics,
                       analysis and plotting
configs/               one YAML per experiment; the unit of reproducibility
data/raw/              Hebrew word lists, split into regular and dual
                       (ambiguous) by hand-tagged provenance in
                       data/word_list_*_w_marks.csv
scripts/               command-line entry points: run, report, figures, replay
results/<run_id>/      per-run config, boards, metrics, figures and report
tests/                 pytest, mirroring src/codenames_heb/
docs/                  proposal, milestone specs, figures, worked examples
paper.md               the final report
DECISIONS.md           decision log with rationale
```

### A note on `results/`

Run directories are committed whole — resolved `config.yaml`, `boards.json`,
`raw.jsonl`, `metrics.csv`, figures and `report.md`. The raw per-call
transcripts are the ones that matter for reproducibility: `metrics.csv` carries
only game-level fields, so every round-level result in the report (clue
ambition, stopping behaviour, intended-vs-hit overlap) is derived from
`raw.jsonl` by `src/codenames_heb/analysis.py`. With them in the repo, a clone
can rebuild every number and figure in `paper.md` offline, without an API key
and without spending a cent.

## Reference

Stephenson, Sidji & Ronval, *"Codenames as a Benchmark for Large Language
Models"* — <https://github.com/stepmat/Codenames_GPT> (branch `ToG_2025`).
