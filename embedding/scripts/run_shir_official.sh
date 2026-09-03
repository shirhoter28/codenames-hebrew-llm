#!/usr/bin/env bash
# Six official methods on Shir's 90 fixed boards. Logs: results/embedding/shir/
set -u
cd "$(dirname "$0")/.."
export PYTHONPATH=.
export PYTHONUNBUFFERED=1
python scripts/run_shir_boards.py --play-both --cross --concat --quiet
echo "==== shir boards series finished ===="
