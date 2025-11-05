import asyncio
import os
import json
import random

from typing import Dict, Any
from mocks.scorer_mock import ScorerMock

# Flaky grader - naive aggregator with double-count bug on retries
class FlakyGrader:
    def __init__(self, config):
        self.scorers = [ScorerMock(i, config) for i in range(config.get('num_scorers', 3))]

    async def grade_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = submission['submission_id']
        answers = submission['answers']
        total = 0
        breakdown = []

        # For each question, dispatch scoring to multiple scorers
        async def score_question(q):
            nonlocal total
            # Each scorer can return a partial score asynchronously; naive code sums as they arrive
            tasks = []
            for s in self.scorers:
                tasks.append(asyncio.create_task(s.score(submission_id, q)))
            # Wait for any to finish (simulate race) and sum results as they come
            for t in asyncio.as_completed(tasks):
                try:
                    r = await t
                    # BUG: naively add partial result to total; retries may cause duplicate adds
                    total += r['score']
                except Exception as e:
                    # swallow errors => missing scores
                    pass
            # record breakdown per question as last seen
            breakdown.append({'q': q['q'], 'ans': q['ans']})

        await asyncio.gather(*(score_question(q) for q in answers))
        return {'submission_id': submission_id, 'score': total, 'breakdown': breakdown}

if __name__ == '__main__':
    import sys
    cfg = json.loads(os.environ.get('FLAKY_CONFIG', '{}') or '{}')
    grader = FlakyGrader(cfg)
    data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else json.loads('[]')
    async def main():
        out = await grader.grade_submission(data)
        print(json.dumps(out))
    asyncio.run(main())
