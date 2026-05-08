# RBAC Permission System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a complete RBAC permission system with role hierarchy, resource-based permissions, and dependency injection for access control.

**Architecture:** FastAPI dependency injection with role-based access control. Roles are strings stored in User model. Permissions are checked via dependency functions. Multi-tenant isolation via org_id scoping.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Python

---

## File Structure

```
backend/app/
├── core/
│   └── rbac.py              # RBAC constants, permission checking functions
├── api/v1/
│   ├── deps.py              # Update: add role dependencies
│   ├── users.py             # New: User management endpoints
│   ├── roles.py             # New: Role permission endpoints
│   └── departments.py       # New: Department management
├── schemas/
│   ├── user.py              # Update: add role schemas
│   └── permission.py        # New: Permission schemas
└── services/
    └── rbac_service.py      # New: RBAC business logic
```

---

## Task 1: RBAC Constants & Permission Definitions

**Files:**
- Create: `backend/app/core/rbac.py`
- Test: `backend/tests/unit/test_rbac.py`

- [ ] **Step 1: Write RBAC tests**

```python
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
    """Verify permission constants exist."""
    assert Permission.USERS_READ in PERMISSIONS
    assert Permission.USERS_WRITE in PERMISSIONS
    assert Permission.DEPT_READ in PERMISSIONS
    assert Permission.DEPT_WRITE in PERMISSIONS


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_rbac.py -v`
Expected: FAIL - module doesn't exist

- [ ] **Step 3: Write RBAC core**

```python
# backend/app/core/rbac.py
"""RBAC (Role-Based Access Control) constants and utilities."""

from enum import Enum
from typing import FrozenSet


class Role(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
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
MEMBER = Role.MEMBER
VIEWER = Role.VIEWER

# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = {
    ADMIN: 3,
    MEMBER: 2,
    VIEWER: 1,
}

# Permissions for each role
PERMISSIONS: dict[Role, FrozenSet[Permission]] = {
    ADMIN: frozenset(Permission),
    MEMBER: frozenset([
        Permission.USERS_READ,
        Permission.DEPT_READ,
        Permission.KNOWLEDGE_READ,
        Permission.KNOWLEDGE_WRITE,
        Permission.AGENT_READ,
        Permission.AGENT_WRITE,
    ]),
    VIEWER: frozenset([
        Permission.USERS_READ,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_rbac.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/rbac.py backend/tests/unit/test_rbac.py
git commit -m "feat(backend): add RBAC constants and permission definitions"
```

---

## Task 2: Role Check Dependencies

**Files:**
- Modify: `backend/app/api/deps.py`
- Test: `backend/tests/unit/test_rbac_deps.py`

- [ ] **Step 1: Write role dependency tests**

```python
# backend/tests/unit/test_rbac_deps.py
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.api.deps import (
    get_current_user,
    require_role,
    require_permission,
    require_org_access,
)


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
    with patch("app.api.deps.get_current_user", return_value=mock_user):
        result = require_role("member")
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
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - functions don't exist in deps.py yet

- [ ] **Step 3: Write role dependencies**

```python
# backend/app/api/deps.py (add these after existing get_current_user)

from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status

from app.core.rbac import (
    Role,
    Permission,
    ADMIN,
    is_role_or_higher,
    has_permission,
)
from app.models.user import User


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Returns:
        User model instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # ... existing implementation ...


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_rbac_deps.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/deps.py backend/tests/unit/test_rbac_deps.py
git commit -m "feat(backend): add RBAC role check dependencies"
```

---

## Task 3: User Role Management API

**Files:**
- Create: `backend/app/api/v1/users.py`
- Test: `backend/tests/api/test_users.py`
- Modify: `backend/app/schemas/user.py`

- [ ] **Step 1: Write user role tests**

```python
# backend/tests/api/test_users.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Get admin access token."""
    # Use test fixture or mock


@pytest.fixture
def member_token():
    """Get member access token."""
    # Use test fixture or mock


def test_list_users_requires_admin():
    """Non-admin cannot list users."""
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 403


def test_list_users_as_admin():
    """Admin can list users in their org."""
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": "Bearer admin_token"},
    )
    assert response.status_code == 200
    assert "users" in response.json()


