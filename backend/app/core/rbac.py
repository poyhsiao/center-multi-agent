# backend/app/core/rbac.py
"""RBAC (Role-Based Access Control) constants and utilities."""

from enum import Enum
from typing import FrozenSet


class Role(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permission types in the system."""
    # User permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    USERS_ROLE_CHANGE = "users:role_change"

    # Department permissions
    DEPT_READ = "dept:read"
    DEPT_WRITE = "dept:write"
    DEPT_DELETE = "dept:delete"

    # Knowledge permissions
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    KNOWLEDGE_DELETE = "knowledge:delete"
    KNOWLEDGE_PUBLISH = "knowledge:publish"

    # Agent/Task permissions
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_EXECUTE = "agent:execute"

    # Organization settings
    ORG_SETTINGS = "org:settings"
    ORG_BILLING = "org:billing"


# Role constants for convenience
ADMIN = Role.ADMIN
MANAGER = Role.MANAGER
MEMBER = Role.MEMBER
VIEWER = Role.VIEWER

# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = {
    ADMIN: 3,
    MANAGER: 2,
    MEMBER: 1,
    VIEWER: 0,
}

# Permissions for each role (per spec Section 3.2)
PERMISSIONS: dict[Role, FrozenSet[Permission]] = {
    ADMIN: frozenset(Permission.__members__.values()),
    MANAGER: frozenset([
        Permission.DEPT_READ,
        Permission.DEPT_WRITE,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.KNOWLEDGE_DELETE,
        Permission.AGENT_READ,
        Permission.AGENT_WRITE,
        Permission.AGENT_EXECUTE,
    ]),
    MEMBER: frozenset([
        Permission.DEPT_READ,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.AGENT_READ,
        Permission.AGENT_WRITE,
    ]),
    VIEWER: frozenset([
        Permission.DEPT_READ,
        Permission.KNOWLEDGE_READ,
        Permission.AGENT_READ,
    ]),
}


def is_role_or_higher(role: Role, required_role: Role) -> bool:
    """
    Check if role meets or exceeds the required role level.

    Args:
        role: The user's role
        required_role: The minimum required role

    Returns:
        True if user's role is >= required role in hierarchy
    """
    return ROLE_HIERARCHY.get(role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: The user's role
        permission: The permission to check

    Returns:
        True if role has the permission
    """
    return permission in PERMISSIONS.get(role, frozenset())