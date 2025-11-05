import json
from pathlib import Path
root = Path(__file__).parent
pre = root / 'results' / 'results_pre.json'
post = root / 'results' / 'results_post.json'

def summarize(path, outfile):
    if not path.exists():
        return {}
    r = json.load(open(path))
    out = {}
    for k, v in r.items():
        t = v.get('timings', [])
        out[k] = {'avg_latency': sum(t)/len(t) if t else None, 'runs': len(t)}
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=2)
    return out

summarize(pre, root / 'Project_A_Flaky' / 'performance' / 'time_pre_flaky.json')
summarize(post, root / 'Project_B_Deterministic' / 'performance' / 'time_post_deterministic.json')
print('wrote performance files')
