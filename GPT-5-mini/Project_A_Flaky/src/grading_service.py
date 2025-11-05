import requests
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class FlakyGrader:
    def __init__(self, scorer_urls, timeout=1.0):
        self.scorer_urls = scorer_urls
        self.timeout = timeout

    def score_submission(self, submission):
        # For each question, fire off async POSTs to scorer services and aggregate naively
        results = {}
        def call_scorer(q, ans, url):
            payload = {'q': q, 'answer': ans}
            try:
                r = requests.post(url, json=payload, timeout=self.timeout)
                return q, r.json()
            except Exception as e:
                return q, {'error': str(e)}

        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = []
            for qa in submission.get('answers', []):
                q = qa.get('q')
                a = qa.get('ans')
                # naive: call all scorers, last writer wins; race-prone
                for url in self.scorer_urls:
                    futures.append(ex.submit(call_scorer, q, a, url))

            for fut in as_completed(futures):
                q, res = fut.result()
                if 'score' in res:
                    # overwrite previous scores -> flaky
                    results[q] = res['score']

        total = sum(results.values())
        breakdown = [{'q':k,'score':v} for k,v in sorted(results.items())]
        return {'submission_id': submission.get('submission_id'), 'score': total, 'breakdown': breakdown}

if __name__ == '__main__':
    # small CLI for manual testing
    import sys
    urls = sys.argv[1].split(',') if len(sys.argv)>1 else ['http://127.0.0.1:9000']
    grader = FlakyGrader(urls)
    sample = {'submission_id':'s1','answers':[{'q':'1','ans':'A'},{'q':'2','ans':'B'}]}
    print(json.dumps(grader.score_submission(sample), indent=2))
