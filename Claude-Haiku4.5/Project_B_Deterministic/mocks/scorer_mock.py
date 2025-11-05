"""
Scorer mock service for Project B - same interface as Project A
Used to validate deterministic behavior under identical conditions.
"""
import asyncio
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ScorerMock:
    """Mock external scorer service with configurable latency and failure behavior."""
    
    def __init__(
        self,
        question_id: str,
        mean_latency_ms: float = 50,
        latency_variance_ms: float = 30,
        failure_rate: float = 0.05,
        retry_delay_ms: float = 100,
        seed: Optional[int] = None,
    ):
        """
        Initialize a scorer mock.
        
        Args:
            question_id: ID of the question this scorer handles
            mean_latency_ms: Mean response latency in milliseconds
            latency_variance_ms: Variance in latency (std dev)
            failure_rate: Probability of scoring failure (0-1)
            retry_delay_ms: Delay added on retry
            seed: Random seed for reproducibility
        """
        self.question_id = question_id
        self.mean_latency_ms = mean_latency_ms
        self.latency_variance_ms = latency_variance_ms
        self.failure_rate = failure_rate
        self.retry_delay_ms = retry_delay_ms
        self.seed = seed
        self.call_count = 0
        self.failure_count = 0
        
        if seed is not None:
            random.seed(seed)
    
    async def score(self, answer: str, retry_attempt: int = 0, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Score an answer with simulated latency and potential failure.
        
        Args:
            answer: The student's answer to score
            retry_attempt: Which retry attempt this is
            idempotency_key: Key for idempotent retries (used in Project B)
            
        Returns:
            Dict with score, feedback, and metadata
        """
        self.call_count += 1
        call_id = f"{self.question_id}_{self.call_count}"
        
        # Simulate variable latency
        latency = max(10, random.gauss(self.mean_latency_ms, self.latency_variance_ms))
        await asyncio.sleep(latency / 1000.0)
        
        # Simulate intermittent failures
        if random.random() < self.failure_rate and retry_attempt == 0:
            self.failure_count += 1
            logger.info(f"[{call_id}] FAILURE on call {self.call_count}, answer={answer}")
            raise Exception(f"Scorer service temporarily unavailable for {self.question_id}")
        
        # Score the answer
        score = self._compute_score(answer)
        
        result = {
            "question_id": self.question_id,
            "answer": answer,
            "score": score,
            "max_score": 10,
            "timestamp": datetime.utcnow().isoformat(),
            "call_id": call_id,
            "retry_attempt": retry_attempt,
            "latency_ms": latency,
            "idempotency_key": idempotency_key,
        }
        
        logger.info(f"[{call_id}] SCORED: question={self.question_id}, score={score}, latency_ms={latency:.1f}, idempotency_key={idempotency_key}")
        return result
    
    def _compute_score(self, answer: str) -> int:
        """Simple scoring heuristic: length-based (demo purposes)."""
        if not answer or len(answer.strip()) == 0:
            return 0
        return min(10, len(answer.strip()) // 2)


class ScorerRegistry:
    """Manages a collection of scorer mocks for different questions."""
    
    def __init__(self, seed: Optional[int] = None):
        self.scorers: Dict[str, ScorerMock] = {}
        self.seed = seed
    
    def register_scorer(
        self,
        question_id: str,
        mean_latency_ms: float = 50,
        latency_variance_ms: float = 30,
        failure_rate: float = 0.05,
    ) -> ScorerMock:
        """Register a new scorer for a question."""
        scorer_seed = None
        if self.seed is not None:
            scorer_seed = self.seed + hash(question_id) % 1000
        
        scorer = ScorerMock(
            question_id=question_id,
            mean_latency_ms=mean_latency_ms,
            latency_variance_ms=latency_variance_ms,
            failure_rate=failure_rate,
            seed=scorer_seed,
        )
        self.scorers[question_id] = scorer
        return scorer
    
    async def score_answer(
        self,
        question_id: str,
        answer: str,
        retry_attempt: int = 0,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Score an answer using the registered scorer for that question."""
        if question_id not in self.scorers:
            raise ValueError(f"No scorer registered for question {question_id}")
        
        return await self.scorers[question_id].score(answer, retry_attempt, idempotency_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics across all scorers."""
        return {
            "scorers": {
                qid: {
                    "call_count": scorer.call_count,
                    "failure_count": scorer.failure_count,
                }
                for qid, scorer in self.scorers.items()
            }
        }
