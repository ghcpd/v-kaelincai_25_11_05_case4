# Experiment: Flaky Behavior Detection & Mitigation

This experiment reproduces a flaky, nondeterministic grading pipeline and a fixed deterministic version.

Flaky scenario:
- A grader concurrently calls multiple scorer services for each question without synchronization.
- Each scorer may return at variable latency, with intermittent failures.
- The flaky aggregator performs read-modify-write updates across tasks without locks, leading to lost updates and inconsistent total scores for identical inputs.

Fix approach:
- Wait for all scorer replies using asyncio.gather.
- Introduce retries with idempotency keys to avoid duplicate application.
- Aggregate results in deterministic order (sorted by question id) and compute total in one atomic step.

Test plan:
- For each test vector, run 30 repeated submissions, measure unique outputs and score variance.
- Expect Project A to show flakiness; Project B to be deterministic.

Run the experiment:
- `bash run_all.sh` or on Windows use the PowerShell script `run_all.ps1`.

Check `results/aggregated_metrics.json` and `compare_report.md` for metrics and analysis.
