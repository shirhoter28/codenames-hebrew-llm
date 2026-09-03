#!/usr/bin/env bash
# Starter official series: 5 seeds × 3 board types × 6 methods, threshold 0.4.
# Skips regular same-model twins (already logged). Continue after a failed clue.
set -u
cd "$(dirname "$0")/.."
export PYTHONPATH=.
export PYTHONUNBUFFERED=1

run() {
  echo "==== $* ===="
  python scripts/run_embedding_game.py \
    --model data/model.bin \
    --intersect-with data/embeddings/wiki.he.vec \
    --threshold 0.4 \
    --seeds 0,1,2,3,4 \
    --quiet \
    "$@"
}

run --wordpool regular --cross
run --wordpool regular --concat
for pool in dual union; do
  run --wordpool "$pool" --play-both
  run --wordpool "$pool" --cross
  run --wordpool "$pool" --concat
done
echo "==== official starter commands finished ===="
