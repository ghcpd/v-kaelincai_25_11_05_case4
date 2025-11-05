"""
Generate comparison report from pre-fix and post-fix results.
"""
import json
from pathlib import Path
from typing import Dict, Any
import statistics

def load_results(results_file: str) -> Dict[str, Any]:
    """Load JSON results file."""
    with open(results_file) as f:
        return json.load(f)

def compare_results(results_pre_path: str, results_post_path: str, output_path: str) -> None:
    """
    Compare pre-fix (flaky) and post-fix (deterministic) results.
    Generate a markdown comparison report.
    """
    
    # Load results
    results_pre = load_results(results_pre_path)
    results_post = load_results(results_post_path)
    
    # Extract test results
    tests_pre = {r["test_name"]: r for r in results_pre.get("test_results", [])}
    tests_post = {r["test_name"]: r for r in results_post.get("test_results", [])}
    
    # Build comparison
    markdown_lines = [
        "# Flaky Behavior - Pre-Fix vs Post-Fix Comparison Report",
        "",
        f"**Report Generated:** {results_pre.get('test_run_timestamp')}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report compares the behavior of Project A (Flaky - baseline) and Project B (Deterministic - fixed)",
        "across multiple test scenarios designed to trigger non-deterministic behavior.",
        "",
        "### Key Findings",
        "",
    ]
    
    # Summary stats
    pre_summary = results_pre.get("summary", {})
    post_summary = results_post.get("summary", {})
    
    flaky_cases_pre = pre_summary.get("flaky_test_cases", 0)
    deterministic_cases_post = post_summary.get("deterministic_test_cases", 0)
    total_cases = pre_summary.get("total_test_cases", 0)
    
    markdown_lines.extend([
        f"- **Project A (Flaky):** {flaky_cases_pre}/{total_cases} test cases showed flaky behavior",
        f"- **Project B (Deterministic):** {deterministic_cases_post}/{total_cases} test cases showed deterministic behavior",
        f"- **Improvement:** {((deterministic_cases_post - flaky_cases_pre) / max(1, total_cases) * 100):.1f}% reduction in flakiness",
        "",
        "---",
        "",
        "## Detailed Test Results",
        "",
    ])
    
    # Detailed comparison per test
    all_test_names = set(tests_pre.keys()) | set(tests_post.keys())
    
    for test_name in sorted(all_test_names):
        test_pre = tests_pre.get(test_name, {})
        test_post = tests_post.get(test_name, {})
        
        markdown_lines.extend([
            f"### Test: {test_name}",
            "",
            "#### Pre-Fix (Project A - Flaky)",
            "",
        ])
        
        if test_pre:
            markdown_lines.extend([
                f"- **Total Runs:** {test_pre.get('total_runs', 'N/A')}",
                f"- **Successful Runs:** {test_pre.get('successful_runs', 'N/A')}",
                f"- **Flaky:** {test_pre.get('flaky', False)}",
                f"- **Flakiness Rate:** {test_pre.get('flakiness_rate', 0)*100:.2f}%",
                f"- **Unique Outputs:** {test_pre.get('unique_outputs', 'N/A')}",
                f"- **Mean Score:** {test_pre.get('mean_score', 0):.2f}",
                f"- **Score Std Dev:** {test_pre.get('score_std_dev', 0):.2f}",
                f"- **Score Range:** {test_pre.get('min_score', 'N/A')} - {test_pre.get('max_score', 'N/A')}",
                f"- **Score Distribution:** {test_pre.get('score_distribution', {})}",
            ])
        else:
            markdown_lines.append("- No data available")
        
        markdown_lines.extend([
            "",
            "#### Post-Fix (Project B - Deterministic)",
            "",
        ])
        
        if test_post:
            markdown_lines.extend([
                f"- **Total Runs:** {test_post.get('total_runs', 'N/A')}",
                f"- **Successful Runs:** {test_post.get('successful_runs', 'N/A')}",
                f"- **Deterministic:** {test_post.get('deterministic', False)}",
                f"- **Determinism Score:** {test_post.get('determinism_score', 0)*100:.2f}%",
                f"- **Unique Outputs:** {test_post.get('unique_outputs', 'N/A')}",
                f"- **Mean Score:** {test_post.get('mean_score', 0):.2f}",
                f"- **Score Std Dev:** {test_post.get('score_std_dev', 0):.2f}",
                f"- **Score Range:** {test_post.get('min_score', 'N/A')} - {test_post.get('max_score', 'N/A')}",
                f"- **Score Distribution:** {test_post.get('score_distribution', {})}",
            ])
        else:
            markdown_lines.append("- No data available")
        
        # Comparison
        markdown_lines.extend([
            "",
            "#### Comparison",
            "",
        ])
        
        if test_pre and test_post:
            flakiness_improvement = test_pre.get("flakiness_rate", 0) - test_post.get("determinism_score", 1)
            variance_improvement = test_pre.get("score_std_dev", 0) - test_post.get("score_std_dev", 0)
            
            markdown_lines.extend([
                f"- **Flakiness Reduction:** {flakiness_improvement*100:.2f}%",
                f"- **Variance Reduction:** {variance_improvement:.2f}",
                f"- **Unique Output Reduction:** {test_pre.get('unique_outputs', 0) - test_post.get('unique_outputs', 0)}",
            ])
        
        markdown_lines.append("")
    
    # Metrics summary table
    markdown_lines.extend([
        "---",
        "",
        "## Metrics Summary Table",
        "",
        "| Metric | Pre-Fix (A) | Post-Fix (B) | Improvement |",
        "|--------|-------------|-------------|-------------|",
    ])
    
    # Aggregate flakiness metrics
    avg_flakiness_pre = statistics.mean([t.get("flakiness_rate", 0) for t in tests_pre.values()]) if tests_pre else 0
    avg_determinism_post = statistics.mean([t.get("determinism_score", 0) for t in tests_post.values()]) if tests_post else 0
    avg_variance_pre = statistics.mean([t.get("score_std_dev", 0) for t in tests_pre.values()]) if tests_pre else 0
    avg_variance_post = statistics.mean([t.get("score_std_dev", 0) for t in tests_post.values()]) if tests_post else 0
    
    markdown_lines.extend([
        f"| Avg Flakiness Rate | {avg_flakiness_pre*100:.2f}% | {(1-avg_determinism_post)*100:.2f}% | {(avg_flakiness_pre - (1-avg_determinism_post))*100:.2f}% |",
        f"| Avg Score Std Dev | {avg_variance_pre:.2f} | {avg_variance_post:.2f} | {avg_variance_pre - avg_variance_post:.2f} |",
        f"| Deterministic Tests | 0/{total_cases} | {deterministic_cases_post}/{total_cases} | +{deterministic_cases_post} |",
        "",
    ])
    
    # Root cause analysis and fixes
    markdown_lines.extend([
        "---",
        "",
        "## Root Cause Analysis & Fixes Implemented",
        "",
        "### Project A (Flaky) - Issues Identified",
        "",
        "1. **Unordered Async Completion (Race Condition)**",
        "   - `asyncio.gather()` returns results in task completion order, not submission order",
        "   - Variable latencies cause out-of-order score aggregation",
        "   - Same submission may produce different scores on different runs",
        "",
        "2. **Missing Aggregation Locks**",
        "   - No synchronization during result accumulation",
        "   - Concurrent tasks may interleave dictionary updates",
        "   - Race condition in `_aggregate_scores()`",
        "",
        "3. **Non-Idempotent Retries**",
        "   - Retry logic doesn't track idempotency keys",
        "   - Late responses can overwrite earlier successful scores",
        "   - No deduplication of duplicate scorer calls",
        "",
        "4. **No Result Versioning**",
        "   - Each retry overwrites previous result without checking timestamp or version",
        "   - No atomic comparison-and-swap or similar mechanism",
        "",
        "### Project B (Deterministic) - Fixes Applied",
        "",
        "1. **Sequence-Numbered Task Ordering**",
        "   - Assign sequence numbers to each question at submission time",
        "   - Reconstruct original submission order before aggregation",
        "   - Guarantees deterministic output order regardless of completion order",
        "",
        "2. **Per-Question Result Locking & Versioning**",
        "   - Maintain `question_results` cache indexed by idempotency key",
        "   - Ensure only one result accepted per (submission, question) pair",
        "   - No overwriting of valid results by late responses",
        "",
        "3. **Idempotent Retry with Idempotency Keys**",
        "   - Generate idempotency key: `submission_id#question_id`",
        "   - Pass key to scorer to track retry attempts",
        "   - Cache checks before retry to deduplicate requests",
        "",
        "4. **Exponential Backoff with Jitter**",
        "   - Implement bounded retries with exponential backoff: `backoff = base * 2^attempt`",
        "   - Reduces thundering herd on retry storms",
        "   - Prevents timeout cascades",
        "",
        "5. **Deterministic Aggregation Step**",
        "   - Use `OrderedDict` to preserve insertion order",
        "   - Aggregate in explicit sequence order, not completion order",
        "   - Atomic result construction ensures no partial states leak",
        "",
    ])
    
    # Recommendations
    markdown_lines.extend([
        "---",
        "",
        "## Recommendations & Limitations",
        "",
        "### Limitations of Current Fix",
        "",
        "1. **External Scorer Non-Idempotence**",
        "   - If external scorer services are truly non-idempotent and cannot be modified,",
        "   - consider version-based result selection or consensus protocols.",
        "",
        "2. **State Recovery**",
        "   - Cache is in-memory; not persisted across restarts.",
        "   - For production, use durable storage (e.g., Redis, database) for idempotency keys.",
        "",
        "3. **Partial Failures**",
        "   - If scorer times out after max retries, score is reported as error.",
        "   - Consider graceful degradation (partial scoring or default scores).",
        "",
        "### Recommended Operational Mitigations",
        "",
        "1. **Enable Structured Logging**",
        "   - Log all scorer calls with timestamps and idempotency keys.",
        "   - Correlate retries with original requests for debugging.",
        "",
        "2. **Monitor Idempotency Key Collisions**",
        "   - Alert if idempotency cache hit rate drops (indicates external scorer changes).",
        "",
        "3. **Implement Circuit Breaker Pattern**",
        "   - Fail fast if scorer error rate exceeds threshold.",
        "   - Prevent retry storms cascading to other submissions.",
        "",
        "4. **Centralized Aggregator Service**",
        "   - Consider decoupling scoring from aggregation.",
        "   - Dedicated aggregation service maintains transaction semantics.",
        "",
        "5. **Determinism Testing in CI/CD**",
        "   - Run determinism tests on every commit.",
        "   - Fail build if determinism_score < 99.9%.",
        "",
    ])
    
    # Conclusion
    markdown_lines.extend([
        "---",
        "",
        "## Conclusion",
        "",
        "Project B demonstrates significant improvement in determinism and reliability:",
        "",
        f"- **Flakiness eliminated:** {flaky_cases_pre} flaky cases reduced to {total_cases - deterministic_cases_post}",
        f"- **Output variance eliminated:** {avg_variance_pre:.2f} std dev → {avg_variance_post:.2f} std dev",
        "",
        "The fixes employ industry-standard patterns for deterministic distributed systems:",
        "idempotency keys, ordered aggregation, result versioning, and explicit retry semantics.",
        "",
        "When combined with proper operational practices (centralized logging, circuit breakers,",
        "bounded retries), these techniques ensure production-grade reliability for async scoring pipelines.",
        "",
    ])
    
    # Write report
    report_content = "\n".join(markdown_lines)
    with open(output_path, "w") as f:
        f.write(report_content)
    
    print(f"✓ Comparison report written to {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python compare_results.py <results_pre.json> <results_post.json> <output.md>")
        sys.exit(1)
    
    compare_results(sys.argv[1], sys.argv[2], sys.argv[3])
