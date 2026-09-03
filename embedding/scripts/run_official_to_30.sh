#!/usr/bin/env bash
# Retry the two unplayable union-seed-3 fastText-CM games, then seeds 5–29.
# Does not replay seeds 0–4. Same threshold 0.4 and intersection boards.
# Usage: caffeinate -dims bash scripts/run_official_to_30.sh
set -u
cd "$(dirname "$0")/.."
export PYTHONPATH=.
export PYTHONUNBUFFERED=1

SEEDS_MORE=$(python -c 'print(",".join(str(i) for i in range(5, 30)))')

run() {
  echo "==== $* ===="
  python scripts/run_embedding_game.py \
    --model data/model.bin \
    --intersect-with data/embeddings/wiki.he.vec \
    --threshold 0.4 \
    --quiet \
    "$@"
}

echo "==== retry union seed=3 fastText twins ===="
python scripts/run_embedding_game.py \
  --model data/embeddings/wiki.he.vec \
  --intersect-with data/model.bin \
  --threshold 0.4 --quiet --wordpool union --seed 3

echo "==== retry union seed=3 FT->W2V (cross also replays already-logged W2V->FT) ===="
python scripts/run_embedding_game.py \
  --model data/embeddings/wiki.he.vec \
  --intersect-with data/model.bin \
  --cross --threshold 0.4 --quiet --wordpool union --seed 3

echo "==== seeds 5-29, all board types, six methods ===="
for pool in regular dual union; do
  run --wordpool "$pool" --play-both --seeds "$SEEDS_MORE"
  run --wordpool "$pool" --cross --seeds "$SEEDS_MORE"
  run --wordpool "$pool" --concat --seeds "$SEEDS_MORE"
done
echo "==== official extend to 30 finished ===="
