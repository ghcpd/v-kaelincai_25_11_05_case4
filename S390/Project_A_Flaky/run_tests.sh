#!/usr/bin/env bash
set -e
export PORT_GRADER=8001
export PORT_SCORER=9001
export REPEAT=30
pytest -q tests/test_pre_flaky.py -s | tee ../logs/log_pre_flaky.txt

# Output will be written to results/results_pre.json
