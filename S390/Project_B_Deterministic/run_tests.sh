#!/usr/bin/env bash
set -e
export PORT_GRADER=8002
export PORT_SCORER=9001
export REPEAT=30
pytest -q tests/test_post_deterministic.py -s | tee ../logs/log_post_deterministic.txt

# Output will be written to results/results_post.json
