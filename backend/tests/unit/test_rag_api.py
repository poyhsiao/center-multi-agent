import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


class TestRAGAPI:
    """Tests for RAG query API."""

    def test_query_returns_context(self):
        """Test POST /api/v1/rag/query returns relevant context."""
        from app.main import create_app
        from app.api.deps import get_current_user, User

        app = create_app()

        # Mock authentication
        mock_user = User(
            id="test-user-123",
            org_id="test-tenant-456",
            role="member"
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        client = TestClient(app)

        response = client.post(
            "/api/v1/rag/query",
            json={"query": "What is the policy for PTO?", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data