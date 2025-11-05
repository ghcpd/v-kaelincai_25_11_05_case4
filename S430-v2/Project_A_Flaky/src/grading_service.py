import os
import time
import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grading_service_flaky")

SCORER_PORTS = os.environ.get("SCORER_PORTS", "5001,5002,5003").split(",")
RETRY_COUNT = int(os.environ.get("RETRY_COUNT", "2"))
TIMEOUT_S = float(os.environ.get("REQUEST_TIMEOUT", "0.5"))

# naive global store - intentionally not thread-safe to reproduce flaky behavior
results_store = {}

CORRECT_ANSWERS = {"1": "B", "2": "A", "3": "C", "4": "D", "5":"A"}


def call_scorer(scorer_port, submission_id, q, ans, attempt=1):
    url = f"http://127.0.0.1:{scorer_port}/score"
    payload = {"submission_id": submission_id, "q": q, "ans": ans}
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT_S)
        r.raise_for_status()
        data = r.json()
        return data
    except Exception as e:
        logger.info(f"scorer call failed port={scorer_port} q={q} attempt={attempt}: {e}")
        if attempt <= RETRY_COUNT:
            # naive retry without idempotency - could overwrite results non-deterministically
            time.sleep(0.01 * attempt)
            return call_scorer(scorer_port, submission_id, q, ans, attempt + 1)
        return {"ok": False, "reason": str(e)}


def aggregate_response_flaky(submission_id, q, data):
    # intentionally non-atomic and race-prone: read-modify-write without locks
    global results_store
    score = data.get("score", 0) if data.get("ok", True) else 0
    existing = results_store.get(submission_id, {}).get(q, 0)
    # simulate lost update by reading then writing with time gap
    time.sleep(0.001 * random.random())
    total_for_q = existing + score
    if submission_id not in results_store:
        results_store[submission_id] = {}
    results_store[submission_id][q] = total_for_q
    logger.info(f"[FLAKY_AGG] submission={submission_id} q={q} added {score} -> {total_for_q}")


@app.route("/grade", methods=["POST"])
def grade_endpoint():
    payload = request.get_json() or {}
    submission_id = payload.get("submission_id")
    answers = payload.get("answers", [])

    if not submission_id or not isinstance(answers, list):
        return jsonify({"ok": False, "reason": "bad_request"}), 400

    # reset for this submission
    results_store.pop(submission_id, None)

    # for each question call each scorer concurrently
    tasks = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for a in answers:
            q = a.get("q")
            ans = a.get("ans")
            for port in SCORER_PORTS:
                tasks.append(ex.submit(lambda p, sid, qid, ansv: aggregate_response_flaky(sid, qid, call_scorer(p, sid, qid, ansv)), port, submission_id, q, ans))

        # wait for tasks to finish
        for t in tasks:
            try:
                t.result()
            except Exception:
                pass

    # produce summary
    scored = results_store.get(submission_id, {})
    total_score = sum(scored.values())
    logger.info(f"[FLAKY] submission={submission_id} total_score={total_score} detail={scored}")
    return jsonify({"ok": True, "submission_id": submission_id, "score": total_score, "breakdown": scored})


if __name__ == "__main__":
    port = int(os.environ.get("GRADER_PORT", 6000))
    app.run(port=port, debug=False)
