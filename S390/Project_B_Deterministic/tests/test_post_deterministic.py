import asyncio
import json
import os
import time
from aiohttp import ClientSession
import pytest

# Start servers as subprocesses
import subprocess
import signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
with open(os.path.join(ROOT, 'data', 'test_data.json')) as f:
    TEST_CASES = json.load(f)

PORT_GRADER = int(os.environ.get('PORT_GRADER', '8002'))
PORT_SCORER = int(os.environ.get('PORT_SCORER', '9001'))
REPEAT = int(os.environ.get('REPEAT', '30'))

async def start_servers():
    scorer_cmd = ['python', os.path.join(ROOT, 'mocks', 'scorer_mock.py'), '--port', str(PORT_SCORER)]
    grader_cmd = ['python', os.path.join(ROOT, 'src', 'grading_service.py'), '--port', str(PORT_GRADER)]
    scorer_proc = subprocess.Popen(scorer_cmd, cwd=ROOT)
    await asyncio.sleep(0.05)
    grader_proc = subprocess.Popen(grader_cmd, cwd=ROOT)
    await asyncio.sleep(0.05)
    return scorer_proc, grader_proc

async def stop_servers(scorer_proc, grader_proc):
    for p in (scorer_proc, grader_proc):
        try:
            p.send_signal(signal.SIGINT)
        except Exception:
            pass
        p.wait(timeout=1)

async def submit_and_get(session, payload):
    url = f'http://localhost:{PORT_GRADER}/submit'
    async with session.post(url, json=payload) as resp:
        return await resp.json()

@pytest.mark.asyncio
async def test_deterministic_behavior(tmp_path):
    scorer_runner, grader_runner = await start_servers()
    await asyncio.sleep(0.1)
    results = []
    session = ClientSession()
    try:
        for case in TEST_CASES:
            payload = case['input']
            payload['scorer_config'] = case['scorer_config']
            outputs = []
            latencies = []
            for i in range(REPEAT):
                start = time.time()
                res = await submit_and_get(session, payload)
                latencies.append(time.time() - start)
                outputs.append(res)
                await asyncio.sleep(0.005)
            unique = {}
            for out in outputs:
                key = json.dumps(out, sort_keys=True)
                unique.setdefault(key, 0)
                unique[key] += 1
            inconsistency_count = len(unique) - 1
            flakiness_rate = 1.0 if inconsistency_count > 0 else 0.0
            scores = [o.get('score', 0) for o in outputs]
            score_var = 0.0
            if len(scores) > 1:
                mean = sum(scores) / len(scores)
                score_var = sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)
            avg_latency = sum(latencies) / len(latencies) if latencies else None
            error_count = sum(1 for o in outputs if o.get('breakdown') and any(str(b.get('score'))=="0" or b.get('error') for b in o.get('breakdown', {}).values()))
            results.append({
                'case_id': case['id'],
                'unique_outputs': len(unique),
                'inconsistency_count': inconsistency_count,
                'flakiness_rate': flakiness_rate,
                'score_var': score_var,
                'avg_latency': avg_latency,
                'error_count': error_count,
                'samples': outputs[:5]
            })
            print(f"Case {case['id']}: unique_outputs={len(unique)} score_var={score_var}")
    finally:
        await session.close()
        await stop_servers(scorer_runner, grader_runner)

    with open(os.path.join(tmp_path, 'results_post.json'), 'w') as rf:
        json.dump(results, rf, indent=2)
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        outpath = os.path.join(repo_root, 'results', 'results_post.json')
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'w') as rf:
            json.dump(results, rf, indent=2)
    except Exception:
        pass

    # Expect determinism (zero inconsistency for all cases)
    assert all(r['inconsistency_count'] == 0 for r in results), "Post-fix should be deterministic across repeated runs"
