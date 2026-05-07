import pytest
from unittest.mock import AsyncMock

pytestmark = pytest.mark.unit


class TestSSENotificationManager:
    """Tests for SSENotificationManager."""

    @pytest.fixture
    def manager(self):
        from app.core.notification import SSENotificationManager
        return SSENotificationManager()

    @pytest.mark.asyncio
    async def test_broadcast_knowledge_event(self, manager):
        """Test broadcasting knowledge event to connected clients."""
        # Create mock connection
        mock_connection = AsyncMock()
        mock_connection.send_json = AsyncMock()

        manager.add_connection("user-123", mock_connection)

        # Broadcast event
        await manager.broadcast(
            event_type="knowledge.approved",
            data={"knowledge_id": "test-id"}
        )

        # Verify connection received the event
        mock_connection.send_json.assert_called_once()

    def test_remove_connection(self, manager):
        """Test removing a connection."""
        mock_connection = AsyncMock()
        manager.add_connection("user-123", mock_connection)
        manager.remove_connection("user-123")
        assert "user-123" not in manager._connections

    @pytest.mark.asyncio
    async def test_user_connections_isolation(self, manager):
        """Test that user connections are isolated."""
        conn1 = AsyncMock()
        conn2 = AsyncMock()
        manager.add_connection("user-1", conn1)
        manager.add_connection("user-2", conn2)

        await manager.broadcast(
            event_type="knowledge.published",
            data={"knowledge_id": "test-id"}
        )

        conn1.send_json.assert_called_once()
        conn2.send_json.assert_called_once()