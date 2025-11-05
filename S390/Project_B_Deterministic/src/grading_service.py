"""
Deterministic grading service - fixes race conditions by collecting all scores and aggregating deterministically.
Implements idempotency and fixed aggregation.
"""

import asyncio
import json
import os
from aiohttp import web, ClientSession
import time

SCORER_URL = os.environ.get('SCORER_URL', 'http://localhost:9001/score')
CALL_TIMEOUT = float(os.environ.get('CALL_TIMEOUT', '1.5'))

# Optional per-submission idempotency store
processed_submissions = {}

async def call_scorer(session, submission_id, qid, answer, scorer_config=None):
    payload = {'submission_id': submission_id, 'q': qid, 'answer': answer}
    if scorer_config:
        payload['scorer_config'] = scorer_config
    try:
        async with session.post(SCORER_URL, json=payload, timeout=CALL_TIMEOUT) as resp:
            if resp.status != 200:
                raise Exception(f"scorer status {resp.status}")
            data = await resp.json()
            return data
    except Exception as e:
        # Use retry with exponential backoff and idempotency key
        for attempt in range(3):
            await asyncio.sleep(0.05 * (2 ** attempt))
            try:
                async with session.post(SCORER_URL, json=payload, timeout=CALL_TIMEOUT) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    return data
            except Exception:
                continue
        return {'q': qid, 'score': 0, 'error': 'timeout'}

async def process_submission_deterministic(app, submission_id, answers):
    if submission_id in processed_submissions:
        # Return the same result for idempotency
        return processed_submissions[submission_id]

    session = ClientSession()
    tasks = [call_scorer(session, submission_id, q['q'], q.get('ans'), scorer_config=q.get('scorer_config')) for q in answers]
    # await all tasks (bounded by timeout) to avoid race conditions
    # we use asyncio.gather to collect results
    try:
        results = await asyncio.gather(*tasks, return_exceptions=False)
    except Exception:
        # ensure we continue with partial results
        results = []
    await session.close()

    # deterministic aggregation: sort by question id then sum
    # normalize results: ensure q ids exist
    def q_key(res):
        try:
            return int(res.get('q'))
        except Exception:
            return 0
    results_sorted = sorted(results, key=q_key)
    total = sum(r.get('score', 0) for r in results_sorted)
    breakdown = {r.get('q'): r for r in results_sorted}
    res = {'id': submission_id, 'score': total, 'breakdown': breakdown}
    processed_submissions[submission_id] = res
    # Logging trace for reproducibility and analysis
    now = time.time()
    print(f"TRACE_DET: submission={submission_id} total={total} t={now} details={breakdown}")
    return res

async def submit_handler(request):
    payload = await request.json()
    submission_id = payload.get('submission_id')
    answers = payload.get('answers', [])
    scorer_config = payload.get('scorer_config') or None
    if scorer_config:
        for q in answers:
            q['scorer_config'] = scorer_config
    res = await process_submission_deterministic(request.app, submission_id, answers)
    return web.json_response(res)

async def start_app(port=8002):
    app = web.Application()
    app.router.add_post('/submit', submit_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Deterministic grading service running on http://0.0.0.0:{port}")
    return runner

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8002)
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(start_app(args.port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    loop.run_until_complete(runner.cleanup())
