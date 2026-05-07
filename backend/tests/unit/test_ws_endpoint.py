"""Tests for WebSocket endpoint."""
import pytest

pytestmark = pytest.mark.unit


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_endpoint_exists(self):
        """Test websocket_endpoint function exists."""
        from app.api.v1.ws import websocket_endpoint

        assert websocket_endpoint is not None

    def test_ws_router_exists(self):
        """Test ws router exists."""
        from app.api.v1.ws import router

        assert router is not None
