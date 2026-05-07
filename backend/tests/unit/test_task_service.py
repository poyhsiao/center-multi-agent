import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.unit


class TestBackgroundTaskService:
    """Tests for BackgroundTaskService."""

    def test_schedule_knowledge_publish(self):
        """Test scheduling knowledge publish as background task."""
        from app.services.task_service import BackgroundTaskService

        service = BackgroundTaskService()
        task_id = service.schedule_knowledge_publish(
            knowledge_id="test-id",
            user_id="user-123"
        )
        assert task_id is not None
        assert len(task_id) > 0

    def test_schedule_notification(self):
        """Test scheduling notification task."""
        from app.services.task_service import BackgroundTaskService

        service = BackgroundTaskService()
        task_id = service.schedule_notification(
            user_id="user-123",
            event_type="knowledge.approved",
            payload={"knowledge_id": "test-id"}
        )
        assert task_id is not None
