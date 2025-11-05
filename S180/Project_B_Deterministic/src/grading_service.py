import asyncio
import json
import random
from typing import Dict, Any
from mocks.scorer_mock import ScorerMock

# Deterministic grader - idempotent and order-insensitive aggregation
class DeterministicGrader:
    def __init__(self, config):
        self.scorers = [ScorerMock(i, config) for i in range(config.get('num_scorers', 3))]

    async def grade_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = submission['submission_id']
        answers = submission['answers']
        # store per-question per-scorer results with idempotent keys
        results = {q['q']: {} for q in answers}

        async def score_question(q):
            tasks = []
            for s in self.scorers:
                tasks.append(asyncio.create_task(self._idempotent_call(s, submission_id, q, results)))
            await asyncio.gather(*tasks, return_exceptions=True)

        await asyncio.gather(*(score_question(q) for q in answers))

        breakdown = []
        total=0
        # deterministic reduction: average of unique scorer scores per question
        for q in answers:
            qid = q['q']
            scores = list(results[qid].values())
            if len(scores)==0:
                qscore=0
            else:
                qscore = sum(scores)/len(scores)
            breakdown.append({'q': qid, 'ans': q['ans'], 'score': qscore})
            total += qscore
        # ensure deterministic type (int)
        return {'submission_id': submission_id, 'score': int(total), 'breakdown': breakdown}

    async def _idempotent_call(self, scorer, submission_id, q, results):
        try:
            r = await scorer.score(submission_id, q)
            # idempotency_key: (scorer_id)
            results[q['q']][r['scorer']] = r['score']
        except Exception:
            # don't fail; leave missing
            pass

if __name__ == '__main__':
    import os
    cfg = json.loads(os.environ.get('DETERMINISTIC_CONFIG', '{}') or '{}')
    grader = DeterministicGrader(cfg)
    import sys
    data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else json.loads('[]')
    async def main():
        out = await grader.grade_submission(data)
        print(json.dumps(out))
    asyncio.run(main())
