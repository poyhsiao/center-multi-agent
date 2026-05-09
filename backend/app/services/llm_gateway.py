"""LLM Gateway - Model Router with Failover."""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import structlog

logger = structlog.get_logger()


class TaskType(str, Enum):
    """Task classification for model selection."""
    COMPLEX_REASONING = "complex_reasoning"
    GENERAL = "general"
    CREATIVE = "creative"
    BATCH = "batch"


@dataclass
class ModelConfig:
    """Model configuration."""
    name: str
    provider: str
    cost_tier: str  # high, medium, low
    context_window: int
    supports_reasoning: bool = False


class LLMGateway:
    """Model router with failover support."""

    MODELS = {
        "gpt-4o": ModelConfig(
            name="gpt-4o",
            provider="openai",
            cost_tier="high",
            context_window=128000,
            supports_reasoning=True,
        ),
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            cost_tier="medium",
            context_window=128000,
            supports_reasoning=False,
        ),
        "claude-3-5-sonnet": ModelConfig(
            name="claude-3-5-sonnet",
            provider="anthropic",
            cost_tier="high",
            context_window=200000,
            supports_reasoning=True,
        ),
        "claude-3-haiku": ModelConfig(
            name="claude-3-haiku",
            provider="anthropic",
            cost_tier="low",
            context_window=200000,
            supports_reasoning=False,
        ),
        "gemini-2-0-flash": ModelConfig(
            name="gemini-2-0-flash",
            provider="google",
            cost_tier="low",
            context_window=1000000,
            supports_reasoning=False,
        ),
    }

    FAILOVER_CHAINS = {
        TaskType.COMPLEX_REASONING: ["gpt-4o", "claude-3-5-sonnet"],
        TaskType.GENERAL: ["gpt-4o-mini", "gemini-2-0-flash"],
        TaskType.CREATIVE: ["claude-3-5-sonnet", "gpt-4o"],
        TaskType.BATCH: ["gemini-2-0-flash", "claude-3-haiku"],
    }

    def __init__(self):
        self.logger = logger

    def select_model(self, task_type: TaskType) -> ModelConfig:
        """Select primary model for task type."""
        chain = self.FAILOVER_CHAINS.get(task_type, [TaskType.GENERAL])
        model_name = chain[0]
        return self.MODELS[model_name]

    def get_failover_chain(self, task_type: TaskType) -> list[ModelConfig]:
        """Get full failover chain for task type."""
        chain = self.FAILOVER_CHAINS.get(task_type, ["gpt-4o-mini"])
        return [self.MODELS[name] for name in chain]
