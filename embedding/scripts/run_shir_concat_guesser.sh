#!/usr/bin/env bash
# Concat-guesser add-on on Shir's 90 fixed boards. Logs: results/embedding/shir/
# Does not replay the original six. Usage: caffeinate -dims bash scripts/run_shir_concat_guesser.sh
set -u
cd "$(dirname "$0")/.."
export PYTHONPATH=.
export PYTHONUNBUFFERED=1
python scripts/run_shir_boards.py --concat-guesser --quiet
echo "==== shir concat guesser series finished ===="
