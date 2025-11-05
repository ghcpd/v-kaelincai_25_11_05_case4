#!/bin/bash
# Start Project A (Flaky) tests
set -e
python -m pip install -r requirements.txt
export REPEAT_RUNS=${REPEAT_RUNS:-30}
pytest -q
