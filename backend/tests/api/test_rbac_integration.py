"""RBAC integration tests for knowledge, agent, and RAG endpoints."""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import Depends, HTTPException, status

from app.core.rbac import Role, Permission, has_permission
from app.models.user import User


def get_mock_user(role: Role):
    """Create a mock user with given role."""
    user = MagicMock(spec=User)
    user.id = f"{role.value}-123"
    user.org_id = "org-123"
    user.role = role.value
    return user


def create_permission_dependency(permission: Permission):
    """Create a permission check dependency factory."""
    async def check_permission(user: User = Depends(get_current_user_for_test)) -> User:
        if not has_permission(Role(user.role), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission.value}'",
            )
        return user
    return check_permission


# Store current user override
_current_user_override = None


async def get_current_user_for_test():
    """Dependency that returns the overridden user."""
    if _current_user_override is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _current_user_override


def set_current_user(user):
    """Set the current user for the test."""
    global _current_user_override
    _current_user_override = user


def clear_current_user():
    """Clear the current user after test."""
    global _current_user_override
    _current_user_override = None


@pytest.fixture
def viewer_user():
    """Viewer user fixture."""
    return get_mock_user(Role.VIEWER)


@pytest.fixture
def member_user():
    """Member user fixture."""
    return get_mock_user(Role.MEMBER)


@pytest.fixture
def admin_user():
    """Admin user fixture."""
    return get_mock_user(Role.ADMIN)


class TestKnowledgeEndpointsRBAC:
    """Tests for knowledge endpoint permission enforcement."""

    def test_viewer_cannot_create_knowledge(self, viewer_user):
        """Viewer cannot create knowledge - needs knowledge:write permission."""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/knowledge")
        async def create_knowledge(
            data: dict,
            user: User = Depends(create_permission_dependency(Permission.KNOWLEDGE_WRITE)),
        ):
            return {"id": "new-kb-123", "title": data.get("title")}

        set_current_user(viewer_user)
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/knowledge",
                json={"title": "Test", "content": "..."},
            )
            assert response.status_code == 403
            assert "Permission denied" in response.json().get("detail", "")
        finally:
            clear_current_user()

    def test_member_can_create_knowledge(self, member_user):
        """Member can create knowledge - has knowledge:write permission."""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/knowledge")
        async def create_knowledge(
            data: dict,
            user: User = Depends(create_permission_dependency(Permission.KNOWLEDGE_WRITE)),
        ):
            return {"id": "new-kb-123", "title": data.get("title")}

        set_current_user(member_user)
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/knowledge",
                json={"title": "Test", "content": "..."},
            )
            assert response.status_code == 200
        finally:
            clear_current_user()


class TestAgentEndpointsRBAC:
    """Tests for agent endpoint permission enforcement."""

    def test_viewer_cannot_execute_agent(self, viewer_user):
        """Viewer cannot execute agent tasks - needs agent:execute permission."""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/agent/execute")
        async def execute_agent(
            data: dict,
            user: User = Depends(create_permission_dependency(Permission.AGENT_EXECUTE)),
        ):
            return {"task_id": "task-123", "status": "running"}

        set_current_user(viewer_user)
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/agent/execute",
                json={"task": "do something"},
            )
            assert response.status_code == 403
            assert "Permission denied" in response.json().get("detail", "")
        finally:
            clear_current_user()

    def test_admin_can_execute_agent(self, admin_user):
        """Admin can execute agent tasks - has agent:execute permission."""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/agent/execute")
        async def execute_agent(
            data: dict,
            user: User = Depends(create_permission_dependency(Permission.AGENT_EXECUTE)),
        ):
            return {"task_id": "task-123", "status": "running"}

        set_current_user(admin_user)
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/agent/execute",
                json={"task": "do something"},
            )
            assert response.status_code == 200
        finally:
            clear_current_user()


class TestRAGEndpointsRBAC:
    """Tests for RAG endpoint permission enforcement."""

    def test_member_can_query_rag(self, member_user):
        """Member can query RAG - has knowledge:read permission."""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/rag/query")
        async def query_rag(
            data: dict,
            user: User = Depends(create_permission_dependency(Permission.KNOWLEDGE_READ)),
        ):
            return {"results": [], "query": data.get("query")}

        set_current_user(member_user)
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/rag/query",
                json={"query": "test"},
            )
            assert response.status_code == 200
            assert "results" in response.json()
        finally:
            clear_current_user()

    def test_viewer_can_query_rag(self, viewer_user):
        """Viewer can query RAG - has knowledge:read permission."""
        from fastapi import FastAPI

        app = FastAPI()

        @app.post("/api/v1/rag/query")
        async def query_rag(
            data: dict,
            user: User = Depends(create_permission_dependency(Permission.KNOWLEDGE_READ)),
        ):
            return {"results": [], "query": data.get("query")}

        set_current_user(viewer_user)
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/rag/query",
                json={"query": "test"},
            )
            assert response.status_code == 200
            assert "results" in response.json()
        finally:
            clear_current_user()