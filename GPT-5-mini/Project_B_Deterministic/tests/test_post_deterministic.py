import os
import sys
import json
from scorer_mock import run_mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# add local src to path
sys.path.insert(0, os.path.join(ROOT, 'src'))

from grading_service import DeterministicGrader

DATA_FILE = os.path.join(os.path.abspath(os.path.join(ROOT,'..')),'test_data.json')

def load_tests():
    with open(DATA_FILE) as f:
        return json.load(f)

def run_case(cfg, runs=30):
    servers = []
    urls = []
    base_port = 9000
    for i,scfg in enumerate(cfg['scorers']):
        port = base_port + i
        server = run_mock(port=port, cfg=scfg)
        servers.append(server)
        urls.append(f'http://127.0.0.1:{port}')
    grader = DeterministicGrader(urls, timeout=0.5, max_retries=3)
    submission = cfg['input']
    outputs = []
    for i in range(runs):
        out = grader.score_submission(submission)
        outputs.append(out)
    for s in servers:
        s.shutdown()
    return outputs

def compare_outputs(outputs):
    import json
    seen = set()
    for o in outputs:
        seen.add(json.dumps(o, sort_keys=True))
    return len(seen)

def main():
    tests = load_tests()
    results = {}
    for t in tests:
        outputs = run_case(t, runs=30)
        unique = compare_outputs(outputs)
        results[t['name']] = {'unique': unique, 'sample': outputs[0]}
        print(t['name'], 'unique outputs:', unique)
    with open(os.path.join(os.path.abspath(os.path.join(ROOT,'..')),'results_post.json'),'w') as f:
        json.dump(results, f, indent=2)
    print('Done. Results in results_post.json')

if __name__ == '__main__':
    main()
