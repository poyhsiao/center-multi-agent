"""RBAC Service - Business logic for role and permission management."""

from typing import Optional
from app.core.rbac import (
    Role,
    Permission,
    ADMIN,
    has_permission as core_has_permission,
    is_role_or_higher as core_is_role_or_higher,
    PERMISSIONS,
)
from app.models.user import User


def _try_role(value: str) -> Role | None:
    """Try to convert string to Role, return None if invalid."""
    try:
        return Role(value)
    except ValueError:
        return None


class RbacService:
    """Service for RBAC operations."""

    async def check_user_permission(
        self,
        user: User,
        permission: Permission,
    ) -> bool:
        """Check if user has a specific permission."""
        role = _try_role(user.role)
        if role is None:
            return False
        return core_has_permission(role, permission)

    async def check_user_role(
        self,
        user: User,
        required_role: Role,
    ) -> bool:
        """Check if user has required role or higher in hierarchy."""
        role = _try_role(user.role)
        if role is None:
            return False
        return core_is_role_or_higher(role, required_role)

    async def get_user_permissions(
        self,
        user: User,
    ) -> set[Permission]:
        """Get all permissions for a user based on their role."""
        role = _try_role(user.role)
        if role is None:
            return set()
        user_perms = PERMISSIONS.get(role, frozenset())
        return set(user_perms)

    async def is_org_admin(
        self,
        user: User,
        org_id: str,
    ) -> bool:
        """Check if user is admin of the organization."""
        return user.role == ADMIN.value and user.org_id == org_id

    async def can_access_resource(
        self,
        user: User,
        resource_org_id: str,
    ) -> bool:
        """Check if user can access a resource in the org (admin bypasses org check)."""
        if user.role == ADMIN.value:
            return True
        return user.org_id == resource_org_id
