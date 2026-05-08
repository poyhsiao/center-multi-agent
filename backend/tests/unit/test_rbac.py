# backend/tests/unit/test_rbac.py
import pytest
from app.core.rbac import (
    Role,
    Permission,
    has_permission,
    is_role_or_higher,
    ADMIN,
    MEMBER,
    VIEWER,
    PERMISSIONS,
    ROLE_HIERARCHY,
)

def test_role_constants_defined():
    """Verify role constants are defined."""
    assert ADMIN == "admin"
    assert MEMBER == "member"
    assert VIEWER == "viewer"

def test_permission_constants_defined():
    """Verify permission constants exist in the role permission sets."""
    all_permissions = set()
    for perms in PERMISSIONS.values():
        all_permissions.update(perms)
    assert Permission.USERS_READ in all_permissions
    assert Permission.USERS_WRITE in all_permissions
    assert Permission.DEPT_READ in all_permissions
    assert Permission.DEPT_WRITE in all_permissions

def test_admin_has_all_permissions():
    """Admin role should have all permissions."""
    admin_perms = PERMISSIONS[ADMIN]
    assert Permission.USERS_READ in admin_perms
    assert Permission.USERS_WRITE in admin_perms
    assert Permission.DEPT_READ in admin_perms
    assert Permission.DEPT_WRITE in admin_perms

def test_member_permissions_subset_of_admin():
    """Member has fewer permissions than admin."""
    member_perms = PERMISSIONS[MEMBER]
    admin_perms = PERMISSIONS[ADMIN]
    assert member_perms.issubset(admin_perms)

def test_viewer_has_read_only_permissions():
    """Viewer should have read-only permissions."""
    viewer_perms = PERMISSIONS[VIEWER]
    assert Permission.USERS_READ in viewer_perms
    assert Permission.USERS_WRITE not in viewer_perms

def test_is_role_or_higher():
    """Role hierarchy check works correctly."""
    assert is_role_or_higher(ADMIN, ADMIN) is True
    assert is_role_or_higher(ADMIN, MEMBER) is True
    assert is_role_or_higher(MEMBER, VIEWER) is True
    assert is_role_or_higher(MEMBER, ADMIN) is False
    assert is_role_or_higher(VIEWER, ADMIN) is False

def test_has_permission():
    """Permission check works correctly."""
    assert has_permission(ADMIN, Permission.USERS_WRITE) is True
    assert has_permission(MEMBER, Permission.USERS_READ) is True
    assert has_permission(VIEWER, Permission.USERS_WRITE) is False