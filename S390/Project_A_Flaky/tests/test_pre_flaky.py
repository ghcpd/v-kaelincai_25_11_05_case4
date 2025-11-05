import asyncio
import json
import os
import time
from aiohttp import ClientSession
import pytest

# Start servers as subprocesses rather than importing modules to avoid package path issues
import subprocess
import signal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
with open(os.path.join(ROOT, 'data', 'test_data.json')) as f:
    TEST_CASES = json.load(f)

PORT_GRADER = int(os.environ.get('PORT_GRADER', '8001'))
PORT_SCORER = int(os.environ.get('PORT_SCORER', '9001'))
REPEAT = int(os.environ.get('REPEAT', '30'))
CONCURRENCY = int(os.environ.get('CONCURRENCY', '5'))

# Helper to start servers as subprocesses
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
async def test_flaky_behavior(tmp_path):
    scorer_runner, grader_runner = await start_servers()
    # Wait briefly for servers
    await asyncio.sleep(0.1)
    results = []
    session = ClientSession()
    try:
        for case in TEST_CASES:
            payload = case['input']
            # Attach scorer_config to the submission payload so that the scorer mock uses it
            payload['scorer_config'] = case['scorer_config']
            outputs = []
            latencies = []
            # run REPEAT repeated submissions serially to measure nondeterminism
            for i in range(REPEAT):
                start = time.time()
                res = await submit_and_get(session, payload)
                latencies.append(time.time() - start)
                outputs.append(res)
                await asyncio.sleep(0.01)
            # compute stats
            # Determine unique outputs by serialized JSON string
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
            # Print a short summary
            print(f"Case {case['id']}: unique_outputs={len(unique)} score_var={score_var}")
    finally:
        await session.close()
        await stop_servers(scorer_runner, grader_runner)

    # Save machine readable results
    with open(os.path.join(tmp_path, 'results_pre.json'), 'w') as rf:
        json.dump(results, rf, indent=2)
    # Write to shared results folder if exists
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        outpath = os.path.join(repo_root, 'results', 'results_pre.json')
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'w') as rf:
            json.dump(results, rf, indent=2)
    except Exception:
        pass

    # Make an assertion for at least one case being flaky (pre-fix expectation)
    assert any(r['inconsistency_count'] > 0 for r in results), "Pre-fix should show flakiness in at least one case"
