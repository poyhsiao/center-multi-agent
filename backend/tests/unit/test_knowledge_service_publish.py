import pytest
from unittest.mock import MagicMock, AsyncMock

pytestmark = pytest.mark.unit


class TestKnowledgePublishing:
    """Tests for knowledge publishing background task."""

    @pytest.mark.asyncio
    async def test_publish_background_generates_embeddings(self):
        """Test publish_background generates vector embeddings."""
        from app.services.knowledge_service import KnowledgeService, KnowledgeStatus
        from app.services.gateway_service import EmbeddingService

        service = KnowledgeService()

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.find_by_id = AsyncMock(return_value=MagicMock(
            id="test-kb-id",
            status=KnowledgeStatus.APPROVED
        ))
        mock_repo.get_chunks = AsyncMock(return_value=[
            MagicMock(id="chunk-1", content="Test content"),
            MagicMock(id="chunk-2", content="More content")
        ])
        mock_repo.update_chunk_embedding = AsyncMock()
        mock_repo.update_status = AsyncMock()

        service.repository = mock_repo

        # Mock embedding service
        mock_embedding_service = MagicMock()
        mock_embedding_service.generate = AsyncMock(return_value=[0.1] * 1536)
        service._embedding_service = mock_embedding_service

        # Run publish_background
        await service.publish_background("test-kb-id")

        # Verify embeddings were generated for each chunk
        assert mock_embedding_service.generate.call_count == 2