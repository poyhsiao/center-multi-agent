"""Tenant Service - Organization, Department, User CRUD and RBAC Engine."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.exceptions import (
    DuplicateResourceException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.services.auth_service import hash_password


# =============================================================================
# RBAC Engine
# =============================================================================

@dataclass(frozen=True)
class RbacEngine:
    """
    Role-Based Access Control Engine.

    Permission Matrix:
    | Action                | Admin | Manager | Member |
    |-----------------------|-------|---------|--------|
    | manage_org_settings   | ✓     | ✗       | ✗      |
    | manage_departments    | ✓     | ✓       | ✗      |
    | manage_members        | ✓     | ✓       | ✗      |
    | invite_members       | ✓     | ✓       | ✗      |
    | submit_knowledge     | ✓     | ✓       | ✓      |
    | review_knowledge      | ✓     | ✓       | ✗      |
    | publish_knowledge     | ✓     | ✗       | ✗      |
    """

    _permission_matrix: dict[str, frozenset[str]] = field(default_factory=lambda: {
        "admin": frozenset({
            "manage_org_settings",
            "manage_departments",
            "manage_members",
            "invite_members",
            "submit_knowledge",
            "review_knowledge",
            "publish_knowledge",
        }),
        "manager": frozenset({
            "manage_departments",
            "manage_members",
            "invite_members",
            "submit_knowledge",
            "review_knowledge",
        }),
        "member": frozenset({
            "submit_knowledge",
        }),
    })

    def check_permission(
        self,
        role: str,
        action: str,
        user_context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if a role has permission for an action.

        Args:
            role: User role (admin, manager, member)
            action: Action to check (e.g., manage_org_settings)
            user_context: Optional user context dict

        Returns:
            True if permission granted, False otherwise
        """
        if role not in self._permission_matrix:
            return False
        return action in self._permission_matrix[role]

    def get_role_permissions(self, role: str) -> dict[str, bool]:
        """
        Get all permissions for a role.

        Args:
            role: User role

        Returns:
            Dict mapping action names to boolean permissions
        """
        all_actions = {
            "manage_org_settings",
            "manage_departments",
            "manage_members",
            "invite_members",
            "submit_knowledge",
            "review_knowledge",
            "publish_knowledge",
        }
        if role not in self._permission_matrix:
            return {action: False for action in all_actions}
        return {action: action in self._permission_matrix[role] for action in all_actions}

    def require_permission(
        self,
        role: str,
        action: str,
        user_context: dict[str, Any] | None = None,
    ) -> None:
        """
        Require permission or raise PermissionDeniedException.

        Args:
            role: User role
            action: Action to check
            user_context: Optional user context dict

        Raises:
            PermissionDeniedException: If permission denied
        """
        if not self.check_permission(role, action, user_context):
            raise PermissionDeniedException(
                f"Role '{role}' does not have permission for '{action}'"
            )


# =============================================================================
# Repository Interfaces
# =============================================================================


