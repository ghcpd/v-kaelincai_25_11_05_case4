#!/bin/bash
python3 -m venv .venv || true
source .venv/bin/activate || true
python3 -m pip install -r requirements.txt
mkdir -p logs performance
echo 'setup complete for Project B'