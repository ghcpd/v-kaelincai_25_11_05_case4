import asyncio
import os
import random
from typing import Dict, Any

class ScorerMock:
    def __init__(self, scorer_id:int, config:Dict[str,Any]):
        self.id = scorer_id
        self.config = config

    async def score(self, submission_id:str, question:Dict[str,Any]) -> Dict[str,Any]:
        # Simulate latency and failures
        latency_cfg = self.config.get('latency', [0.01, 0.1])
        mean, var = latency_cfg
        delay = max(0, random.gauss(mean, var))
        await asyncio.sleep(delay)
        # Simulate intermittent failure
        fail_prob = self.config.get('fail_prob', 0.1)
        if random.random() < fail_prob:
            raise Exception('scorer failure')
        # Score is deterministic per content but different scorers may vary
        base = hash(question['ans']) % 50
        noise = random.randint(0, 50)
        score = base + noise
        return {'scorer': self.id, 'question': question['q'], 'score': score}
