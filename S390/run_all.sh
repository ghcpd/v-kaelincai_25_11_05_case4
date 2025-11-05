#!/usr/bin/env bash
set -e
# Run both projects (pre-fix flaky and post-fix deterministic)
# 1. Install requirements for both
cd Project_A_Flaky
python -m venv .venv || true
. .venv/bin/activate || true
pip install -r requirements.txt
cd ..

cd Project_B_Deterministic
python -m venv .venv || true
. .venv/bin/activate || true
pip install -r requirements.txt
cd ..

# Run pre-fix tests
cd Project_A_Flaky
bash run_tests.sh || true
cd ..
# Run post-fix tests
cd Project_B_Deterministic
bash run_tests.sh || true
cd ..

# Collect results and build a basic compare_report.md in root
python scripts/aggregate_metrics.py || true
python - <<'PY'
import json, os
rpre = 'results/results_pre.json'
rpost = 'results/results_post.json'
pre = json.load(open(rpre)) if os.path.exists(rpre) else []
post = json.load(open(rpost)) if os.path.exists(rpost) else []
# Basic metric aggregation

def agg(results):
    d = {}
    for r in results:
        d[r['case_id']] = r
    return d

apre = agg(pre)
apost = agg(post)
with open('compare_report.md', 'w') as f:
    f.write('# Comparison Report\n\n')
    f.write('## Pre-fix (flaky) vs Post-fix (deterministic)\n\n')
    f.write('| Test Case | Unique Pre | Var Pre | Unique Post | Var Post | Comments |\n')
    f.write('|---|---:|---:|---:|---:|---|\n')
    cases = set(list(apre.keys()) + list(apost.keys()))
    for c in cases:
        pre = apre.get(c, {})
        post = apost.get(c, {})
        f.write(f"| {c} | {pre.get('unique_outputs','-')} | {pre.get('score_var','-')} | {post.get('unique_outputs','-')} | {post.get('score_var','-')} | {'improved' if pre.get('unique_outputs',0) > post.get('unique_outputs',0) else ''} |\\n")
print('Generated compare_report.md')
PY

echo 'Done. Reports: compare_report.md, results/'
