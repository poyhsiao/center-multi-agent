import pytest

pytestmark = pytest.mark.unit


class TestSecurityHeaders:
    """Tests for security headers."""

    def test_security_headers_in_response(self):
        """Test that security headers are added to response."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert "X-Request-ID" in response.headers