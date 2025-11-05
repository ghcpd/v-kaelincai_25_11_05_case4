"""
Scorer mock for simulating variable latency and intermittent failures.
Accepts POST /score with JSON {submission_id, q, answer}
Config via env: MIN_DELAY_MS, MAX_DELAY_MS, FAIL_RATE
"""

import os
import asyncio
import json
import random
from aiohttp import web

async def score_handler(request):
    payload = await request.json()
    qid = payload.get('q')
    answer = payload.get('answer')
    # Read config per-request for dynamic test control - prefer payload config, fallback to env
    cfg = payload.get('scorer_config') or {}
    min_delay = int(cfg.get('MIN_DELAY_MS', os.environ.get('MIN_DELAY_MS', '10')))
    max_delay = int(cfg.get('MAX_DELAY_MS', os.environ.get('MAX_DELAY_MS', '400')))
    fail_rate = float(cfg.get('FAIL_RATE', os.environ.get('FAIL_RATE', '0.15')))
    jitter = int(cfg.get('JITTER', os.environ.get('JITTER', '0')))
    # Simulate variable delay
    delay_ms = random.randint(min_delay, max_delay)
    await asyncio.sleep(delay_ms / 1000.0)
    # Simulate occasional failure
    if random.random() < fail_rate:
        print(f"SCORER_TRACE: FAIL q={qid} answer={answer}")
        return web.Response(status=503, text='service unavailable')
    # Simple scoring: map answers to score value
    score_map = {'A': 10, 'B': 5, 'C': 0, 'D': 0}
    score = score_map.get(answer, 0)
    # Add small jitter to score for nondeterminism if desired
    jitter = int(os.environ.get('JITTER', '0'))
    if jitter:
        score += random.randint(-jitter, jitter)
        if score < 0:
            score = 0
    return web.json_response({'q': qid, 'score': score})

async def start_mock_server(port=9001):
    app = web.Application()
    app.router.add_post('/score', score_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Scorer mock running on http://0.0.0.0:{port} (dynamic delay/fail config via env variables)")
    return runner

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9001)
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(start_mock_server(args.port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    loop.run_until_complete(runner.cleanup())
