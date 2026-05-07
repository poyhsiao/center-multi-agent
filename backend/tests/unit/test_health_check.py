"""Tests for enhanced health check endpoint."""
import pytest

pytestmark = pytest.mark.unit


class TestHealthCheck:
    """Tests for enhanced health check endpoint."""

    def test_health_check_returns_status(self):
        """Test health check returns basic status."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