class OrganizationRepository:
    """Repository interface for Organization operations."""

    def find_by_id(self, org_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def find_by_slug(self, slug: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def save(self, org: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def delete(self, org_id: str) -> bool:
        raise NotImplementedError


class DepartmentRepository:
    """Repository interface for Department operations."""

    def find_by_id(self, dept_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def find_by_org_id(self, org_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def find_children(self, parent_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def save(self, dept: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def delete(self, dept_id: str) -> bool:
        raise NotImplementedError


class UserRepository:
    """Repository interface for User operations."""

    def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def find_by_org_id(self, org_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def save(self, user: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def delete(self, user_id: str) -> bool:
        raise NotImplementedError


# =============================================================================
# In-Memory Repositories (for testing)
# =============================================================================


class InMemoryOrganizationRepository(OrganizationRepository):
    """In-memory implementation of OrganizationRepository."""

    def __init__(self):
        self._orgs: dict[str, dict[str, Any]] = {}

    def find_by_id(self, org_id: str) -> dict[str, Any] | None:
        return self._orgs.get(org_id)

    def find_by_slug(self, slug: str) -> dict[str, Any] | None:
        for org in self._orgs.values():
            if org.get("slug") == slug:
                return org
        return None

    def save(self, org: dict[str, Any]) -> dict[str, Any]:
        self._orgs[org["id"]] = org
        return org

    def delete(self, org_id: str) -> bool:
        if org_id in self._orgs:
            del self._orgs[org_id]
            return True
        return False


class InMemoryDepartmentRepository(DepartmentRepository):
    """In-memory implementation of DepartmentRepository."""

    def __init__(self):
        self._depts: dict[str, dict[str, Any]] = {}

    def find_by_id(self, dept_id: str) -> dict[str, Any] | None:
        return self._depts.get(dept_id)

    def find_by_org_id(self, org_id: str) -> list[dict[str, Any]]:
        return [d for d in self._depts.values() if d.get("org_id") == org_id]

    def find_children(self, parent_id: str) -> list[dict[str, Any]]:
        return [d for d in self._depts.values() if d.get("parent_id") == parent_id]

    def save(self, dept: dict[str, Any]) -> dict[str, Any]:
        self._depts[dept["id"]] = dept
        return dept

    def delete(self, dept_id: str) -> bool:
        if dept_id in self._depts:
            del self._depts[dept_id]
            return True
        return False


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository."""

    def __init__(self):
        self._users: dict[str, dict[str, Any]] = {}

    def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        for user in self._users.values():
            if user.get("email") == email:
                return user
        return None

    def find_by_org_id(self, org_id: str) -> list[dict[str, Any]]:
        return [u for u in self._users.values() if u.get("org_id") == org_id]

    def save(self, user: dict[str, Any]) -> dict[str, Any]:
        self._users[user["id"]] = user
        return user

    def delete(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


# =============================================================================
# Organization Service
# =============================================================================


@dataclass
class OrganizationService:
    """Service for Organization CRUD operations."""

    repo: OrganizationRepository = field(default_factory=InMemoryOrganizationRepository)

    def _generate_id(self) -> str:
        return str(uuid4())

    def _utcnow(self) -> str:
        from datetime import datetime, UTC
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def create_org(self, org_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new organization.

        Args:
            org_data: Dict with name, slug, plan (optional)

        Returns:
            Created organization dict

        Raises:
            DuplicateResourceException: If slug already exists
        """
        existing = self.repo.find_by_slug(org_data.get("slug", ""))
        if existing:
            raise DuplicateResourceException(f"Organization with slug '{org_data['slug']}' already exists")

        now = self._utcnow()
        org = {
            "id": self._generate_id(),
            "name": org_data["name"],
            "slug": org_data["slug"],
            "plan": org_data.get("plan", "free"),
            "created_at": now,
            "updated_at": now,
        }
        return self.repo.save(org)

    def get_org(self, org_id: str) -> dict[str, Any]:
        """
        Get organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization dict

        Raises:
            ResourceNotFoundException: If not found
        """
        org = self.repo.find_by_id(org_id)
        if not org:
            raise ResourceNotFoundException(f"Organization '{org_id}' not found")
        return org

    def get_org_by_slug(self, slug: str) -> dict[str, Any]:
        """
        Get organization by slug.

        Args:
            slug: Organization slug

        Returns:
            Organization dict

        Raises:
            ResourceNotFoundException: If not found
        """
        org = self.repo.find_by_slug(slug)
        if not org:
            raise ResourceNotFoundException(f"Organization with slug '{slug}' not found")
        return org

    def update_org(self, org_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update organization.

        Args:
            org_id: Organization ID
            updates: Dict of fields to update

        Returns:
            Updated organization dict

        Raises:
            ResourceNotFoundException: If not found
        """
        org = self.get_org(org_id)
        updated = {**org, **updates, "updated_at": self._utcnow()}
        return self.repo.save(updated)

    def delete_org(self, org_id: str) -> bool:
        """
        Delete organization.

        Args:
            org_id: Organization ID

        Returns:
            True if deleted

        Raises:
            ResourceNotFoundException: If not found
        """
        org = self.get_org(org_id)
        return self.repo.delete(org["id"])


# =============================================================================
# Department Service
# =============================================================================


@dataclass
class DepartmentService:
    """Service for Department CRUD with hierarchy support."""

    repo: DepartmentRepository = field(default_factory=InMemoryDepartmentRepository)

    def _generate_id(self) -> str:
        return str(uuid4())

    def _utcnow(self) -> str:
        from datetime import datetime, UTC
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def create_dept(self, dept_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new department.

        Args:
            dept_data: Dict with org_id, name, parent_id (optional)

        Returns:
            Created department dict
        """
        dept = {
            "id": self._generate_id(),
            "org_id": dept_data["org_id"],
            "name": dept_data["name"],
            "parent_id": dept_data.get("parent_id"),
            "created_at": self._utcnow(),
        }
        return self.repo.save(dept)

    def get_dept(self, dept_id: str) -> dict[str, Any]:
        """
        Get department by ID.

        Args:
            dept_id: Department ID

        Returns:
            Department dict

        Raises:
            ResourceNotFoundException: If not found
        """
        dept = self.repo.find_by_id(dept_id)
        if not dept:
            raise ResourceNotFoundException(f"Department '{dept_id}' not found")
        return dept

    def get_dept_tree(self, org_id: str) -> list[dict[str, Any]]:
        """
        Get department tree structure for an organization.

        Args:
            org_id: Organization ID

        Returns:
            List of root departments with nested children
        """
        all_depts = self.repo.find_by_org_id(org_id)
        return self._build_tree(all_depts)

    def _build_tree(
        self,
        depts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build tree structure from flat department list."""
        dept_map = {d["id"]: {**d, "children": []} for d in depts}
        roots = []

        for dept in depts:
            node = dept_map[dept["id"]]
            if dept["parent_id"] and dept["parent_id"] in dept_map:
                dept_map[dept["parent_id"]]["children"].append(node)
            else:
                roots.append(node)

        return roots

    def update_dept(self, dept_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update department.

        Args:
            dept_id: Department ID
            updates: Dict of fields to update

        Returns:
            Updated department dict

        Raises:
            ResourceNotFoundException: If not found
        """
        dept = self.get_dept(dept_id)
        updated = {**dept, **updates}
        return self.repo.save(updated)

    def delete_dept(self, dept_id: str) -> bool:
        """
        Delete department and re-assign children to no parent.

        Args:
            dept_id: Department ID

        Returns:
            True if deleted

        Raises:
            ResourceNotFoundException: If not found
        """
        dept = self.get_dept(dept_id)

        # Re-assign children to have no parent
        children = self.repo.find_children(dept_id)
        for child in children:
            updated_child = {**child, "parent_id": None}
            self.repo.save(updated_child)

        return self.repo.delete(dept_id)


# =============================================================================
# User Service
# =============================================================================


@dataclass
class UserService:
    """Service for User CRUD operations."""

    repo: UserRepository = field(default_factory=InMemoryUserRepository)

    def _generate_id(self) -> str:
        return str(uuid4())

    def _utcnow(self) -> str:
        from datetime import datetime, UTC
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new user.

        Args:
            user_data: Dict with org_id, email, password, role (optional)

        Returns:
            Created user dict (without password_hash)

        Raises:
            DuplicateResourceException: If email already exists
        """
        existing = self.repo.find_by_email(user_data["email"])
        if existing:
            raise DuplicateResourceException(f"User with email '{user_data['email']}' already exists")

        password_hash = hash_password(user_data["password"])

        user = {
            "id": self._generate_id(),
            "org_id": user_data["org_id"],
            "dept_id": user_data.get("dept_id"),
            "email": user_data["email"],
            "password_hash": password_hash,
            "role": user_data.get("role", "member"),
            "totp_secret": None,
            "totp_enabled": False,
            "status": "active",
            "created_at": self._utcnow(),
        }
        saved = self.repo.save(user)
        return {k: v for k, v in saved.items() if k != "password_hash"}

    def get_user(self, user_id: str) -> dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User dict (without password_hash)

        Raises:
            ResourceNotFoundException: If not found
        """
        user = self.repo.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundException(f"User '{user_id}' not found")
        return {k: v for k, v in user.items() if k != "password_hash"}

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User dict (without password_hash)

        Raises:
            ResourceNotFoundException: If not found
        """
        user = self.repo.find_by_email(email)
        if not user:
            raise ResourceNotFoundException(f"User with email '{email}' not found")
        return {k: v for k, v in user.items() if k != "password_hash"}

    def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update user.

        Args:
            user_id: User ID
            updates: Dict of fields to update

        Returns:
            Updated user dict (without password_hash)

        Raises:
            ResourceNotFoundException: If not found
        """
        user = self.get_user(user_id)
        if "password" in updates:
            updates["password_hash"] = hash_password(updates.pop("password"))
        updated = {**user, **updates}
        saved = self.repo.save(updated)
        return {k: v for k, v in saved.items() if k != "password_hash"}

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted

        Raises:
            ResourceNotFoundException: If not found
        """
        user = self.get_user(user_id)
        return self.repo.delete(user["id"])

    def get_org_users(self, org_id: str) -> list[dict[str, Any]]:
        """
        Get all users in an organization.

        Args:
            org_id: Organization ID

        Returns:
            List of user dicts (without password_hash)
        """
        users = self.repo.find_by_org_id(org_id)
        return [{k: v for k, v in u.items() if k != "password_hash"} for u in users]
