import json
import os
from statistics import mean, pstdev

def load_json(path):
    if os.path.exists(path):
        return json.load(open(path))
    return {}

pre = load_json('Project_A_Flaky/results_pre.json')
post = load_json('Project_B_Deterministic/results_post.json')

metrics = {'pre':{}, 'post':{}}

def analyze_pre(pre):
    res = {}
    for tname, val in pre.items():
        outputs = val.get('outputs', [])
        # extract total scores
        scores = []
        for o in outputs:
            if isinstance(o, dict) and 'score' in o:
                scores.append(o['score'])
        unique = val.get('unique', len(set(json.dumps(o, sort_keys=True) for o in outputs)))
        res[tname] = {
            'runs': len(outputs),
            'unique_outputs': unique,
            'flaky': unique>1,
            'score_mean': mean(scores) if scores else None,
            'score_variance': (pstdev(scores)**2) if len(scores)>1 else 0,
        }
    return res

def analyze_post(post):
    res = {}
    for tname, val in post.items():
        unique = val.get('unique',1)
        sample = val.get('sample')
        res[tname] = {
            'unique_outputs': unique,
            'flaky': unique>1,
            'sample': sample,
        }
    return res

metrics['pre'] = analyze_pre(pre)
metrics['post'] = analyze_post(post)

os.makedirs('results', exist_ok=True)
open('results/aggregated_metrics.json','w').write(json.dumps(metrics, indent=2))

# simple markdown report
with open('compare_report.md','w') as f:
    f.write('# Flaky vs Deterministic Comparison Report\n\n')
    f.write('## Summary Metrics\n\n')
    f.write('Pre-fix and Post-fix metrics:\n\n')
    f.write('```json\n')
    f.write(json.dumps(metrics, indent=2))
    f.write('\n```\n')

print('Wrote results/aggregated_metrics.json and compare_report.md')
