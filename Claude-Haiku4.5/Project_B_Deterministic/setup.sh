#!/bin/bash
# Setup script for Project B (Deterministic)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo "Setting up Project B (Deterministic)..."
echo "Project directory: $PROJECT_DIR"

# Create directories
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/performance"
mkdir -p "$PROJECT_DIR/data"

# Create __init__.py files for Python packages
touch "$PROJECT_DIR/src/__init__.py"
touch "$PROJECT_DIR/mocks/__init__.py"
touch "$PROJECT_DIR/tests/__init__.py"

echo "✓ Project B setup complete"
