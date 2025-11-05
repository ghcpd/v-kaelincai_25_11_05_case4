import os
import json
import time
import subprocess
import requests
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_DATA_FILE = ROOT / 'test_data.json'

GRADER_PORT = int(os.environ.get("GRADER_PORT", "6000"))
SCORER_PORTS = os.environ.get("SCORER_PORTS", "5001,5002,5003").split(",")
RUNS = int(os.environ.get("REPEAT_RUNS", "30"))
SEED = os.environ.get("SEED")


def start_process(cmd, env=None):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=False)


def start_mocks_and_grader(scorer_config):
    # start scorers
    procs = []
    for i, p in enumerate(SCORER_PORTS):
        env = os.environ.copy()
        env["DELAY_MEAN"] = str(scorer_config.get("delay_mean", 0.1))
        env["DELAY_STD"] = str(scorer_config.get("delay_std", 0.05))
        env["FAIL_RATE"] = str(scorer_config.get("fail_rate", 0.0))
        env["PORT"] = str(p)
        proc = start_process(["python", str(ROOT / "Project_A_Flaky" / "mocks" / "scorer_mock.py")], env=env)
        procs.append(proc)
    # start grader
    env = os.environ.copy()
    env["GRADER_PORT"] = str(GRADER_PORT)
    env["SCORER_PORTS"] = ",".join(SCORER_PORTS)
    proc_grader = start_process(["python", str(ROOT / "Project_A_Flaky" / "src" / "grading_service.py")], env=env)
    procs.append(proc_grader)
    time.sleep(1.0)
    return procs


def stop_processes(procs):
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass


def run_test_case(test_case):
    submission = test_case["submission"]
    runs = []
    timings = []
    for i in range(RUNS):
        # Allow some jitter
        start = time.time()
        r = requests.post(f"http://127.0.0.1:{GRADER_PORT}/grade", json=submission, timeout=30)
        elapsed = time.time() - start
        timings.append(elapsed)
        runs.append(r.json())
    return runs, timings


def compute_metrics(runs, timings=None):
    # check if outputs identical across runs
    outputs = [json.dumps(r, sort_keys=True) for r in runs]
    unique = set(outputs)
    inconsistency_count = 1 if len(unique) > 1 else 0
    flakiness_rate = 1.0 if len(unique) > 1 else 0.0
    # compute score variance
    scores = [r.get('score', 0) for r in runs]
    avg = sum(scores)/len(scores)
    variance = sum((s-avg)**2 for s in scores)/len(scores)
    res = {
        "inconsistency_count": inconsistency_count,
        "flakiness_rate": flakiness_rate,
        "score_variance": variance,
        "sample_scores": scores[:10]
    }
    if timings:
        avg_t = sum(timings)/len(timings)
        res["avg_latency"] = avg_t
    return res


def test_pre_flaky_experiment():
    # load tests
    tdata = json.load(open(TEST_DATA_FILE))
    results = {}
    for tc in tdata:
        # configure seed per test for reproducibility
        if SEED:
            random.seed(int(SEED))
        # set scorer config
        procs = start_mocks_and_grader(tc["scorer_config"]) 
        try:
            runs, timings = run_test_case(tc)
            metrics = compute_metrics(runs, timings)
            results[tc["id"]] = {"metrics": metrics, "runs": runs, "timings": timings}
        finally:
            stop_processes(procs)
            time.sleep(0.2)

    out_file = ROOT / 'results' / 'results_pre.json'
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
    # assert we observed some non-zero flakiness in at least one of the cases
    flakiness_sum = sum(1 for v in results.values() if v['metrics']['flakiness_rate'] > 0)
    assert flakiness_sum >= 1, "Expected flaky behavior in Project A tests"
