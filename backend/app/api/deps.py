"""Authentication dependencies for API endpoints."""
from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from app.core.rbac import (
    Role,
    Permission,
    ADMIN,
    is_role_or_higher,
    has_permission,
)
from app.models.user import User


# CurrentUser class for endpoints that haven't been migrated to use User model
class CurrentUser(BaseModel):
    """Current authenticated user context."""

    user_id: str
    role: str
    tenant_id: str

    class Config:
        from_attributes = True


# Placeholder - actual implementation uses oauth2_scheme from auth module
oauth2_scheme = None


async def get_current_user(
    token: Annotated[str, Depends(lambda: None)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Returns:
        User model instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # ... existing implementation placeholder ...
    raise NotImplementedError("Implement in auth module")


def require_role(required_role: Role) -> Callable[[User], User]:
    """
    Dependency factory: require user to have at least the specified role.

    Args:
        required_role: Minimum role required (or higher in hierarchy)

    Returns:
        Dependency function that validates role

    Example:
        @router.get("/users", dependencies=[Depends(require_role(ADMIN))])
    """
    # Convert string to Role if needed
    if isinstance(required_role, str):
        required_role = Role(required_role)

    def role_checker(user: User = Depends(get_current_user)) -> User:
        if not is_role_or_higher(Role(user.role), required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is insufficient. Required: '{required_role.value}'",
            )
        return user
    return role_checker


def require_permission(permission: Permission) -> Callable[[User], User]:
    """
    Dependency factory: require user to have the specified permission.

    Args:
        permission: Permission required

    Returns:
        Dependency function that validates permission

    Example:
        @router.post("/users", dependencies=[Depends(require_permission(Permission.USERS_WRITE))])
    """
    # Convert string to Permission if needed
    if isinstance(permission, str):
        permission = Permission(permission)

    def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not has_permission(Role(user.role), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission.value}'",
            )
        return user
    return permission_checker


def require_org_access(org_id: str) -> Callable[[User], User]:
    """
    Dependency factory: require user to belong to specified org (or be admin).

    Args:
        org_id: Organization ID required

    Returns:
        Dependency function that validates org membership

    Example:
        @router.get("/org/{org_id}/users", dependencies=[Depends(require_org_access(org_id))])
    """
    def org_checker(user: User = Depends(get_current_user)) -> User:
        if user.role == ADMIN.value:
            return user  # Admin bypasses org check

        if user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization",
            )
        return user
    return org_checker


def require_org_admin(org_id: str) -> Callable[[User], User]:
    """
    Dependency factory: require admin role within specific org.

    Args:
        org_id: Organization ID required

    Returns:
        Dependency function that validates org admin role
    """
    def org_admin_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required",
            )
        if user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization",
            )
        return user
    return org_admin_checker