import json, os, math

rpre = 'results/results_pre.json'
rpost = 'results/results_post.json'
pre = json.load(open(rpre)) if os.path.exists(rpre) else []
post = json.load(open(rpost)) if os.path.exists(rpost) else []

metrics = {'cases': []}
for p in pre:
    pid = p['case_id']
    post_match = next((x for x in post if x['case_id'] == pid), None)
    metrics['cases'].append({
        'case_id': pid,
        'pre_unique': p.get('unique_outputs', 0),
        'post_unique': post_match.get('unique_outputs', 0) if post_match else None,
        'pre_var': p.get('score_var', 0),
        'post_var': post_match.get('score_var', 0) if post_match else None,
        'pre_flaky': p.get('flakiness_rate', 0),
        'post_flaky': post_match.get('flakiness_rate', 0) if post_match else None
    })
open('results/aggregated_metrics.json', 'w').write(json.dumps(metrics, indent=2))
print('Wrote results/aggregated_metrics.json')
