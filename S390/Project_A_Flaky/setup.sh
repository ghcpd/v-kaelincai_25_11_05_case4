#!/usr/bin/env bash
python -m venv .venv ;
. .venv/bin/activate ;
python -m pip install --upgrade pip ;
pip install -r requirements.txt

# For Windows PowerShell users, suggest running the following instead:
# python -m venv .venv
# .\.venv\Scripts\Activate.ps1
# python -m pip install --upgrade pip
# pip install -r requirements.txt
