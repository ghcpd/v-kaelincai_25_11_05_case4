#!/bin/bash
set -e
# create venv
python -m venv .venv
source .venv/bin/activate
python -m pip install -r Project_A_Flaky/requirements.txt
python -m pip install -r Project_B_Deterministic/requirements.txt

# run pre-fix
export REPEAT_RUNS=30
pushd Project_A_Flaky
pytest -q
popd

# run post-fix
export REPEAT_RUNS=30
pushd Project_B_Deterministic
pytest -q
popd

python compare_results.py
python generate_performance_artifacts.py
echo "Results: results/results_pre.json and results/results_post.json"
echo "Report: compare_report.md"
