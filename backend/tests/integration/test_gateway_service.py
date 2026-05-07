"""Integration tests for Gateway Service - RAG query and failover."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestRAGQueryWithContext:
    """Test RAG query with full context assembly."""

    @pytest.mark.asyncio
    async def test_rag_query_pipeline_integration(self):
        """Full RAG query should work with context assembled."""
        from app.services.gateway_service import EmbeddingService
        from app.services.knowledge_service import RAGPipeline, KnowledgeChunk

        # Step 1: Generate embedding
        embedding_service = EmbeddingService()
        query = "What is Python programming language?"
        query_embedding = await embedding_service.generate(query)

        # Step 2: Create mock chunks (simulating vector search results)
        chunks = [
            KnowledgeChunk(
                id="chunk-1",
                content="Python is a high-level programming language.",
                metadata={"source": "python-docs"},
                embedding=query_embedding,
            ),
            KnowledgeChunk(
                id="chunk-2",
                content="Guido van Rossum created Python in 1991.",
                metadata={"source": "python-history"},
                embedding=query_embedding,
            ),
        ]

        # Step 3: Assemble context
        pipeline = RAGPipeline()
        context = await pipeline.assemble_context(chunks, max_chunks=2)

        # Assert
        assert "Python" in context
        assert "Guido" in context


class TestFailoverOnModelError:
    """Test failover chain when primary model fails."""

    def test_failover_chain_defined(self):
        """Failover chain should be defined for all task types."""
        from app.services.gateway_service import ModelRouter, TaskType

        router = ModelRouter()

        # complex_reasoning: GPT-4o → Claude 3.5 Sonnet
        chain = router.get_failover_chain(TaskType.COMPLEX_REASONING)
        assert len(chain) == 2
        assert chain[0] == "gpt-4o"
        assert chain[1] == "claude-3.5-sonnet"

        # general: GPT-4o-mini → Gemini 2.0 Flash
        chain = router.get_failover_chain(TaskType.GENERAL)
        assert len(chain) == 2
        assert chain[0] == "gpt-4o-mini"
        assert chain[1] == "gemini-2.0-flash"

        # creative: Claude 3.5 Sonnet → GPT-4o
        chain = router.get_failover_chain(TaskType.CREATIVE)
        assert len(chain) == 2
        assert chain[0] == "claude-3.5-sonnet"
        assert chain[1] == "gpt-4o"

        # batch: Gemini 2.0 Flash → Claude 3 Haiku
        chain = router.get_failover_chain(TaskType.BATCH)
        assert len(chain) == 2
        assert chain[0] == "gemini-2.0-flash"
        assert chain[1] == "claude-3-haiku"

    def test_model_selection_respects_cost_tier(self):
        """Router should select lowest cost model for task type."""
        from app.services.gateway_service import ModelRouter, TaskType

        router = ModelRouter()

        # Complex reasoning: GPT-4o (high cost tier) selected as primary
        selected = router.select_model(TaskType.COMPLEX_REASONING)
        assert selected == "gpt-4o"

        # General: GPT-4o-mini (medium cost tier) selected as primary
        selected = router.select_model(TaskType.GENERAL)
        assert selected == "gpt-4o-mini"


class TestEmbeddingGeneration:
    """Test embedding generation in integration context."""

    @pytest.mark.asyncio
    async def test_embedding_consistency_across_calls(self):
        """Same text should produce same embedding (deterministic)."""
        from app.services.gateway_service import EmbeddingService

        service = EmbeddingService()
        text = "Integration test for consistent embedding generation"

        embedding1 = await service.generate(text)
        embedding2 = await service.generate(text)
        embedding3 = await service.generate(text)

        assert embedding1 == embedding2 == embedding3

    @pytest.mark.asyncio
    async def test_embedding_different_texts_different_vectors(self):
        """Different texts should produce different embeddings."""
        from app.services.gateway_service import EmbeddingService

        service = EmbeddingService()

        embedding1 = await service.generate("Python programming")
        embedding2 = await service.generate("JavaScript programming")
        embedding3 = await service.generate("Go programming")

        # All embeddings should be different
        assert embedding1 != embedding2
        assert embedding2 != embedding3
        assert embedding1 != embedding3

    @pytest.mark.asyncio
    async def test_embedding_dimension_constant(self):
        """All embeddings should have 1536 dimensions."""
        from app.services.gateway_service import EmbeddingService

        service = EmbeddingService()

        texts = [
            "Short text",
            "A much longer piece of text that contains more content",
            "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor",
        ]

        for text in texts:
            embedding = await service.generate(text)
            assert len(embedding) == 1536
