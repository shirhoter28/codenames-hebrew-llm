# Embedding experiment plan (`clean_embedding`)

Embedding-only branch. LLM Codemaster work stays on `main` / `embeddings_method`.

1. Same-model hyperparameter checks (threshold; dimension only via a **new**
   pretrained file or an explicit reduction method — the current tables are
   100-d Word2Vec and 300-d wiki fastText). Locked: **threshold 0.4**,
   `candidate_limit=20000`.
2. Three board types: `regular` (tags `r`/`s`, no dual), `dual` (tag `d`),
   `union` (mix). Use in-vocab intersection so seed `k` matches across methods.
3. Nine methods on those boards. The first six were the original locked set
   (concat **codemaster-only**). The last three are an added concat-guesser
   condition (same boards, same threshold; do not replay the first six):
   - Word2Vec CM → Word2Vec guesser
   - fastText CM → fastText guesser
   - Word2Vec CM → fastText guesser
   - fastText CM → Word2Vec guesser
   - concatenated CM → fastText guesser
   - concatenated CM → Word2Vec guesser
   - Word2Vec CM → concatenated guesser
   - fastText CM → concatenated guesser
   - concatenated CM → concatenated guesser

   Official series: seeds **0–29** (30 boards). CLI: `scripts/run_official_starter.sh`
   (0–4) then `scripts/run_official_to_30.sh` (retry unplayable + 5–29), then
   `scripts/run_concat_guesser.sh` for the three concat-guesser methods. Plots:
   `notebooks/inspect_official_experiments.ipynb` (win/loss counts and mean
   turns among wins; no Stephenson in the figures).
4. Shir's fixed boards are a **separate** condition (`shir_v1` OOV policy,
   logs under `results/embedding/shir/`, notebook
   `notebooks/shirs_boards_inspection_official_experiments.ipynb`). Same nine
   methods: `scripts/run_shir_official.sh` then
   `scripts/run_shir_concat_guesser.sh`.

Each game log still records outcome, turns, and Stephenson score (turns if
win, else 25) for completeness; the official figures do not use Stephenson.
