#!/bin/bash
# Run tests for Project B (Deterministic)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo "Running Project B (Deterministic) Tests..."
echo "=========================================="

# Setup
bash "$PROJECT_DIR/setup.sh"

# Run tests
echo ""
echo "Executing deterministic tests..."
python "$PROJECT_DIR/tests/test_post_deterministic.py"

echo ""
echo "✓ Project B tests completed"
echo "Check logs in: $PROJECT_DIR/logs/"
