"""Knowledge Service - State machine and RAG pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class KnowledgeStatus(str, Enum):
    """Knowledge document status states."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


# Valid state transitions
_VALID_TRANSITIONS: dict[KnowledgeStatus, list[KnowledgeStatus]] = {
    KnowledgeStatus.DRAFT: [KnowledgeStatus.PENDING_REVIEW],
    KnowledgeStatus.PENDING_REVIEW: [
        KnowledgeStatus.APPROVED,
        KnowledgeStatus.REJECTED,
    ],
    KnowledgeStatus.APPROVED: [KnowledgeStatus.PUBLISHED],
    KnowledgeStatus.REJECTED: [KnowledgeStatus.DRAFT],
    KnowledgeStatus.PUBLISHED: [],  # Terminal state
}


@dataclass
class Knowledge:
    """Knowledge document with state machine."""

    title: str
    content: str
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    rejection_reason: str | None = None
    id: str | None = None

    def _transition(self, new_status: KnowledgeStatus) -> None:
        """Execute state transition with validation."""
        valid_targets = _VALID_TRANSITIONS.get(self.status, [])
        if new_status not in valid_targets:
            raise ValueError(
                f"Invalid transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status

    def submit_for_review(self) -> None:
        """Submit draft for review."""
        self._transition(KnowledgeStatus.PENDING_REVIEW)

    def approve(self) -> None:
        """Approve pending knowledge."""
        self._transition(KnowledgeStatus.APPROVED)

    def reject(self, reason: str) -> None:
        """Reject pending knowledge with reason."""
        self.rejection_reason = reason
        self._transition(KnowledgeStatus.REJECTED)

    def publish(self) -> None:
        """Publish approved knowledge."""
        self._transition(KnowledgeStatus.PUBLISHED)

    def revise(self) -> None:
        """Revise rejected knowledge back to draft."""
        self.rejection_reason = None
        self._transition(KnowledgeStatus.DRAFT)


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge content with vector embedding."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


@dataclass
class SSEEvent:
    """Server-Sent Event for knowledge notifications."""

    event_type: str
    data: dict[str, Any]


class KnowledgeService:
    """Knowledge management with SSE notifications."""

    def create_submitted_event(self, knowledge_id: str) -> SSEEvent:
        """Create event for knowledge submission."""
        return SSEEvent(
            event_type="knowledge.submitted",
            data={"knowledge_id": knowledge_id},
        )

    def create_approved_event(self, knowledge_id: str) -> SSEEvent:
        """Create event for knowledge approval."""
        return SSEEvent(
            event_type="knowledge.approved",
            data={"knowledge_id": knowledge_id},
        )

    def create_rejected_event(self, knowledge_id: str, reason: str) -> SSEEvent:
        """Create event for knowledge rejection."""
        return SSEEvent(
            event_type="knowledge.rejected",
            data={"knowledge_id": knowledge_id, "reason": reason},
        )

    def create_published_event(self, knowledge_id: str) -> SSEEvent:
        """Create event for knowledge publication."""
        return SSEEvent(
            event_type="knowledge.published",
            data={"knowledge_id": knowledge_id},
        )

    async def publish_background(self, knowledge_id: str) -> None:
        """Publish knowledge to vector database (background task).

        Generates embeddings for all chunks and updates them in the database.
        """
        # Generate embeddings for all chunks
        knowledge = await self.repository.find_by_id(knowledge_id)
        if not knowledge or knowledge.status != KnowledgeStatus.APPROVED:
            return

        chunks = await self.repository.get_chunks(knowledge_id)
        for chunk in chunks:
            # Use EmbeddingService to generate vector
            embedding = await self._embedding_service.generate(chunk.content)
            # Update chunk with embedding
            await self.repository.update_chunk_embedding(
                chunk.id, embedding
            )

        # Mark knowledge as published
        await self.repository.update_status(
            knowledge_id, KnowledgeStatus.PUBLISHED
        )


class RAGPipeline:
    """RAG pipeline for context assembly."""

    async def assemble_context(
        self, chunks: list[KnowledgeChunk], max_chunks: int = 5
    ) -> str:
        """
        Assemble context from knowledge chunks.

        Args:
            chunks: List of knowledge chunks
            max_chunks: Maximum number of chunks to include

        Returns:
            Assembled context string
        """
        selected = chunks[:max_chunks]
        context_parts = [chunk.content for chunk in selected]
        return "\n\n".join(context_parts)
