import json
from pathlib import Path

root = Path(__file__).parent
rpre = root / 'results' / 'results_pre.json'
rpost = root / 'results' / 'results_post.json'

def load(path):
    if not path.exists():
        return {}
    return json.load(open(path))

pre = load(rpre)
post = load(rpost)

metrics = {}
for k in set(pre.keys()) | set(post.keys()):
    pre_m = pre.get(k, {}).get('metrics', {})
    post_m = post.get(k, {}).get('metrics', {})
    metrics[k] = { 'before': pre_m, 'after': post_m }

out = root / 'compare_report.md'
with open(out, 'w') as f:
    f.write('# Flaky Behavior Comparison Report\n\n')
    f.write('This report compares Project A (flaky) vs Project B (deterministic).\n\n')
    f.write('| Test Case | Inconsistency Count (Before) | Flakiness Rate (Before) | Score Var (Before) | Inconsistency Count (After) | Flakiness Rate (After) | Score Var (After) |\n')
    f.write('|---|---:|---:|---:|---:|---:|---:|\n')
    for k, v in metrics.items():
        pb = v['before'] or {'inconsistency_count': None, 'flakiness_rate': None, 'score_variance': None}
        pa = v['after'] or {'inconsistency_count': None, 'flakiness_rate': None, 'score_variance': None}
        f.write(f"| {k} | {pb['inconsistency_count']} | {pb['flakiness_rate']} | {pb['score_variance']} | {pa['inconsistency_count']} | {pa['flakiness_rate']} | {pa['score_variance']} |\n")

print('wrote', out)
