#!/bin/bash
set -e
# Run Project A pre-fix
(cd Project_A_Flaky && bash run_tests.sh)
# Run Project B post-fix
(cd Project_B_Deterministic && bash run_tests.sh)
# Collect results
mkdir -p results
cp Project_A_Flaky/logs/results_pre.json results/results_pre.json || true
cp Project_B_Deterministic/logs/results_post.json results/results_post.json || true
# Generate a simple comparison
python3 - <<'PY'
import json
pre=json.load(open('results/results_pre.json'))
post=json.load(open('results/results_post.json'))
report={}
summary={'pre':{'inconsistent':0,'cases':len(pre)},'post':{'inconsistent':0,'cases':len(post)}}
for k in pre:
    pre_var = pre[k]['variance']
    post_var = post.get(k,{}).get('variance',0)
    if pre_var>0: summary['pre']['inconsistent']+=1
    if post_var>0: summary['post']['inconsistent']+=1
    report[k]={'pre':pre[k],'post':post.get(k)}
open('compare_report.md','w').write('# Comparison\n\nSummary:\n'+json.dumps(summary,indent=2)+'\n\nDetails:\n'+json.dumps(report,indent=2))
print('Wrote compare_report.md')
PY
