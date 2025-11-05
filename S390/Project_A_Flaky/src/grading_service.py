"""
Flaky grading service - demonstrates nondeterministic outputs due to race conditions.
Exposes HTTP POST /submit endpoint to accept submissions and returns final score (imperfectly).
"""

import asyncio
import json
import os
from aiohttp import web, ClientSession
import random
import time

SCORER_URL = os.environ.get('SCORER_URL', 'http://localhost:9001/score')
CALL_TIMEOUT = float(os.environ.get('CALL_TIMEOUT', '1.5'))

# In-memory store for submissions (not thread-safe in a race-prone way)
submissions = {}

async def call_scorer(session, submission_id, qid, answer, scorer_config=None):
    payload = {'submission_id': submission_id, 'q': qid, 'answer': answer}
    if scorer_config:
        payload['scorer_config'] = scorer_config
    try:
        async with session.post(SCORER_URL, json=payload, timeout=CALL_TIMEOUT) as resp:
            data = await resp.json()
            return data
    except Exception as e:
        # simulate flaky retry behavior (naive, non-idempotent)
        # random retry with no idempotency - can cause duplicates/out-of-order
        if random.random() < 0.5:
            await asyncio.sleep(0.1 + random.random() * 0.2)
            try:
                async with session.post(SCORER_URL, json=payload, timeout=CALL_TIMEOUT) as resp:
                    data = await resp.json()
                    return data
            except Exception:
                return {'q': qid, 'score': 0, 'error': 'timeout'}
        return {'q': qid, 'score': 0, 'error': 'timeout'}

async def process_submission_flaky(app, submission_id, answers):
    # Initialize
    submissions[submission_id] = {'id': submission_id, 'breakdown': {}, 'score': 0}
    session = ClientSession()

    async def task_fn(q):
        qid = q['q']
        answer = q['ans']
        # call scorer
        # Assume caller may provide per-case scorer_config via the 'answers' structure
        config = q.get('scorer_config') or q.get('config') or None
        result = await call_scorer(session, submission_id, qid, answer, scorer_config=config)
        # simulate a read-modify-write race: read current total, add, artificial delay, then write
        cur = submissions[submission_id]['score']
        # random delay increases the chance of lost updates
        await asyncio.sleep(random.uniform(0, 0.05))
        new_total = cur + result.get('score', 0)
        submissions[submission_id]['score'] = new_total
        submissions[submission_id]['breakdown'][qid] = result
        # Logging trace for debugging and analysis
        now = time.time()
        print(f"TRACE: submission={submission_id} q={qid} score={result.get('score')} cur={cur} new_total={new_total} t={now}")

    # schedule tasks without waiting
    for q in answers:
        asyncio.create_task(task_fn(q))

    # Wait for SHORT time then return partial result (flaky behavior: not waiting for all)
    await asyncio.sleep(0.2)
    await session.close()
    return submissions[submission_id]

async def submit_handler(request):
    payload = await request.json()
    submission_id = payload.get('submission_id')
    answers = payload.get('answers', [])
    scorer_config = payload.get('scorer_config') or None
    # attach scorer_config to each answer dict to pass through call
    if scorer_config:
        for q in answers:
            q['scorer_config'] = scorer_config
    res = await process_submission_flaky(request.app, submission_id, answers)
    return web.json_response(res)

async def start_app(port=8001):
    app = web.Application()
    app.router.add_post('/submit', submit_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Flaky grading service running on http://0.0.0.0:{port}")
    return runner

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(start_app(args.port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    loop.run_until_complete(runner.cleanup())