def test_list_users_filters_by_org():
    """Users only see users in their org."""
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": "Bearer admin_token"},
    )
    users = response.json()["users"]
    for user in users:
        assert user["org_id"] == expected_org_id


def test_change_user_role_requires_admin():
    """Non-admin cannot change user roles."""
    response = client.patch(
        "/api/v1/users/user-123/role",
        json={"role": "admin"},
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 403


def test_change_user_role_as_admin():
    """Admin can change user roles."""
    response = client.patch(
        "/api/v1/users/user-123/role",
        json={"role": "viewer"},
        headers={"Authorization": "Bearer admin_token"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


def test_change_own_role_not_allowed():
    """Admin cannot change their own role."""
    response = client.patch(
        "/api/v1/users/self-id/role",
        json={"role": "viewer"},
        headers={"Authorization": "Bearer admin_token"},
    )
    assert response.status_code == 400


def test_deactivate_user_requires_admin():
    """Non-admin cannot deactivate users."""
    response = client.post(
        "/api/v1/users/user-123/deactivate",
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - endpoint doesn't exist

- [ ] **Step 3: Write user schemas update**

```python
# backend/app/schemas/user.py (add these schemas)

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class RoleUpdate(BaseModel):
    """Schema for updating user role."""
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserRoleResponse(BaseModel):
    """Response schema for user role change."""
    id: str
    email: str
    role: str
    org_id: str

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Response schema for user list."""
    users: list[UserResponse]
    total: int
```

- [ ] **Step 4: Write user role endpoints**

```python
# backend/app/api/v1/users.py
"""User management API endpoints with RBAC."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role, require_permission
from app.core.rbac import ADMIN, Role, Permission
from app.models.user import User
from app.schemas.user import UserResponse, RoleUpdate, UserListResponse, UserRoleResponse
from app.db.database import get_db


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    org_id: str,
    user: User = Depends(require_role(ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users in an organization.
    Requires admin role.
    """
    # Query users where org_id matches
    from sqlalchemy import select
    stmt = select(User).where(User.org_id == org_id)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=len(users),
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    org_id: str,
    user: User = Depends(require_permission(Permission.USERS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific user by ID.
    Requires users:read permission.
    """
    stmt = select(User).where(User.id == user_id, User.org_id == org_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(target_user)


@router.patch("/{user_id}/role", response_model=UserRoleResponse)
async def change_user_role(
    user_id: str,
    role_update: RoleUpdate,
    user: User = Depends(require_permission(Permission.USERS_ROLE_CHANGE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Change a user's role.
    Requires users:role_change permission.
    Cannot change own role.
    """
    if user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role",
        )

    # Verify target user exists and is in same org
    stmt = select(User).where(User.id == user_id, User.org_id == user.org_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate role value
    try:
        new_role = Role(role_update.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role_update.role}")

    # Update role
    target_user.role = new_role.value
    await db.commit()
    await db.refresh(target_user)

    return UserRoleResponse.model_validate(target_user)


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    user: User = Depends(require_permission(Permission.USERS_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user account.
    Requires users:delete permission.
    """
    if user_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate yourself",
        )

    stmt = select(User).where(User.id == user_id, User.org_id == user.org_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.status = "inactive"
    await db.commit()

    return {"message": "User deactivated"}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/api/test_users.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/users.py backend/app/schemas/user.py backend/tests/api/test_users.py
git commit -m "feat(backend): add user role management API endpoints"
```

---

## Task 4: Department Management API

**Files:**
- Create: `backend/app/api/v1/departments.py`
- Test: `backend/tests/api/test_departments.py`
- Modify: `backend/app/schemas/department.py`

- [ ] **Step 1: Write department tests**

```python
# backend/tests/api/test_departments.py
import pytest
from fastapi.testclient import TestClient


def test_create_department_requires_admin():
    """Non-admin cannot create departments."""
    response = client.post(
        "/api/v1/departments",
        json={"name": "Engineering", "org_id": "org-123"},
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 403


def test_create_department_as_admin():
    """Admin can create departments."""
    response = client.post(
        "/api/v1/departments",
        json={"name": "Engineering", "org_id": "org-123"},
        headers={"Authorization": "Bearer admin_token"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Engineering"


def test_list_departments_member_can_read():
    """Member can list departments."""
    response = client.get(
        "/api/v1/departments",
        params={"org_id": "org-123"},
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 200


def test_delete_department_requires_admin():
    """Non-admin cannot delete departments."""
    response = client.delete(
        "/api/v1/departments/dept-123",
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - endpoint doesn't exist

- [ ] **Step 3: Write department schemas**

```python
# backend/app/schemas/department.py (add these)

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class DepartmentBase(BaseModel):
    name: str
    org_id: str
    parent_id: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    departments: list[DepartmentResponse]
    total: int
```

- [ ] **Step 4: Write department endpoints**

```python
# backend/app/api/v1/departments.py
"""Department management API endpoints with RBAC."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role, require_permission
from app.core.rbac import ADMIN, MEMBER, Permission
from app.models.user import User
from app.models.department import Department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)
from app.db.database import get_db


router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=DepartmentListResponse)
async def list_departments(
    org_id: str,
    user: User = Depends(require_permission(Permission.DEPT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """
    List all departments in an organization.
    Requires dept:read permission.
    """
    stmt = select(Department).where(Department.org_id == org_id)
    result = await db.execute(stmt)
    departments = result.scalars().all()

    return DepartmentListResponse(
        departments=[DepartmentResponse.model_validate(d) for d in departments],
        total=len(departments),
    )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_data: DepartmentCreate,
    user: User = Depends(require_permission(Permission.DEPT_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new department.
    Requires dept:write permission.
    """
    department = Department(
        id=generate_uuid(),  # Use your UUID generation
        name=dept_data.name,
        org_id=dept_data.org_id,
        parent_id=dept_data.parent_id,
    )

    db.add(department)
    await db.commit()
    await db.refresh(department)

    return DepartmentResponse.model_validate(department)


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: str,
    user: User = Depends(require_permission(Permission.DEPT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific department.
    Requires dept:read permission.
    """
    stmt = select(Department).where(Department.id == department_id)
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    return DepartmentResponse.model_validate(department)


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    dept_update: DepartmentUpdate,
    user: User = Depends(require_permission(Permission.DEPT_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a department.
    Requires dept:write permission.
    """
    stmt = select(Department).where(
        Department.id == department_id,
        Department.org_id == user.org_id,
    )
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    if dept_update.name is not None:
        department.name = dept_update.name
    if dept_update.parent_id is not None:
        department.parent_id = dept_update.parent_id

    await db.commit()
    await db.refresh(department)

    return DepartmentResponse.model_validate(department)


@router.delete("/{department_id}")
async def delete_department(
    department_id: str,
    user: User = Depends(require_permission(Permission.DEPT_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a department.
    Requires dept:delete permission.
    """
    stmt = select(Department).where(
        Department.id == department_id,
        Department.org_id == user.org_id,
    )
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    await db.delete(department)
    await db.commit()

    return {"message": "Department deleted"}
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/departments.py backend/app/schemas/department.py backend/tests/api/test_departments.py
git commit -m "feat(backend): add department management API with RBAC"
```

---

## Task 5: Apply RBAC to Existing Endpoints

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`
- Modify: `backend/app/api/v1/agent.py`
- Modify: `backend/app/api/v1/rag.py`
- Test: `backend/tests/api/test_rbac_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/api/test_rbac_integration.py
import pytest
from fastapi.testclient import TestClient


def test_knowledge_endpoints_require_permissions():
    """Knowledge endpoints enforce permission checks."""
    # Viewer cannot create knowledge
    response = client.post(
        "/api/v1/knowledge",
        json={"title": "Test", "content": "..."},
        headers={"Authorization": "Bearer viewer_token"},
    )
    assert response.status_code == 403

    # Member can create knowledge
    response = client.post(
        "/api/v1/knowledge",
        json={"title": "Test", "content": "..."},
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 201


def test_agent_endpoints_require_permissions():
    """Agent endpoints enforce permission checks."""
    # Viewer cannot execute agent tasks
    response = client.post(
        "/api/v1/agent/execute",
        json={"task": "do something"},
        headers={"Authorization": "Bearer viewer_token"},
    )
    assert response.status_code == 403


def test_rag_search_requires_read_permission():
    """RAG search requires knowledge:read permission."""
    # Any authenticated user with knowledge:read can search
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "test"},
        headers={"Authorization": "Bearer member_token"},
    )
    assert response.status_code == 200

    # Viewer can read
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "test"},
        headers={"Authorization": "Bearer viewer_token"},
    )
    assert response.status_code == 200


def test_org_isolation_enforced():
    """Users cannot access resources from other orgs."""
    # User from org-A cannot access org-B resources
    response = client.get(
        "/api/v1/knowledge",
        headers={"Authorization": "Bearer org_a_user_token"},
    )
    # Should only return org-A's knowledge
    for item in response.json()["items"]:
        assert item["org_id"] == "org-A"
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - RBAC not applied yet

- [ ] **Step 3: Apply RBAC to knowledge endpoints**

```python
# backend/app/api/v1/knowledge.py (add dependencies)
from app.api.deps import require_permission, require_org_access
from app.core.rbac import Permission

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/", dependencies=[Depends(require_permission(Permission.KNOWLEDGE_READ))])
async def list_knowledge(
    org_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...


@router.post("/", dependencies=[Depends(require_permission(Permission.KNOWLEDGE_WRITE))])
async def create_knowledge(
    knowledge_data: KnowledgeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...


@router.delete("/{knowledge_id}", dependencies=[Depends(require_permission(Permission.KNOWLEDGE_DELETE))])
async def delete_knowledge(
    knowledge_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...
```

- [ ] **Step 4: Apply RBAC to agent endpoints**

```python
# backend/app/api/v1/agent.py (add dependencies)
from app.api.deps import require_permission
from app.core.rbac import Permission

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/tasks", dependencies=[Depends(require_permission(Permission.AGENT_READ))])
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...


@router.post("/execute", dependencies=[Depends(require_permission(Permission.AGENT_EXECUTE))])
async def execute_task(
    task_data: TaskExecute,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...
```

- [ ] **Step 5: Apply RBAC to RAG endpoints**

```python
# backend/app/api/v1/rag.py (add dependencies)
from app.api.deps import require_permission
from app.core.rbac import Permission

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", dependencies=[Depends(require_permission(Permission.KNOWLEDGE_READ))])
async def search_knowledge(
    search_data: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...


@router.post("/publish", dependencies=[Depends(require_permission(Permission.KNOWLEDGE_PUBLISH))])
async def publish_knowledge(
    publish_data: PublishRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ... existing implementation ...
```

- [ ] **Step 6: Run tests to verify**

Run: `cd backend && python -m pytest tests/api/test_rbac_integration.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/knowledge.py backend/app/api/v1/agent.py backend/app/api/v1/rag.py
git commit -m "feat(backend): apply RBAC permissions to existing endpoints"
```

---

## Task 6: RBAC Service for Business Logic

**Files:**
- Create: `backend/app/services/rbac_service.py`
- Test: `backend/tests/unit/test_rbac_service.py`

- [ ] **Step 1: Write RBAC service tests**

```python
# backend/tests/unit/test_rbac_service.py
import pytest
from app.services.rbac_service import RBACService, RoleAssignmentError


@pytest.fixture
def rbac_service():
    return RBACService()


def test_validate_role_assignment_valid():
    """Valid role assignments are accepted."""
    # Admin can assign any role
    rbac_service.validate_role_assignment("admin", "member")
    rbac_service.validate_role_assignment("admin", "viewer")
    rbac_service.validate_role_assignment("admin", "admin")


def test_member_cannot_assign_admin():
    """Member cannot assign admin role."""
    with pytest.raises(RoleAssignmentError):
        rbac_service.validate_role_assignment("member", "admin")


def test_admin_cannot_assign_higher_than_self():
    """No role can assign a role higher than itself."""
    with pytest.raises(RoleAssignmentError):
        rbac_service.validate_role_assignment("viewer", "admin")


def test_get_role_permissions():
    """Get all permissions for a role."""
    admin_perms = rbac_service.get_role_permissions("admin")
    assert "users:write" in admin_perms

    viewer_perms = rbac_service.get_role_permissions("viewer")
    assert "users:write" not in viewer_perms


def test_check_permission_for_role():
    """Check if role has specific permission."""
    assert rbac_service.check_permission("admin", "users:delete") is True
    assert rbac_service.check_permission("member", "users:delete") is False


def test_check_role_hierarchy():
    """Check role hierarchy correctly."""
    assert rbac_service.is_role_higher_or_equal("admin", "member") is True
    assert rbac_service.is_role_higher_or_equal("member", "viewer") is True
    assert rbac_service.is_role_higher_or_equal("viewer", "admin") is False
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL - service doesn't exist

- [ ] **Step 3: Write RBAC service**

```python
# backend/app/services/rbac_service.py
"""RBAC business logic service."""
from app.core.rbac import (
    Role,
    Permission,
    ADMIN,
    MEMBER,
    VIEWER,
    PERMISSIONS,
    ROLE_HIERARCHY,
)


class RoleAssignmentError(Exception):
    """Raised when a role assignment is not permitted."""
    pass


class RBACService:
    """
    Service for RBAC business logic.
    Centralizes role hierarchy checks and permission validation.
    """

    def validate_role_assignment(
        self,
        assigning_role: str,
        target_role: str,
    ) -> None:
        """
        Validate that a role can assign another role.

        Args:
            assigning_role: Role of the user making the assignment
            target_role: Role being assigned

        Raises:
            RoleAssignmentError: If assignment is not permitted
        """
        try:
            assigner = Role(assigning_role)
            target = Role(target_role)
        except ValueError:
            raise RoleAssignmentError(f"Invalid role: {assigning_role} or {target_role}")

        assigner_level = ROLE_HIERARCHY.get(assigner, 0)
        target_level = ROLE_HIERARCHY.get(target, 0)

        # Can only assign roles at or below your level
        if target_level > assigner_level:
            raise RoleAssignmentError(
                f"Role '{assigner.value}' cannot assign '{target.value}' - insufficient role level"
            )

    def get_role_permissions(self, role: str) -> list[str]:
        """
        Get all permissions for a role.

        Args:
            role: Role name

        Returns:
            List of permission strings
        """
        try:
            role_enum = Role(role)
        except ValueError:
            return []

        return [p.value for p in PERMISSIONS.get(role_enum, frozenset())]

    def check_permission(self, role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            role: Role name
            permission: Permission string

        Returns:
            True if role has the permission
        """
        try:
            role_enum = Role(role)
            perm_enum = Permission(permission)
        except ValueError:
            return False

        return perm_enum in PERMISSIONS.get(role_enum, frozenset())

    def is_role_higher_or_equal(self, role: str, compare_role: str) -> bool:
        """
        Check if a role is higher or equal in hierarchy.

        Args:
            role: Role to check
            compare_role: Role to compare against

        Returns:
            True if role >= compare_role in hierarchy
        """
        try:
            role_enum = Role(role)
            compare_enum = Role(compare_role)
        except ValueError:
            return False

        return ROLE_HIERARCHY.get(role_enum, 0) >= ROLE_HIERARCHY.get(compare_enum, 0)

    def get_role_display_name(self, role: str) -> str:
        """Get human-readable role name."""
        names = {
            "admin": "Administrator",
            "member": "Member",
            "viewer": "Viewer",
        }
        return names.get(role, role)

    def get_all_roles(self) -> list[dict]:
        """Get all roles with their permissions."""
        return [
            {
                "role": role.value,
                "display_name": self.get_role_display_name(role.value),
                "permissions": self.get_role_permissions(role.value),
                "level": ROLE_HIERARCHY.get(role, 0),
            }
            for role in Role
        ]
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/rbac_service.py backend/tests/unit/test_rbac_service.py
git commit -m "feat(backend): add RBAC service for business logic"
```

---

## Verification

After all tasks:

```bash
# Run all RBAC tests
cd backend && python -m pytest tests/unit/test_rbac.py tests/unit/test_rbac_deps.py tests/unit/test_rbac_service.py tests/api/test_users.py tests/api/test_departments.py tests/api/test_rbac_integration.py -v

# Run full test suite to ensure no regressions
cd backend && python -m pytest tests/ -v --tb=short

# Verify imports work
cd backend && python -c "from app.core.rbac import Role, Permission; from app.api.deps import require_role, require_permission"
```

---

## Summary

- **Task 1:** RBAC constants and permission definitions
- **Task 2:** Role check dependencies for FastAPI
- **Task 3:** User role management API endpoints
- **Task 4:** Department management API with RBAC
- **Task 5:** Apply RBAC to existing endpoints (Knowledge, Agent, RAG)
- **Task 6:** RBAC service for business logic encapsulation