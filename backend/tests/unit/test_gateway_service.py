"""Unit tests for Gateway Service - Model Router and Failover."""

import pytest
from dataclasses import dataclass


class TaskType:
    COMPLEX_REASONING = "complex_reasoning"
    GENERAL = "general"
    CREATIVE = "creative"
    BATCH = "batch"


class TestModelRouterSelection:
    """Test model router selection logic."""

    def test_select_model_for_complex_reasoning(self):
        """Router should select GPT-4o for complex reasoning tasks."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        selected = router.select_model(TaskType.COMPLEX_REASONING)

        assert selected == "gpt-4o"

    def test_select_model_for_general_tasks(self):
        """Router should select GPT-4o-mini for general tasks."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        selected = router.select_model(TaskType.GENERAL)

        assert selected == "gpt-4o-mini"

    def test_select_model_for_creative_tasks(self):
        """Router should select Claude 3.5 Sonnet for creative tasks."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        selected = router.select_model(TaskType.CREATIVE)

        assert selected == "claude-3.5-sonnet"

    def test_select_model_for_batch_tasks(self):
        """Router should select Gemini 2.0 Flash for batch tasks."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        selected = router.select_model(TaskType.BATCH)

        assert selected == "gemini-2.0-flash"

    def test_task_type_mapping_complete(self):
        """All task types should have valid model mappings."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        task_types = [
            TaskType.COMPLEX_REASONING,
            TaskType.GENERAL,
            TaskType.CREATIVE,
            TaskType.BATCH,
        ]

        for task_type in task_types:
            selected = router.select_model(task_type)
            assert selected is not None, f"No model selected for {task_type}"
            assert isinstance(selected, str), f"Invalid model type for {task_type}"


class TestModelFailoverChain:
    """Test failover chain logic."""

    def test_complex_reasoning_failover_chain(self):
        """Complex reasoning should failover: GPT-4o → Claude 3.5 Sonnet."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        chain = router.get_failover_chain(TaskType.COMPLEX_REASONING)

        assert chain == ["gpt-4o", "claude-3.5-sonnet"]

    def test_general_failover_chain(self):
        """General tasks should failover: GPT-4o-mini → Gemini 2.0 Flash."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        chain = router.get_failover_chain(TaskType.GENERAL)

        assert chain == ["gpt-4o-mini", "gemini-2.0-flash"]

    def test_creative_failover_chain(self):
        """Creative tasks should failover: Claude 3.5 Sonnet → GPT-4o."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        chain = router.get_failover_chain(TaskType.CREATIVE)

        assert chain == ["claude-3.5-sonnet", "gpt-4o"]

    def test_batch_failover_chain(self):
        """Batch tasks should failover: Gemini 2.0 Flash → Claude 3 Haiku."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        chain = router.get_failover_chain(TaskType.BATCH)

        assert chain == ["gemini-2.0-flash", "claude-3-haiku"]

    def test_failover_chain_returns_list(self):
        """Failover chain should return a list with primary and backup."""
        from app.services.gateway_service import ModelRouter

        router = ModelRouter()
        chain = router.get_failover_chain(TaskType.COMPLEX_REASONING)

        assert isinstance(chain, list)
        assert len(chain) == 2
        assert chain[0] != chain[1]


class TestCostTracking:
    """Test cost and latency tracking."""

    def test_track_cost_updates_metrics(self):
        """Tracking cost should update the metrics store."""
        from app.services.gateway_service import ModelRouter, CostMetrics

        router = ModelRouter()
        metrics = CostMetrics()

        router.track_cost(metrics, "gpt-4o", cost=0.03, latency_ms=1500)

        assert metrics.total_cost > 0
        assert metrics.total_requests == 1

    def test_metrics_initial_state(self):
        """Metrics should start with zero values."""
        from app.services.gateway_service import CostMetrics

        metrics = CostMetrics()

        assert metrics.total_cost == 0
        assert metrics.total_requests == 0
        assert metrics.total_latency_ms == 0

    def test_metrics_accumulate(self):
        """Multiple cost tracks should accumulate correctly."""
        from app.services.gateway_service import ModelRouter, CostMetrics

        router = ModelRouter()
        metrics = CostMetrics()

        router.track_cost(metrics, "gpt-4o", cost=0.03, latency_ms=1500)
        router.track_cost(metrics, "gpt-4o-mini", cost=0.001, latency_ms=500)

        assert metrics.total_cost == 0.031
        assert metrics.total_requests == 2


class TestEmbeddingGeneration:
    """Test embedding generation consistency."""

    @pytest.mark.asyncio
    async def test_generate_embedding_consistency(self):
        """Same text should generate consistent embeddings."""
        from app.services.gateway_service import EmbeddingService

        service = EmbeddingService()
        text = "This is a test document for embedding."

        embedding1 = await service.generate(text)
        embedding2 = await service.generate(text)

        assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_embedding_dimension(self):
        """Embedding should have correct dimension (1536 for text-embedding-3-small)."""
        from app.services.gateway_service import EmbeddingService

        service = EmbeddingService()
        embedding = await service.generate("Test document")

        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embedding_is_list_of_floats(self):
        """Embedding should be a list of floats."""
        from app.services.gateway_service import EmbeddingService

        service = EmbeddingService()
        embedding = await service.generate("Test document")

        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)
