#!/bin/bash
# Run tests for Project A (Flaky)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo "Running Project A (Flaky) Tests..."
echo "=================================="

# Setup
bash "$PROJECT_DIR/setup.sh"

# Run tests
echo ""
echo "Executing flaky tests..."
python "$PROJECT_DIR/tests/test_pre_flaky.py"

echo ""
echo "✓ Project A tests completed"
echo "Check logs in: $PROJECT_DIR/logs/"
