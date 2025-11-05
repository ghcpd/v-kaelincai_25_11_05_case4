# Comparison Report

This experiment demonstrates flakiness in Project_A_Flaky and deterministic behavior in Project_B_Deterministic.

How to reproduce:
- Run `bash run_all.sh` (Unix) or use `run_all.ps1` (PowerShell) to run both test suites and generate metrics.

Summary Metrics:
- `results/results_pre.json` and `results/results_post.json` contain per-test-case results. Use `scripts/aggregate_metrics.py` to create `results/aggregated_metrics.json`.

Expected outcome:
- Project A: non-zero flakiness_rate and score variance in at least one test.
- Project B: flakiness_rate == 0 across repeated runs (deterministic aggregation).

Recommendations and root cause analysis:
- Flakiness root cause: read-modify-write races that cause lost updates, naive retries that cause duplicates or overwrite, response arrival order affecting write sequences.
- Mitigation: gather replies, sort by q id or use consistent ordering, apply atomic commit per submission, idempotency keys for retried requests, bounded retries with backoff.

Limitations:
- This experiment uses in-process mocks and does not use external durable storage; in production systems, use persistent stores, transactional commits, or a central aggregator.
- If external scorers are inherently non-idempotent, additional efforts are necessary (e.g., versioned results, consensus).

See `results/aggregated_metrics.json` and `results/` for detailed logs and metrics.
