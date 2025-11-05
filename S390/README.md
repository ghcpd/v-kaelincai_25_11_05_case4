# Flaky Behavior Detection & Mitigation Experiment

This repository contains two projects demonstrating a flaky (non-deterministic) exam-grading pipeline and a corrected deterministic version.

Folders:
- Project_A_Flaky - pre-fix, demonstrates lost updates/race non-determinism
- Project_B_Deterministic - post-fix, deterministic aggregation and idempotency
- results - aggregated test outputs

Run the full experiment:
- On Unix-like systems: `bash run_all.sh`
- For Windows PowerShell: run `Project_A_Flaky/run_tests.ps1` and `Project_B_Deterministic/run_tests.ps1` then run the `run_all.sh` in WSL or use similar commands.

See `compare_report.md` for a generated comparison after running tests.
