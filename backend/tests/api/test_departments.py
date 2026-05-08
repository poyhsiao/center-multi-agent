"""Department management API endpoint tests with RBAC."""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException, status

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


@pytest.fixture
def admin_user():
    """Admin user fixture."""
    return get_mock_user(Role.ADMIN)


@pytest.fixture
def member_user():
    """Member user fixture."""
    return get_mock_user(Role.MEMBER)


@pytest.fixture
def test_app(admin_user, member_user):
    """Create test app with department endpoints."""
    app = FastAPI()

    @app.get("/api/v1/departments/")
    async def list_departments(
        org_id: str,
        user: User = Depends(create_permission_dependency(Permission.DEPT_READ)),
    ):
        """List all departments in an organization."""
        return {"departments": [], "total": 0}

    @app.post("/api/v1/departments/", status_code=status.HTTP_201_CREATED)
    async def create_department(
        dept_data: dict,
        user: User = Depends(create_permission_dependency(Permission.DEPT_WRITE)),
    ):
        """Create a new department."""
        return {"id": "new-dept-123", "name": dept_data.get("name"), "org_id": dept_data.get("org_id")}

    @app.get("/api/v1/departments/{department_id}")
    async def get_department(
        department_id: str,
        user: User = Depends(create_permission_dependency(Permission.DEPT_READ)),
    ):
        """Get a specific department."""
        return {"id": department_id, "name": "Test Dept", "org_id": "org-123"}

    @app.patch("/api/v1/departments/{department_id}")
    async def update_department(
        department_id: str,
        dept_update: dict,
        user: User = Depends(create_permission_dependency(Permission.DEPT_WRITE)),
    ):
        """Update a department."""
        return {"id": department_id, "name": dept_update.get("name", "Updated"), "org_id": "org-123"}

    @app.delete("/api/v1/departments/{department_id}")
    async def delete_department(
        department_id: str,
        user: User = Depends(create_permission_dependency(Permission.DEPT_DELETE)),
    ):
        """Delete a department."""
        return {"id": department_id, "deleted": True}

    return app


def set_current_user(user):
    """Set the current user for the test."""
    global _current_user_override
    _current_user_override = user


def clear_current_user():
    """Clear the current user after test."""
    global _current_user_override
    _current_user_override = None


class TestCreateDepartment:
    """Tests for POST /api/v1/departments endpoint."""

    def test_create_department_requires_admin(self, test_app, member_user):
        """Non-admin cannot create departments - returns 403."""
        set_current_user(member_user)
        try:
            client = TestClient(test_app)
            response = client.post(
                "/api/v1/departments/",
                json={"name": "Engineering", "org_id": "org-123"},
            )
            assert response.status_code == 403
            assert "Permission denied" in response.json().get("detail", "")
        finally:
            clear_current_user()

    def test_create_department_as_admin_succeeds(self, test_app, admin_user):
        """Admin can create departments - returns 201."""
        set_current_user(admin_user)
        try:
            client = TestClient(test_app)
            response = client.post(
                "/api/v1/departments/",
                json={"name": "Engineering", "org_id": "org-123"},
            )
            assert response.status_code == 201
            assert response.json()["name"] == "Engineering"
        finally:
            clear_current_user()


class TestListDepartments:
    """Tests for GET /api/v1/departments endpoint."""

    def test_list_departments_member_can_read(self, test_app, member_user):
        """Member can list departments - has DEPT_READ permission."""
        # Verify member has DEPT_READ permission
        assert has_permission(Role.MEMBER, Permission.DEPT_READ)

        set_current_user(member_user)
        try:
            client = TestClient(test_app)
            response = client.get(
                "/api/v1/departments/",
                params={"org_id": "org-123"},
            )
            assert response.status_code == 200
            assert "departments" in response.json()
        finally:
            clear_current_user()


class TestDeleteDepartment:
    """Tests for DELETE /api/v1/departments/{id} endpoint."""

    def test_delete_department_requires_admin(self, test_app, member_user):
        """Non-admin cannot delete departments - returns 403."""
        # Verify member does NOT have DEPT_DELETE permission
        assert not has_permission(Role.MEMBER, Permission.DEPT_DELETE)

        set_current_user(member_user)
        try:
            client = TestClient(test_app)
            response = client.delete("/api/v1/departments/dept-123")
            assert response.status_code == 403
            assert "Permission denied" in response.json().get("detail", "")
        finally:
            clear_current_user()

    def test_delete_department_as_admin_succeeds(self, test_app, admin_user):
        """Admin can delete departments - has DEPT_DELETE permission."""
        # Verify admin has DEPT_DELETE permission
        assert has_permission(Role.ADMIN, Permission.DEPT_DELETE)

        set_current_user(admin_user)
        try:
            client = TestClient(test_app)
            response = client.delete("/api/v1/departments/dept-123")
            assert response.status_code == 200
        finally:
            clear_current_user()


class TestGetDepartment:
    """Tests for GET /api/v1/departments/{id} endpoint."""

    def test_get_department_member_can_read(self, test_app, member_user):
        """Member can get department details - has DEPT_READ permission."""
        set_current_user(member_user)
        try:
            client = TestClient(test_app)
            response = client.get("/api/v1/departments/dept-123")
            assert response.status_code == 200
            assert response.json()["id"] == "dept-123"
        finally:
            clear_current_user()


class TestUpdateDepartment:
    """Tests for PATCH /api/v1/departments/{id} endpoint."""

    def test_update_department_requires_admin(self, test_app, member_user):
        """Non-admin cannot update departments - returns 403."""
        set_current_user(member_user)
        try:
            client = TestClient(test_app)
            response = client.patch(
                "/api/v1/departments/dept-123",
                json={"name": "Updated Engineering"},
            )
            assert response.status_code == 403
            assert "Permission denied" in response.json().get("detail", "")
        finally:
            clear_current_user()

    def test_update_department_as_admin_succeeds(self, test_app, admin_user):
        """Admin can update departments - has DEPT_WRITE permission."""
        set_current_user(admin_user)
        try:
            client = TestClient(test_app)
            response = client.patch(
                "/api/v1/departments/dept-123",
                json={"name": "Updated Engineering"},
            )
            assert response.status_code == 200
            assert response.json()["name"] == "Updated Engineering"
        finally:
            clear_current_user()
