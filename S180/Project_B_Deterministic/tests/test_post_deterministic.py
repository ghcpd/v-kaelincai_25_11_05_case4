import asyncio
import json
import random
import statistics
import time
from src.grading_service import DeterministicGrader

async def run_case(case, repeats=30, seed=0):
    random.seed(seed)
    grader = DeterministicGrader(case['config'])
    outputs=[]
    timings=[]
    for i in range(repeats):
        start = time.time()
        out = await grader.grade_submission(case['submission'])
        duration = time.time() - start
        outputs.append(out['score'])
        timings.append(duration)
    return outputs, timings

async def main():
    cases = json.load(open('../Project_A_Flaky/data/test_data.json'))
    results={}
    for case in cases:
        outs, timings = await run_case(case, repeats=30, seed=42)
        results[case['name']]={'scores':outs,'mean':statistics.mean(outs),'variance':statistics.variance(outs) if len(outs)>1 else 0,'avg_latency':sum(timings)/len(timings)}
        print(case['name'], results[case['name']])
    with open('logs/results_post.json','w') as f:
        json.dump(results,f,indent=2)
    with open('performance/time_post_deterministic.txt','w') as f:
        json.dump({k:v['avg_latency'] for k,v in results.items()}, f, indent=2)

if __name__=='__main__':
    import os
    os.makedirs('logs', exist_ok=True)
    asyncio.run(main())
