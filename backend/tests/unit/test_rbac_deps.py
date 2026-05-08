"""Tests for RBAC dependency injection functions."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.api.deps import (
    get_current_user,
    require_role,
    require_permission,
    require_org_access,
    require_org_admin,
)
from app.core.rbac import Role, Permission


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = MagicMock()
    user.id = "user-123"
    user.org_id = "org-456"
    user.role = "member"
    return user


def test_require_role_passes_for_matching_role(mock_user):
    """require_role passes when user has required role."""
    mock_user.role = "member"
    with patch("app.api.deps.get_current_user", return_value=mock_user):
        result = require_role("member")(mock_user)
        assert result.role == "member"


def test_require_role_raises_for_insufficient_role():
    """require_role raises HTTPException when role is insufficient."""
    mock_user = MagicMock()
    mock_user.role = "viewer"

    with pytest.raises(HTTPException) as exc_info:
        require_role("admin")(mock_user)

    assert exc_info.value.status_code == 403


def test_require_role_passes_for_higher_role():
    """require_role passes when user has higher role."""
    mock_user = MagicMock()
    mock_user.role = "admin"

    # admin should pass for member requirement
    result = require_role("member")(mock_user)
    assert result.role == "admin"


def test_require_permission_passes_when_role_has_permission():
    """require_permission passes when role has the permission."""
    mock_user = MagicMock()
    mock_user.role = "admin"

    result = require_permission("users:write")(mock_user)
    assert result.role == "admin"


def test_require_permission_raises_when_missing():
    """require_permission raises HTTPException when role lacks permission."""
    mock_user = MagicMock()
    mock_user.role = "viewer"

    with pytest.raises(HTTPException) as exc_info:
        require_permission("users:delete")(mock_user)

    assert exc_info.value.status_code == 403


def test_require_org_access_checks_org_id():
    """require_org_access passes when user's org_id matches."""
    mock_user = MagicMock()
    mock_user.org_id = "org-456"
    mock_user.role = "member"

    result = require_org_access("org-456")(mock_user)
    assert result.org_id == "org-456"


def test_require_org_access_raises_for_different_org():
    """require_org_access raises when org_id doesn't match."""
    mock_user = MagicMock()
    mock_user.org_id = "org-456"
    mock_user.role = "member"

    with pytest.raises(HTTPException) as exc_info:
        require_org_access("org-999")(mock_user)

    assert exc_info.value.status_code == 403


def test_admin_bypasses_org_restriction():
    """Admin role bypasses org_id check."""
    mock_user = MagicMock()
    mock_user.org_id = "org-456"
    mock_user.role = "admin"

    # Admin should pass org check for any org
    result = require_org_access("org-different")(mock_user)
    assert result.role == "admin"


def test_require_org_admin_checks_both_role_and_org():
    """require_org_admin passes only when user is admin AND in correct org."""
    # Non-admin should fail
    mock_user = MagicMock()
    mock_user.org_id = "org-456"
    mock_user.role = "member"

    with pytest.raises(HTTPException) as exc_info:
        require_org_admin("org-456")(mock_user)
    assert exc_info.value.status_code == 403

    # Admin but wrong org should fail
    mock_user.role = "admin"
    with pytest.raises(HTTPException) as exc_info:
        require_org_admin("org-999")(mock_user)
    assert exc_info.value.status_code == 403

    # Admin in correct org should pass
    mock_user.role = "admin"
    result = require_org_admin("org-456")(mock_user)
    assert result.role == "admin"
