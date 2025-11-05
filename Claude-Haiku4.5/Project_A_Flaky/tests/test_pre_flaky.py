"""
Test harness for Project A (Flaky) - demonstrates non-deterministic behavior
"""
import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import time
import random

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "mocks"))

from mocks.scorer_mock import ScorerRegistry
from src.grading_service import FlakyGradingService

# Configure logging
log_file = Path(__file__).parent.parent / "logs" / "test_pre_flaky.txt"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


class FlakyTestHarness:
    """Test harness for Project A - demonstrates and measures flakiness."""
    
    def __init__(self, test_data_path: str, seed: int = 42):
        self.test_data_path = test_data_path
        self.seed = seed
        with open(test_data_path) as f:
            self.test_data = json.load(f)
        self.results = []
    
    async def run_single_test(
        self, submission: Dict[str, Any], scorer_registry: ScorerRegistry
    ) -> Dict[str, Any]:
        """Run a single test - grade one submission."""
        service = FlakyGradingService(scorer_registry)
        try:
            result = await service.grade_submission(submission)
            result["success"] = True
            return result
        except Exception as e:
            logger.error(f"Grading failed for {submission.get('submission_id')}: {e}")
            return {
                "submission_id": submission.get("submission_id"),
                "success": False,
                "error": str(e),
            }
    
    async def run_test_case(
        self, test_case: Dict[str, Any], repeat_count: int = 30
    ) -> Dict[str, Any]:
        """
        Run a test case multiple times to capture flakiness.
        
        For each run, we reuse the same submission and scorer config but 
        let async execution vary the results.
        """
        test_name = test_case.get("name", "unknown")
        logger.info(f"\n{'='*70}")
        logger.info(f"Running test case: {test_name}")
        logger.info(f"Repeating {repeat_count} times to measure flakiness")
        logger.info(f"{'='*70}\n")
        
        test_results = []
        
        for run_num in range(repeat_count):
            # Create fresh scorer registry for this run
            run_seed = self.seed + run_num if self.seed else None
            scorer_registry = ScorerRegistry(seed=run_seed)
            
            # Register scorers with configured latency/failure
            scorer_config = test_case.get("scorer_config", {})
            for qid, config in scorer_config.items():
                scorer_registry.register_scorer(
                    qid,
                    mean_latency_ms=config.get("mean_latency_ms", 50),
                    latency_variance_ms=config.get("latency_variance_ms", 30),
                    failure_rate=config.get("failure_rate", 0.05),
                )
            
            # Get submission (for simple test case)
            if "submission" in test_case:
                submission = test_case["submission"]
            else:
                logger.warning(f"Skipping test case {test_name} - no submission defined")
                continue
            
            logger.info(f"  Run {run_num+1}/{repeat_count}: {submission['submission_id']}")
            
            result = await self.run_single_test(submission, scorer_registry)
            result["run_number"] = run_num + 1
            test_results.append(result)
        
        # Analyze flakiness
        return self._analyze_flakiness(test_name, test_results, test_case)
    
    def _analyze_flakiness(
        self, test_name: str, test_results: List[Dict[str, Any]], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze results across repeated runs to measure flakiness.
        
        Flakiness metrics:
        - inconsistency_count: number of runs with different outputs
        - flakiness_rate: fraction of runs with different outputs
        - score_variance: statistical variance of scores
        - output_hashes: track unique output combinations
        """
        
        # Extract scores and breakdowns
        scores = []
        score_vectors = []  # Full breakdown for each run
        errors = []
        
        for result in test_results:
            if result.get("success"):
                score = result.get("total_score", 0)
                scores.append(score)
                score_vectors.append((score, json.dumps(result.get("breakdown", {}), sort_keys=True)))
            else:
                errors.append(result.get("error", "Unknown error"))
        
        # Calculate metrics
        num_runs = len(test_results)
        num_success = len(scores)
        num_failures = num_runs - num_success
        
        # Check for output consistency
        unique_outputs = set(sv[1] for sv in score_vectors)
        inconsistency_count = len(unique_outputs) - 1 if unique_outputs else 0
        flakiness_rate = inconsistency_count / max(1, num_runs)
        
        # Score variance
        if scores:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5
        else:
            mean_score = variance = std_dev = 0
        
        analysis = {
            "test_name": test_name,
            "total_runs": num_runs,
            "successful_runs": num_success,
            "failed_runs": num_failures,
            "unique_outputs": len(unique_outputs),
            "inconsistency_count": inconsistency_count,
            "flakiness_rate": flakiness_rate,
            "flaky": flakiness_rate > 0.01,  # More than 1% variance = flaky
            "mean_score": mean_score,
            "score_variance": variance,
            "score_std_dev": std_dev,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None,
            "score_distribution": defaultdict(int),
            "errors": errors,
        }
        
        # Build score distribution
        for score in scores:
            analysis["score_distribution"][int(score)] += 1
        analysis["score_distribution"] = dict(analysis["score_distribution"])
        
        logger.info(f"\nFLAKINESS ANALYSIS FOR {test_name}:")
        logger.info(f"  Total runs: {num_runs}")
        logger.info(f"  Successful: {num_success}, Failed: {num_failures}")
        logger.info(f"  Unique outputs: {len(unique_outputs)}")
        logger.info(f"  Inconsistency count: {inconsistency_count}")
        logger.info(f"  Flakiness rate: {flakiness_rate*100:.2f}%")
        logger.info(f"  Mean score: {mean_score:.2f}")
        logger.info(f"  Score std dev: {std_dev:.2f}")
        logger.info(f"  Score range: {min(scores) if scores else 'N/A'} - {max(scores) if scores else 'N/A'}")
        logger.info(f"  Score distribution: {analysis['score_distribution']}")
        if errors:
            logger.info(f"  Errors: {set(errors)}")
        logger.info("")
        
        return analysis
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and return aggregated results."""
        all_results = []
        
        for test_case in self.test_data.get("test_cases", []):
            test_name = test_case.get("name")
            repeat_count = test_case.get("repeat_count", 30)
            
            # Skip edge case tests for now (they require special handling)
            if test_name == "malformed_edge_inputs":
                logger.info(f"Skipping {test_name} - requires special handling")
                continue
            
            result = await self.run_test_case(test_case, repeat_count)
            all_results.append(result)
        
        return self._create_final_report(all_results)
    
    def _create_final_report(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create final report with aggregated metrics."""
        total_runs = sum(r.get("total_runs", 0) for r in all_results)
        total_failures = sum(r.get("failed_runs", 0) for r in all_results)
        total_flaky = sum(1 for r in all_results if r.get("flaky", False))
        
        report = {
            "project": "Project_A_Flaky",
            "test_run_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_test_cases": len(all_results),
                "total_runs": total_runs,
                "total_failures": total_failures,
                "flaky_test_cases": total_flaky,
            },
            "test_results": all_results,
        }
        
        logger.info(f"\n{'='*70}")
        logger.info("FINAL REPORT - PROJECT A (FLAKY)")
        logger.info(f"{'='*70}")
        logger.info(f"Total test cases: {len(all_results)}")
        logger.info(f"Total runs: {total_runs}")
        logger.info(f"Total failures: {total_failures}")
        logger.info(f"Flaky test cases: {total_flaky}/{len(all_results)}")
        logger.info(f"{'='*70}\n")
        
        return report


async def main():
    """Run the flaky test harness."""
    test_data_path = Path(__file__).parent.parent.parent / "shared_artifacts" / "test_data.json"
    
    harness = FlakyTestHarness(str(test_data_path), seed=42)
    report = await harness.run_all_tests()
    
    # Save results
    results_file = Path(__file__).parent.parent / "logs" / "results_pre.json"
    with open(results_file, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Results saved to {results_file}")
    
    return report


if __name__ == "__main__":
    report = asyncio.run(main())
    print(f"\n✓ Flaky tests completed. Results saved.")
