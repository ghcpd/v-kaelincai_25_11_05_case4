import os
import time
import random
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scorer_mock")

# configuration via env
DELAY_MEAN = float(os.environ.get("DELAY_MEAN", "0.1"))
DELAY_STD = float(os.environ.get("DELAY_STD", "0.05"))
FAIL_RATE = float(os.environ.get("FAIL_RATE", "0.1"))

CORRECT_ANSWERS = {"1": "B", "2": "A", "3": "C", "4": "D", "5": "A"}


@app.route('/score', methods=['POST'])
def score():
    payload = request.get_json() or {}
    q = str(payload.get("q"))
    ans = payload.get("ans")

    # simulate delay
    delay = max(0, random.gauss(DELAY_MEAN, DELAY_STD))
    time.sleep(delay)
    # simulate failure
    if random.random() < FAIL_RATE:
        logger.info(f"scorer FAIL q={q} payload={payload}")
        return jsonify({"ok": False, "reason": "mock_fail"}), 500

    # deterministic scoring logic
    correct = CORRECT_ANSWERS.get(q)
    score_value = 10 if ans == correct else 0
    logger.info(f"scorer OK q={q} ans={ans} score={score_value} delay={delay:.3f}")
    return jsonify({"ok": True, "q": q, "score": score_value})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5001'))
    app.run(port=port, debug=False)
