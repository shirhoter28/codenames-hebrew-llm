#!/usr/bin/env bash
# Concat-guesser add-on: three methods × 3 board types × seeds 0–29.
# Does not replay the original six. Same threshold 0.4 and intersection boards.
# Usage: caffeinate -dims bash scripts/run_concat_guesser.sh
set -u
cd "$(dirname "$0")/.."
export PYTHONPATH=.
export PYTHONUNBUFFERED=1

SEEDS=$(python -c 'print(",".join(str(i) for i in range(30)))')

run() {
  echo "==== $* ===="
  python scripts/run_embedding_game.py \
    --model data/model.bin \
    --intersect-with data/embeddings/wiki.he.vec \
    --threshold 0.4 \
    --quiet \
    "$@"
}

echo "==== concat guesser, seeds 0-29, all board types ===="
for pool in regular dual union; do
  run --wordpool "$pool" --concat-guesser --seeds "$SEEDS"
done
echo "==== concat guesser official series finished ===="
