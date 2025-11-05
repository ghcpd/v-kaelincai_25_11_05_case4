# Flaky vs Deterministic Grader Experiment

Run `bash run_all.sh` to execute both projects and generate results.

Project A (Flaky): `Project_A_Flaky` - intentionally flawed aggregation where retries and out-of-order asynchronous results can be double-counted.
Project B (Deterministic): `Project_B_Deterministic` - idempotent per-scorer aggregation, order-insensitive reduce to maintain determinism.

Each project has setup.sh and run_tests.sh. Tests write results to `logs/results_pre.json` and `logs/results_post.json` respectively. 

See `compare_report.md` for summary.
