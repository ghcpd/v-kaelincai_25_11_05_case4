# Windows PowerShell run-all script
# Set up venvs and install dependencies
cd Project_A_Flaky
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd Project_B_Deterministic
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# Run tests
cd Project_A_Flaky; .\run_tests.ps1; cd ..
cd Project_B_Deterministic; .\run_tests.ps1; cd ..

# Aggregate and generate reports
python .\scripts\aggregate_metrics.py
python - <<'PY'
import json, os
rpre = 'results/results_pre.json'
rpost = 'results/results_post.json'
pre = json.load(open(rpre)) if os.path.exists(rpre) else []
post = json.load(open(rpost)) if os.path.exists(rpost) else []

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
