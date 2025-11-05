import requests
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class DeterministicGrader:
    def __init__(self, scorer_urls, timeout=1.0, max_retries=2):
        self.scorer_urls = scorer_urls
        self.timeout = timeout
        self.max_retries = max_retries

    def _call_with_retries(self, url, payload, idempotency_key):
        last_exc = None
        headers = {'Idempotency-Key': idempotency_key}
        for attempt in range(self.max_retries+1):
            try:
                r = requests.post(url, json=payload, timeout=self.timeout, headers=headers)
                if r.status_code==200:
                    return r.json()
                last_exc = Exception(f'status {r.status_code}')
            except Exception as e:
                last_exc = e
                time.sleep(0.05 * (attempt+1))
        return {'error': str(last_exc)}

    def score_submission(self, submission):
        # Validate input
        answers = submission.get('answers')
        if not isinstance(answers, list):
            return {'submission_id': submission.get('submission_id'), 'error':'bad input'}

        # For determinism, we will query each scorer once per question and reduce deterministically:
        # - Use idempotency keys per (submission_id, q)
        # - Aggregate by taking the max score across scorers (order-insensitive)
        per_q_scores = {qa.get('q'): [] for qa in answers}

        def call(q, a, url):
            payload = {'q': q, 'answer': a}
            ik = f"{submission.get('submission_id')}:{q}"
            return q, self._call_with_retries(url, payload, ik)

        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = []
            for qa in answers:
                q = qa.get('q')
                a = qa.get('ans')
                for url in self.scorer_urls:
                    futures.append(ex.submit(call, q, a, url))
            for fut in as_completed(futures):
                q, res = fut.result()
                if 'score' in res:
                    per_q_scores[q].append(res['score'])

        # Deterministic reduce: sort questions and use max score to avoid last-writer wins
        breakdown = []
        total = 0
        for q in sorted(per_q_scores.keys(), key=lambda x: str(x)):
            scores = per_q_scores[q]
            chosen = max(scores) if scores else 0
            breakdown.append({'q': q, 'score': chosen})
            total += chosen

        return {'submission_id': submission.get('submission_id'), 'score': total, 'breakdown': breakdown}

if __name__ == '__main__':
    import sys
    urls = sys.argv[1].split(',') if len(sys.argv)>1 else ['http://127.0.0.1:9000']
    grader = DeterministicGrader(urls)
    sample = {'submission_id':'s1','answers':[{'q':'1','ans':'A'},{'q':'2','ans':'B'}]}
    print(json.dumps(grader.score_submission(sample), indent=2))
