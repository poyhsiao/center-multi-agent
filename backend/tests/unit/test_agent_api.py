import pytest
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.unit


class TestAgentAPI:
    """Tests for Agent API endpoints."""

    def test_create_task_returns_task_id(self):
        """Test POST /api/v1/agent/tasks creates task and returns ID."""
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.api.deps import get_current_user, User

        app = create_app()

        # Mock authentication
        mock_user = User(
            id="test-user-123",
            tenant_id="test-tenant-456",
            device_id="test-device-789",
            role="member"
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        response = client.post(
            "/api/v1/agent/tasks",
            json={"task_type": "general", "input": "test input"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"

    def test_sse_endpoint_returns_event_stream(self):
        """Test GET /api/v1/agent/events returns SSE stream."""
        from fastapi.testclient import TestClient
        from app.main import create_app
        from app.api.deps import get_current_user, User

        app = create_app()

        # Mock authentication
        mock_user = User(
            id="test-user-123",
            tenant_id="test-tenant-456",
            device_id="test-device-789",
            role="member"
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        response = client.get("/api/v1/agent/events")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
