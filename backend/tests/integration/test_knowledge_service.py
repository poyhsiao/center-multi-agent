"""Integration tests for Knowledge Service - Approval workflow and SSE events."""

import pytest
from unittest.mock import AsyncMock, patch


class TestApprovalWorkflow:
    """Test complete approval workflow."""

    def test_full_knowledge_lifecycle(self):
        """Test knowledge through complete lifecycle: draft → review → approved → published."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        # Draft
        knowledge = Knowledge(title="Test Knowledge", content="Test content")
        assert knowledge.status == KnowledgeStatus.DRAFT

        # Submit for review
        knowledge.submit_for_review()
        assert knowledge.status == KnowledgeStatus.PENDING_REVIEW

        # Approve
        knowledge.approve()
        assert knowledge.status == KnowledgeStatus.APPROVED

        # Publish
        knowledge.publish()
        assert knowledge.status == KnowledgeStatus.PUBLISHED

    def test_rejection_workflow(self):
        """Test knowledge rejection and revision workflow."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        # Draft
        knowledge = Knowledge(title="Rejected Knowledge", content="Needs improvement")
        knowledge.submit_for_review()

        # Reject
        knowledge.reject(reason="Content needs more detail")
        assert knowledge.status == KnowledgeStatus.REJECTED
        assert knowledge.rejection_reason == "Content needs more detail"

        # Revise
        knowledge.revise()
        assert knowledge.status == KnowledgeStatus.DRAFT
        assert knowledge.rejection_reason is None

    def test_rejected_to_approved_flow(self):
        """Test knowledge can be re-submitted and eventually approved."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Revised Knowledge", content="Improved content")
        knowledge.submit_for_review()
        knowledge.reject(reason="Initial rejection")

        # Re-submit
        knowledge.revise()
        knowledge.submit_for_review()
        knowledge.approve()
        knowledge.publish()

        assert knowledge.status == KnowledgeStatus.PUBLISHED


class TestSSENotificationEvents:
    """Test SSE notification events for knowledge lifecycle."""

    def test_submitted_event_structure(self):
        """knowledge.submitted event should have correct structure."""
        from app.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        event = service.create_submitted_event(knowledge_id="kb-12345")

        assert event.event_type == "knowledge.submitted"
        assert "knowledge_id" in event.data
        assert event.data["knowledge_id"] == "kb-12345"

    def test_approved_event_structure(self):
        """knowledge.approved event should have correct structure."""
        from app.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        event = service.create_approved_event(knowledge_id="kb-12345")

        assert event.event_type == "knowledge.approved"
        assert "knowledge_id" in event.data

    def test_rejected_event_includes_reason(self):
        """knowledge.rejected event should include rejection reason."""
        from app.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        event = service.create_rejected_event(
            knowledge_id="kb-12345", reason="Inaccurate information"
        )

        assert event.event_type == "knowledge.rejected"
        assert event.data["reason"] == "Inaccurate information"

    def test_published_event_structure(self):
        """knowledge.published event should have correct structure."""
        from app.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        event = service.create_published_event(knowledge_id="kb-12345")

        assert event.event_type == "knowledge.published"
        assert "knowledge_id" in event.data

    def test_all_events_are_sse_event_dataclasses(self):
        """All knowledge events should be SSEEvent instances."""
        from app.services.knowledge_service import KnowledgeService, SSEEvent

        service = KnowledgeService()

        submitted = service.create_submitted_event("kb-1")
        approved = service.create_approved_event("kb-2")
        rejected = service.create_rejected_event("kb-3", "reason")
        published = service.create_published_event("kb-4")

        assert isinstance(submitted, SSEEvent)
        assert isinstance(approved, SSEEvent)
        assert isinstance(rejected, SSEEvent)
        assert isinstance(published, SSEEvent)


class TestRAGPipelineIntegration:
    """Test RAG pipeline with knowledge chunks."""

    @pytest.mark.asyncio
    async def test_context_assembly_with_multiple_sources(self):
        """Context should combine multiple knowledge sources."""
        from app.services.knowledge_service import RAGPipeline, KnowledgeChunk

        pipeline = RAGPipeline()
        chunks = [
            KnowledgeChunk(
                id="chunk-1",
                content="Python supports multiple programming paradigms.",
                metadata={"source": "python-docs", "page": 1},
            ),
            KnowledgeChunk(
                id="chunk-2",
                content="JavaScript is primarily used for web development.",
                metadata={"source": "js-docs", "page": 1},
            ),
            KnowledgeChunk(
                id="chunk-3",
                content="Go excels at concurrent programming.",
                metadata={"source": "go-docs", "page": 1},
            ),
        ]

        context = await pipeline.assemble_context(chunks, max_chunks=3)

        assert "Python" in context
        assert "JavaScript" in context
        assert "Go" in context

    @pytest.mark.asyncio
    async def test_context_respects_max_chunks_limit(self):
        """Context assembly should limit to max_chunks."""
        from app.services.knowledge_service import RAGPipeline, KnowledgeChunk

        pipeline = RAGPipeline()
        chunks = [
            KnowledgeChunk(id=f"chunk-{i}", content=f"Content from chunk {i}", metadata={})
            for i in range(10)
        ]

        # Request only 3 chunks
        context = await pipeline.assemble_context(chunks, max_chunks=3)

        # Should contain exactly 3 chunks
        assert "Content from chunk 0" in context
        assert "Content from chunk 1" in context
        assert "Content from chunk 2" in context
        assert "Content from chunk 3" not in context

    @pytest.mark.asyncio
    async def test_empty_chunks_returns_empty_context(self):
        """Empty chunks list should return empty context."""
        from app.services.knowledge_service import RAGPipeline, KnowledgeChunk

        pipeline = RAGPipeline()
        chunks: list[KnowledgeChunk] = []

        context = await pipeline.assemble_context(chunks, max_chunks=5)

        assert context == ""


class TestStateMachineInvalidTransitions:
    """Test invalid state transitions are rejected."""

    def test_cannot_skip_review(self):
        """Cannot approve directly from draft."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")

        with pytest.raises(ValueError) as exc_info:
            knowledge.approve()
        assert "Invalid transition" in str(exc_info.value)

    def test_cannot_publish_from_draft(self):
        """Cannot publish directly from draft."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")

        with pytest.raises(ValueError) as exc_info:
            knowledge.publish()
        assert "Invalid transition" in str(exc_info.value)

    def test_cannot_reject_from_approved(self):
        """Cannot reject already approved knowledge."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.approve()

        with pytest.raises(ValueError) as exc_info:
            knowledge.reject(reason="Too late")
        assert "Invalid transition" in str(exc_info.value)

    def test_published_is_terminal_no_transitions(self):
        """Published knowledge cannot be changed."""
        from app.services.knowledge_service import Knowledge, KnowledgeStatus

        knowledge = Knowledge(title="Test", content="Test content")
        knowledge.submit_for_review()
        knowledge.approve()
        knowledge.publish()

        with pytest.raises(ValueError):
            knowledge.submit_for_review()

        with pytest.raises(ValueError):
            knowledge.approve()

        with pytest.raises(ValueError):
            knowledge.publish()
