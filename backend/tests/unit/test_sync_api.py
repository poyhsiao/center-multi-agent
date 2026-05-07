import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


class TestSyncAPI:
    """Tests for Client Sync API."""

    def test_sync_mcp_version_returns_updates(self):
        """Test GET /api/v1/sync/mcp returns available updates."""
        from app.main import create_app
        from app.api.deps import get_current_user, User

        app = create_app()

        # Mock authentication
        mock_user = User(
            user_id="test-user-123",
            tenant_id="test-tenant-456",
            device_id="test-device-789",
            role="member"
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        response = client.get("/api/v1/sync/mcp?version=1.2.0")

        assert response.status_code == 200
        data = response.json()
        assert "needs_update" in data

    def test_sync_settings_returns_full_config(self):
        """Test GET /api/v1/sync/settings returns full config."""
        from app.main import create_app
        from app.api.deps import get_current_user, User

        app = create_app()

        # Mock authentication
        mock_user = User(
            user_id="test-user-123",
            tenant_id="test-tenant-456",
            device_id="test-device-789",
            role="member"
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        response = client.get("/api/v1/sync/settings")

        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "settings" in data

    def test_update_settings_saves_config(self):
        """Test PUT /api/v1/sync/settings updates config."""
        from app.main import create_app
        from app.api.deps import get_current_user, User

        app = create_app()

        # Mock authentication
        mock_user = User(
            user_id="test-user-123",
            tenant_id="test-tenant-456",
            device_id="test-device-789",
            role="member"
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        response = client.put(
            "/api/v1/sync/settings",
            json={"theme": "dark", "language": "en"}
        )

        assert response.status_code == 200