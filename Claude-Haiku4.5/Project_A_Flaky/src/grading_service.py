"""
FLAKY GRADING SERVICE - Project A
Demonstrates non-deterministic behavior in exam scoring due to:
1. Unordered async completion (race conditions)
2. Missing aggregation locks
3. Lack of idempotency on retries
4. No ordered result processing
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FlakyGradingService:
    """
    Flaky grading service that scores exam submissions asynchronously.
    
    FLAKY BEHAVIORS:
    - Uses dict accumulation without locks (race condition)
    - Doesn't guarantee processing order
    - Retries overwrite previous results without idempotency keys
    - No atomic aggregation step
    """
    
    def __init__(self, scorer_registry):
        self.scorer_registry = scorer_registry
        self.max_retries = 3
        self.retry_delay = 0.1  # seconds
    
    async def grade_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade an exam submission by scoring each answer asynchronously.
        
        FLAKY POINT #1: Tasks are awaited via gather() which doesn't preserve order.
        Different runs may interleave score updates differently.
        
        Args:
            submission: Dict with submission_id and list of answers
            
        Returns:
            Dict with submission_id, total_score, and per-question breakdown
        """
        submission_id = submission.get("submission_id")
        answers = submission.get("answers", [])
        
        logger.info(f"[{submission_id}] Starting grade for {len(answers)} questions")
        
        # Create tasks for each answer (no ordering guarantee!)
        tasks = []
        for idx, answer_item in enumerate(answers):
            question_id = answer_item.get("question_id", f"q_{idx+1}")
            answer_text = answer_item.get("answer", "")
            
            # FLAKY: Create task with retry logic but no idempotency
            task = self._score_with_retry(
                submission_id, question_id, answer_text, retry_count=0
            )
            tasks.append(task)
        
        # FLAKY POINT #2: gather() returns results in task completion order (not submission order)
        # This means the same submission can aggregate scores in different orders
        scores = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"[{submission_id}] All scoring tasks completed")
        
        # FLAKY POINT #3: No locking - race condition during aggregation
        return self._aggregate_scores(submission_id, scores, answers)
    
    async def _score_with_retry(
        self, submission_id: str, question_id: str, answer: str, retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Score a single answer with retries.
        
        FLAKY: Each retry doesn't check if a previous score exists; just overwrites.
        In concurrent scenarios, late responses can overwrite earlier ones.
        """
        try:
            result = await self.scorer_registry.score_answer(
                question_id, answer, retry_attempt=retry_count
            )
            logger.info(f"[{submission_id}] {question_id} scored: {result['score']}")
            return result
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(
                    f"[{submission_id}] {question_id} failed (attempt {retry_count+1}), retrying..."
                )
                await asyncio.sleep(self.retry_delay)
                # FLAKY: Retry without idempotency key - late response might overwrite good one
                return await self._score_with_retry(
                    submission_id, question_id, answer, retry_count + 1
                )
            else:
                logger.error(f"[{submission_id}] {question_id} failed after {self.max_retries} retries")
                raise
    
    def _aggregate_scores(
        self, submission_id: str, scores: List[Any], answers: List[Dict]
    ) -> Dict[str, Any]:
        """
        Aggregate individual question scores into total score.
        
        FLAKY POINT #4: No atomic operation, no ordering guarantee.
        The order of aggregation varies with completion order.
        """
        breakdown = {}
        total_score = 0
        max_total = 0
        errors = []
        
        # FLAKY: Accumulate in order of task completion (not submission order)
        for idx, score_result in enumerate(scores):
            if isinstance(score_result, Exception):
                errors.append(str(score_result))
                logger.warning(f"[{submission_id}] Score error at index {idx}: {score_result}")
                continue
            
            question_id = score_result.get("question_id")
            score = score_result.get("score", 0)
            max_score = score_result.get("max_score", 10)
            
            # FLAKY: Update without locking - other tasks may be updating simultaneously
            breakdown[question_id] = {
                "score": score,
                "max_score": max_score,
                "timestamp": score_result.get("timestamp"),
            }
            total_score += score
            max_total += max_score
        
        result = {
            "submission_id": submission_id,
            "total_score": total_score,
            "max_score": max_total,
            "percentage": (total_score / max_total * 100) if max_total > 0 else 0,
            "breakdown": breakdown,
            "errors": errors,
            "graded_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(
            f"[{submission_id}] Grade aggregated: total={total_score}/{max_total} "
            f"({result['percentage']:.1f}%)"
        )
        return result


async def grade_submission_flaky(
    submission: Dict[str, Any],
    scorer_registry
) -> Dict[str, Any]:
    """
    Convenience function to grade a submission using the flaky service.
    """
    service = FlakyGradingService(scorer_registry)
    return await service.grade_submission(submission)
