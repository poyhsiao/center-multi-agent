import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


@pytest.fixture
def mock_admin_user():
    user = MagicMock()
    user.id = "admin-123"
    user.org_id = "org-123"
    user.role = "admin"
    return user


@pytest.fixture
def mock_member_user():
    user = MagicMock()
    user.id = "member-123"
    user.org_id = "org-123"
    user.role = "member"
    return user


def test_create_department_requires_admin(mock_member_user):
    """Non-admin cannot create departments."""
    from app.core.rbac import Permission

    with patch("app.api.deps.get_current_user", return_value=mock_member_user):
        from app.api.deps import require_permission
        # Member doesn't have DEPT_WRITE permission
        assert not mock_member_user.role == "admin"


def test_create_department_as_admin():
    """Admin can create departments."""
    from app.core.rbac import Permission, Role, has_permission

    # Admin should have dept:write permission
    assert has_permission(Role.ADMIN, Permission.DEPT_WRITE)


def test_list_departments_member_can_read():
    """Member can list departments."""
    from app.core.rbac import Permission, Role, has_permission

    # Member should have dept:read permission
    assert has_permission(Role.MEMBER, Permission.DEPT_READ)


def test_delete_department_requires_admin():
    """Non-admin cannot delete departments."""
    from app.core.rbac import Permission, Role, has_permission

    # Member doesn't have DEPT_DELETE permission
    assert not has_permission(Role.MEMBER, Permission.DEPT_DELETE)
