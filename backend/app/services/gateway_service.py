"""Gateway Service - Model Router with failover and cost tracking."""

from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    """Task classification types."""

    COMPLEX_REASONING = "complex_reasoning"
    GENERAL = "general"
    CREATIVE = "creative"
    BATCH = "batch"


class CostTier(str, Enum):
    """Cost tiers for model selection."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Failover chains by task type
_FAILOVER_CHAINS: dict[TaskType, list[str]] = {
    TaskType.COMPLEX_REASONING: ["gpt-4o", "claude-3.5-sonnet"],
    TaskType.GENERAL: ["gpt-4o-mini", "gemini-2.0-flash"],
    TaskType.CREATIVE: ["claude-3.5-sonnet", "gpt-4o"],
    TaskType.BATCH: ["gemini-2.0-flash", "claude-3-haiku"],
}


@dataclass
class CostMetrics:
    """Track cost and latency metrics."""

    total_cost: float = 0.0
    total_requests: int = 0
    total_latency_ms: int = 0


class ModelRouter:
    """Route tasks to appropriate models with failover support."""

    def select_model(self, task_type: TaskType) -> str:
        """
        Select the primary model for a task type.

        Args:
            task_type: Classification of the task

        Returns:
            Model identifier string
        """
        chain = self.get_failover_chain(task_type)
        return chain[0] if chain else ""

    def get_failover_chain(self, task_type: TaskType) -> list[str]:
        """
        Get the failover chain for a task type.

        Args:
            task_type: Classification of the task

        Returns:
            List of model identifiers in failover order
        """
        return _FAILOVER_CHAINS.get(task_type, []).copy()

    def track_cost(
        self, metrics: CostMetrics, model: str, cost: float, latency_ms: int
    ) -> None:
        """
        Track cost and latency for a model invocation.

        Args:
            metrics: Metrics object to update
            model: Model identifier
            cost: Cost in USD
            latency_ms: Latency in milliseconds
        """
        metrics.total_cost += cost
        metrics.total_requests += 1
        metrics.total_latency_ms += latency_ms


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embedding: list[float]
    model: str = "text-embedding-3-small"


class EmbeddingService:
    """Generate embeddings for vector search."""

    DIMENSION = 1536

    async def generate(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Input text to embed

        Returns:
            1536-dimensional embedding vector
        """
        # Deterministic mock for testing consistency
        import hashlib
        import random

        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        seed = hash_value % (2**32)

        rng = random.Random(seed)
        embedding = [rng.uniform(-1, 1) for _ in range(self.DIMENSION)]

        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding
