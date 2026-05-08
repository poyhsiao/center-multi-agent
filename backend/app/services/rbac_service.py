"""RBAC Service - Business logic for role and permission management."""

from typing import TYPE_CHECKING

from app.core.rbac import (
    PERMISSIONS,
    Role,
    Permission,
    has_permission as core_has_permission,
    is_role_or_higher as core_is_role_or_higher,
)

if TYPE_CHECKING:
    from app.models.user import User


class RbacService:
    """Service for RBAC operations."""

    async def check_user_permission(
        self,
        user: "User",
        permission: Permission,
    ) -> bool:
        """Check if user has a specific permission."""
        try:
            role = Role(user.role)
        except ValueError:
            return False
        return core_has_permission(role, permission)

    async def check_user_role(
        self,
        user: "User",
        required_role: Role,
    ) -> bool:
        """Check if user has required role or higher."""
        try:
            role = Role(user.role)
        except ValueError:
            return False
        return core_is_role_or_higher(role, required_role)

    async def get_user_permissions(
        self,
        user: "User",
    ) -> frozenset[Permission]:
        """Get all permissions for a user."""
        try:
            role = Role(user.role)
        except ValueError:
            return frozenset()
        return PERMISSIONS.get(role, frozenset())

    async def is_org_admin(
        self,
        user: "User",
        org_id: str,
    ) -> bool:
        """Check if user is admin of the organization."""
        return user.org_id == org_id and user.role == Role.ADMIN.value

    async def can_access_resource(
        self,
        user: "User",
        resource_org_id: str,
    ) -> bool:
        """Check if user can access a resource in the org."""
        return user.org_id == resource_org_id