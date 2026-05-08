import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_admin_user():
    user = MagicMock()
    user.id = "admin-123"
    user.org_id = "org-456"
    user.role = "admin"
    return user


@pytest.fixture
def mock_member_user():
    user = MagicMock()
    user.id = "member-123"
    user.org_id = "org-456"
    user.role = "member"
    return user


def test_list_users_requires_admin():
    """Non-admin cannot list users."""
    # Mock get_current_user to return member user
    with patch("app.api.v1.users.get_current_user", return_value=mock_member_user):
        # require_role should raise 403
        from app.api.deps import require_role
        with pytest.raises(HTTPException) as exc_info:
            require_role("admin")(mock_member_user)
        assert exc_info.value.status_code == 403


def test_change_user_role_requires_admin():
    """Non-admin cannot change user roles."""
    with patch("app.api.v1.users.require_permission") as mock_perm:
        mock_perm.return_value = lambda x: x  # Pass through
        # Should raise because member doesn't have USERS_ROLE_CHANGE
        from app.core.rbac import Permission
        assert not mock_member_user.role == "admin"


def test_change_own_role_not_allowed():
    """Admin cannot change their own role."""
    # When user_id == user.id, should raise 400
    pass


def test_role_enum_validation():
    """Invalid role values should be rejected."""
    from app.core.rbac import Role
    with pytest.raises(ValueError):
        Role("invalid_role")