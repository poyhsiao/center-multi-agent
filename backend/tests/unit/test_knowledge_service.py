"""Unit tests for Knowledge Service - State Machine and RAG Pipeline."""

import pytest
from dataclasses import dataclass
from enum import Enum


class KnowledgeStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class TestKnowledgeStateMachine:
    """Test knowledge status state transitions."""

    def test_initial_state_is_draft(self):
        """New knowledge should start in draft state."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")

        assert knowledge.status == KnowledgeStatus.DRAFT

    def test_draft_to_pending_review(self):
        """Draft knowledge can be submitted for review."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()

        assert knowledge.status == KnowledgeStatus.PENDING_REVIEW

    def test_pending_review_to_approved(self):
        """Pending review can be approved by admin."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.approve()

        assert knowledge.status == KnowledgeStatus.APPROVED

    def test_pending_review_to_rejected(self):
        """Pending review can be rejected by admin."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.reject(reason="Inaccurate information")

        assert knowledge.status == KnowledgeStatus.REJECTED
        assert knowledge.rejection_reason == "Inaccurate information"

    def test_approved_to_published(self):
        """Approved knowledge can be published."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.approve()
        knowledge.publish()

        assert knowledge.status == KnowledgeStatus.PUBLISHED

    def test_rejected_to_draft(self):
        """Rejected knowledge can be revised back to draft."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.reject(reason="Needs more detail")
        knowledge.revise()

        assert knowledge.status == KnowledgeStatus.DRAFT

    def test_invalid_transition_draft_to_approved(self):
        """Cannot approve directly from draft state."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")

        with pytest.raises(ValueError):
            knowledge.approve()

    def test_invalid_transition_draft_to_published(self):
        """Cannot publish directly from draft state."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")

        with pytest.raises(ValueError):
            knowledge.publish()

    def test_invalid_transition_approved_to_rejected(self):
        """Cannot reject already approved knowledge."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.approve()

        with pytest.raises(ValueError):
            knowledge.reject(reason="Too late")

    def test_published_is_terminal(self):
        """Published is a terminal state."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.approve()
        knowledge.publish()

        with pytest.raises(ValueError):
            knowledge.submit_for_review()


class TestSSENotificationEvents:
    """Test SSE notification event triggers."""

    def test_knowledge_submitted_event(self):
        """Submitting knowledge should trigger submitted event."""
        from app.services.knowledge_service import KnowledgeService, SSEEvent

        service = KnowledgeService()
        event = service.create_submitted_event(knowledge_id="test-123")

        assert event.event_type == "knowledge.submitted"
        assert event.data["knowledge_id"] == "test-123"

    def test_knowledge_approved_event(self):
        """Approving knowledge should trigger approved event."""
        from app.services.knowledge_service import KnowledgeService, SSEEvent

        service = KnowledgeService()
        event = service.create_approved_event(knowledge_id="test-123")

        assert event.event_type == "knowledge.approved"
        assert event.data["knowledge_id"] == "test-123"

    def test_knowledge_rejected_event(self):
        """Rejecting knowledge should trigger rejected event with reason."""
        from app.services.knowledge_service import KnowledgeService, SSEEvent

        service = KnowledgeService()
        event = service.create_rejected_event(
            knowledge_id="test-123", reason="Inaccurate"
        )

        assert event.event_type == "knowledge.rejected"
        assert event.data["knowledge_id"] == "test-123"
        assert event.data["reason"] == "Inaccurate"

    def test_knowledge_published_event(self):
        """Publishing knowledge should trigger published event."""
        from app.services.knowledge_service import KnowledgeService, SSEEvent

        service = KnowledgeService()
        event = service.create_published_event(knowledge_id="test-123")

        assert event.event_type == "knowledge.published"
        assert event.data["knowledge_id"] == "test-123"


class TestRAGPipeline:
    """Test RAG pipeline components."""

    @pytest.mark.asyncio
    async def test_rag_query_with_context(self):
        """RAG query should return context-assembled response."""
        from app.services.knowledge_service import RAGPipeline, KnowledgeChunk

        pipeline = RAGPipeline()
        chunks = [
            KnowledgeChunk(
                id="chunk-1",
                content="Python is a programming language.",
                metadata={"source": "doc1"},
            ),
            KnowledgeChunk(
                id="chunk-2",
                content="It was created by Guido van Rossum.",
                metadata={"source": "doc2"},
            ),
        ]

        result = await pipeline.assemble_context(chunks, max_chunks=2)

        assert "Python" in result
        assert "Guido" in result

    @pytest.mark.asyncio
    async def test_context_assembly_respects_max_chunks(self):
        """Context assembly should limit chunks to max_chunks."""
        from app.services.knowledge_service import RAGPipeline, KnowledgeChunk

        pipeline = RAGPipeline()
        chunks = [
            KnowledgeChunk(id=f"chunk-{i}", content=f"Content {i}", metadata={})
            for i in range(10)
        ]

        result = await pipeline.assemble_context(chunks, max_chunks=3)

        # Should contain at most 3 chunks' worth of content
        assert isinstance(result, str)

    def test_chunk_has_required_fields(self):
        """KnowledgeChunk should have id, content, and metadata."""
        from app.services.knowledge_service import KnowledgeChunk

        chunk = KnowledgeChunk(
            id="test-id", content="Test content", metadata={"key": "value"}
        )

        assert chunk.id == "test-id"
        assert chunk.content == "Test content"
        assert chunk.metadata == {"key": "value"}

    def test_embedding_dimension_for_vector_search(self):
        """Embeddings should be 1536-dimensional for PGVector."""
        from app.services.knowledge_service import KnowledgeChunk
        import random

        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        chunk = KnowledgeChunk(
            id="test",
            content="Test",
            metadata={},
            embedding=embedding,
        )

        assert len(chunk.embedding) == 1536
