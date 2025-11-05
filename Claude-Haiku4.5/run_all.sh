#!/bin/bash
# Master script to run the complete flaky behavior experiment
# Runs Project A (flaky), Project B (deterministic), and generates comparison report

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_DIR="$SCRIPT_DIR/.."

PROJECT_A_DIR="$WORKSPACE_DIR/Project_A_Flaky"
PROJECT_B_DIR="$WORKSPACE_DIR/Project_B_Deterministic"
SHARED_DIR="$WORKSPACE_DIR/shared_artifacts"
RESULTS_DIR="$SHARED_DIR/results"

echo "================================================================================"
echo "Flaky Behavior Detection & Mitigation - Complete Experiment"
echo "================================================================================"
echo ""
echo "Workspace: $WORKSPACE_DIR"
echo "Project A (Flaky): $PROJECT_A_DIR"
echo "Project B (Deterministic): $PROJECT_B_DIR"
echo "Shared artifacts: $SHARED_DIR"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Run Project A (Flaky)
echo "================================================================================"
echo "PHASE 1: Running Project A (Flaky Baseline)"
echo "================================================================================"
echo ""
cd "$PROJECT_A_DIR"
bash run_tests.sh
echo ""
echo "✓ Project A tests completed"
echo ""

# Copy results to shared
cp "$PROJECT_A_DIR/logs/results_pre.json" "$RESULTS_DIR/"
if [ -f "$PROJECT_A_DIR/logs/test_pre_flaky.txt" ]; then
    cp "$PROJECT_A_DIR/logs/test_pre_flaky.txt" "$RESULTS_DIR/"
fi

# Run Project B (Deterministic)
echo "================================================================================"
echo "PHASE 2: Running Project B (Deterministic Fix)"
echo "================================================================================"
echo ""
cd "$PROJECT_B_DIR"
bash run_tests.sh
echo ""
echo "✓ Project B tests completed"
echo ""

# Copy results to shared
cp "$PROJECT_B_DIR/logs/results_post.json" "$RESULTS_DIR/"
if [ -f "$PROJECT_B_DIR/logs/test_post_deterministic.txt" ]; then
    cp "$PROJECT_B_DIR/logs/test_post_deterministic.txt" "$RESULTS_DIR/"
fi

# Generate comparison report
echo "================================================================================"
echo "PHASE 3: Generating Comparison Report"
echo "================================================================================"
echo ""

cd "$SHARED_DIR"
python compare_results.py \
    "$RESULTS_DIR/results_pre.json" \
    "$RESULTS_DIR/results_post.json" \
    "$RESULTS_DIR/compare_report.md"

echo ""
echo "================================================================================"
echo "EXPERIMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Results saved to: $RESULTS_DIR/"
echo ""
echo "Key artifacts:"
echo "  - results_pre.json: Project A (flaky) detailed results"
echo "  - results_post.json: Project B (deterministic) detailed results"
echo "  - compare_report.md: Full comparison and analysis"
echo "  - test_pre_flaky.txt: Project A execution log"
echo "  - test_post_deterministic.txt: Project B execution log"
echo ""
echo "To view the comparison report:"
echo "  cat $RESULTS_DIR/compare_report.md"
echo ""
