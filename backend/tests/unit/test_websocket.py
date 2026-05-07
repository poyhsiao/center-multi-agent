import pytest
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.unit


class TestWebSocketManager:
    """Tests for WebSocketManager."""

    @pytest.fixture
    def manager(self):
        from app.core.websocket import WebSocketManager
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_creates_channel(self, manager):
        """Test that connecting creates a WebSocket channel."""
        websocket = AsyncMock()
        user_id = "user-123"

        await manager.connect(websocket, user_id)

        assert user_id in manager._channels

    @pytest.mark.asyncio
    async def test_disconnect_removes_channel(self, manager):
        """Test that disconnecting removes the WebSocket channel."""
        websocket = AsyncMock()
        user_id = "user-123"

        await manager.connect(websocket, user_id)
        await manager.disconnect(websocket, user_id)

        assert user_id not in manager._channels

    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, manager):
        """Test broadcasting message to specific user."""
        websocket = AsyncMock()
        user_id = "user-123"

        await manager.connect(websocket, user_id)
        await manager.broadcast_to_user(user_id, {"type": "notification", "data": "test"})

        websocket.send_json.assert_called_once_with({"type": "notification", "data": "test"})