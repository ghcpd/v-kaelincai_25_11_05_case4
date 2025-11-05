import os
import time
import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
import requests
import threading

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grading_service_deterministic")

SCORER_PORTS = os.environ.get("SCORER_PORTS", "5001,5002,5003").split(",")
RETRY_COUNT = int(os.environ.get("RETRY_COUNT", "2"))
TIMEOUT_S = float(os.environ.get("REQUEST_TIMEOUT", "0.5"))

# deterministic global store with locks and idempotency tracking
results_store = {}
processed_keys = set()
store_lock = threading.Lock()

CORRECT_ANSWERS = {"1": "B", "2": "A", "3": "C", "4": "D", "5":"A"}


def call_scorer_deterministic(scorer_port, submission_id, q, ans, attempt=1):
    url = f"http://127.0.0.1:{scorer_port}/score"
    payload = {"submission_id": submission_id, "q": q, "ans": ans, "idempotency_key": f"{submission_id}-{q}-{scorer_port}"}
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT_S)
        r.raise_for_status()
        data = r.json()
        # include which scorer replied for idempotency
        data["scorer_port"] = scorer_port
        return data
    except Exception as e:
        logger.info(f"scorer call failed port={scorer_port} q={q} attempt={attempt}: {e}")
        if attempt <= RETRY_COUNT:
            # idempotent retry: call again but deduped by key
            time.sleep(0.01 * attempt)
            return call_scorer_deterministic(scorer_port, submission_id, q, ans, attempt + 1)
        return {"ok": False, "reason": str(e), "scorer_port": scorer_port}


def aggregate_response_deterministic(submission_id, q, data):
    # atomic update with lock, using idempotency keys to ensure no double-count
    global results_store, processed_keys
    if not data.get("ok", True):
        return
    scorer_port = data.get("scorer_port")
    idempotency_key = f"{submission_id}:{q}:{scorer_port}"

    with store_lock:
        if idempotency_key in processed_keys:
            logger.info(f"[DETERMINISTIC] duplicate ignored {idempotency_key}")
            return
        score = data.get("score", 0)
        if submission_id not in results_store:
            results_store[submission_id] = {}
        # use deterministic reduction: sum scores per question
        results_store[submission_id].setdefault(q, 0)
        results_store[submission_id][q] += score
        processed_keys.add(idempotency_key)
        logger.info(f"[DETERMINISTIC] submission={submission_id} q={q} scorer={scorer_port} added {score}")


@app.route("/grade", methods=["POST"])
def grade_endpoint():
    payload = request.get_json() or {}
    submission_id = payload.get("submission_id")
    answers = payload.get("answers", [])

    if not submission_id or not isinstance(answers, list):
        return jsonify({"ok": False, "reason": "bad_request"}), 400

    # reset for this submission
    with store_lock:
        results_store.pop(submission_id, None)
        # don't clear processed key set globally; but for simplicity we will remove keys with this submission prefix
        removed = [k for k in processed_keys if k.startswith(submission_id + ":")]
        for k in removed:
            processed_keys.remove(k)

    tasks = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        for a in answers:
            q = a.get("q")
            ans = a.get("ans")
            for port in SCORER_PORTS:
                tasks.append(ex.submit(lambda p, sid, qid, ansv: aggregate_response_deterministic(sid, qid, call_scorer_deterministic(p, sid, qid, ansv)), port, submission_id, q, ans))

        for t in tasks:
            try:
                t.result()
            except Exception:
                pass

    # deterministic final result: sum questions in sorted order
    scored = results_store.get(submission_id, {})
    ordered_qs = sorted(scored.keys(), key=lambda x: int(x))
    total_score = sum(scored[q] for q in ordered_qs)
    logger.info(f"[DETERMINISTIC] submission={submission_id} total_score={total_score} detail={scored}")
    return jsonify({"ok": True, "submission_id": submission_id, "score": total_score, "breakdown": scored})


if __name__ == "__main__":
    port = int(os.environ.get("GRADER_PORT", 7000))
    app.run(port=port, debug=False)
