import os
import sys
import time
import json
import requests
import threading
from subprocess import Popen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# make src importable
sys.path.insert(0, os.path.join(ROOT, 'src'))

from grading_service import FlakyGrader
from scorer_mock import run_mock

DATA_FILE = os.path.join(ROOT, 'data', 'test_data.json')

def load_tests():
    with open(DATA_FILE) as f:
        return json.load(f)

def run_case(cfg, runs=20):
    # start mocks per cfg
    servers = []
    urls = []
    base_port = 9000
    for i,scfg in enumerate(cfg['scorers']):
        port = base_port + i
        server = run_mock(port=port, cfg=scfg)
        servers.append(server)
        urls.append(f'http://127.0.0.1:{port}')
    grader = FlakyGrader(urls, timeout=0.5)
    submission = cfg['input']
    outputs = []
    for i in range(runs):
        out = grader.score_submission(submission)
        outputs.append(out)
    # stop servers
    for s in servers:
        s.shutdown()
    return outputs

def compare_outputs(outputs):
    # simple comparison of JSON-serialised outputs
    seen = set()
    for o in outputs:
        seen.add(json.dumps(o, sort_keys=True))
    return len(seen), list(seen)[:3]

def main():
    tests = load_tests()
    results = {}
    for t in tests:
        print('\nRunning test:', t['name'])
        outputs = run_case(t, runs=20)
        unique_count, examples = compare_outputs(outputs)
        results[t['name']] = {'unique': unique_count, 'examples': examples, 'outputs': outputs}
        print('Unique outputs:', unique_count)
    with open(os.path.join(ROOT,'logs','log_pre_flaky.txt'),'w') as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(ROOT,'results_pre.json'),'w') as f:
        json.dump(results, f, indent=2)
    print('Done. Results in results_pre.json and logs/log_pre_flaky.txt')

if __name__ == '__main__':
    main()
