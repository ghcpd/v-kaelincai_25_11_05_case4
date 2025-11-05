#!/bin/bash
set -e
echo "Run Project A tests"
pushd Project_A_Flaky
./run_tests.sh || true
popd

echo "Run Project B tests"
pushd Project_B_Deterministic
./run_tests.sh || true
popd

echo "Collecting results and producing report"
python3 produce_compare.py
echo "Done"
