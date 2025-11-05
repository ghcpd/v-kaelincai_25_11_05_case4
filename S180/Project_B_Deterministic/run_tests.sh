#!/bin/bash
set -e
python3 -m pip install -r requirements.txt
python3 tests/test_post_deterministic.py
