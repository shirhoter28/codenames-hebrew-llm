# Provenance — this run was salvaged mid-flight

Started 2026-08-23 19:12 UTC. Stopped 2026-08-24 at 1,667/8,640 games.

`translate_pipeline` was rejecting 15.9% of codemaster calls for multi-word
clues (against 0.6% for the same method on the 08-17 run). Cause: the
2026-08-23 JSON key reorder made the method genuinely derive the Hebrew clue
from the English one, but the prompt required only the *Hebrew* clue to be a
single word — and 17.2% of `en_clue` values were English phrases. Almost all of
the damage was qwen. See DECISIONS.md 2026-08-24.

## What was done

- The 587 `translate_pipeline` games played before the fix were **removed** from
  `raw.jsonl` and preserved verbatim in `raw.pre_translate_fix.jsonl`.
- The 1,080 `strong_hebrew` games were **kept**: that prompt was not changed, so
  they are valid. They are complete and balanced for the 4 pairs played —
  360 per count arm, 360 per board style.
- The run was then resumed, replaying every `translate_pipeline` task under the
  fixed prompt (commit 95a82db).

## How to read this run

- Every `translate_pipeline` game in `raw.jsonl` is POST-fix. Every
  `strong_hebrew` game is from either side of the fix, which does not matter —
  its prompt is byte-identical across the boundary.
- `raw.pre_translate_fix.jsonl` is NOT part of the experiment. It is kept as
  evidence of the defect, and must not be pooled with `raw.jsonl`.
- `config.yaml` does not record prompt text, so nothing in this directory would
  otherwise reveal the boundary. That is why this file exists.
