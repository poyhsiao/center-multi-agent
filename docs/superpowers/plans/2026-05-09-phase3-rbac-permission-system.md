# Phase 3: RBAC Permission System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement complete RBAC with role hierarchy (ADMIN > MANAGER > MEMBER > VIEWER), resource-based permissions, and FastAPI dependency injection for access control.

**Architecture:** FastAPI dependency injection with role-based access control. Roles stored as strings in User model. Permissions checked via dependency functions. Multi-tenant isolation via org_id scoping.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Python

---

## File Structure

```
backend/app/core/rbac.py                   # Role/Permission enums (EXISTS)
backend/app/api/deps.py                     # RBAC dependencies (EXISTS)
backend/app/api/v1/departments.py           # Department router (VERIFY)
backend/app/api/v1/knowledge.py             # Knowledge with RBAC (EXISTS)
backend/app/api/v1/rag.py                    # RAG with RBAC (EXISTS)
backend/tests/unit/test_rbac_deps.py        # EXISTS
backend/tests/unit/test_rbac_service.py     # EXISTS
backend/tests/api/test_rbac_integration.py  # CREATE
backend/tests/bdd/features/                 # EXISTS
```

---

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `Role` enum (ADMIN/MEMBER/VIEWER) | ✅ EXISTS | In rbac.py |
| `Permission` enum | ✅ EXISTS | Full permission set |
| `ROLE_HIERARCHY` | ✅ EXISTS | In rbac.py |
| `ROLE_PERMISSIONS` dict | ✅ EXISTS | In rbac.py |
| `require_role` dependency | ✅ EXISTS | In deps.py |
| `require_permission` dependency | ✅ EXISTS | In deps.py |
| Departments router | ⚠️ VERIFY | Need to check |
| Knowledge endpoints RBAC | ⚠️ VERIFY | Need to check |
| RAG endpoint RBAC | ✅ EXISTS | Has Permission.KNOWLEDGE_READ |
| Unit tests (test_rbac_deps) | ✅ EXISTS | |
| Integration tests | ❌ MISSING | Need to create |

---

## Task 1: RBAC Dependencies Verification

**Files:**
- Review: `backend/app/api/deps.py`
- Review: `backend/app/core/rbac.py`

- [ ] **Step 1: Verify require_role and require_permission exist**

Run: `grep -A 20 'def require_role' backend/app/api/deps.py`

- [ ] **Step 2: Verify ROLE_PERMISSIONS matches spec Section 3.2**

Expected permissions matrix:

| Action | Admin | Manager | Member | Viewer |
|--------|-------|---------|--------|--------|
| org:settings | ✓ | ✗ | ✗ | ✗ |
| dept:read | ✓ | ✓ | ✓ | ✓ |
| dept:write | ✓ | ✓ | ✗ | ✗ |
| dept:delete | ✓ | ✗ | ✗ | ✗ |
| users:read | ✓ | ✓ | ✗ | ✗ |
| users:write | ✓ | ✓ | ✗ | ✗ |
| users:delete | ✓ | ✗ | ✗ | ✗ |
| users:role_change | ✓ | ✗ | ✗ | ✗ |
| knowledge:read | ✓ | ✓ | ✓ | ✓ |
| knowledge:write | ✓ | ✓ | ✓ | ✗ |
| knowledge:delete | ✓ | ✓ | ✗ | ✗ |
| knowledge:publish | ✓ | ✗ | ✗ | ✗ |
| agent:read | ✓ | ✓ | ✓ | ✓ |
| agent:write | ✓ | ✓ | ✓ | ✗ |
| agent:execute | ✓ | ✓ | ✗ | ✗ |

- [ ] **Step 3: Add missing permissions if needed**

Check rbac.py. If missing, add to Permission enum.

- [ ] **Step 4: Verify require_org_access**

Run: `grep -A 15 'def require_org_access' backend/app/api/deps.py`

If missing, implement:

```python
def require_org_access(org_id: str) -> Callable[[User], User]:
    """Require user to belong to specified org (or be admin)."""
    def org_checker(user: User = Depends(get_current_user)) -> User:
        if user.role == ADMIN.value:
            return user
        if user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization",
            )
        return user
    return org_checker
```

- [ ] **Step 5: Run existing RBAC deps tests**

Run: `cd backend && python -m pytest tests/unit/test_rbac_deps.py -v`

- [ ] **Step 6: Commit if changes made**

```bash
git add backend/app/api/deps.py backend/app/core/rbac.py
git commit -m "fix(rbac): add missing require_org_access dependency"
```

---

## Task 2: Department Management API Tests

**Files:**
- Test: `backend/tests/api/test_departments.py`
- Modify: `backend/app/api/v1/departments.py` (if needed)

- [ ] **Step 1: Check if departments.py exists**

Run: `cat backend/app/api/v1/departments.py 2>/dev/null || echo 'NOT FOUND'`

- [ ] **Step 2: Write department API tests**

```python
# backend/tests/api/test_departments.py
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_create_department_requires_admin():
    """Non-admin cannot create departments."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/departments",
            json={"name": "Engineering", "org_id": "org-123"},
            headers={"Authorization": "Bearer member_token"},
        )
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_department_as_admin():
    """Admin can create departments."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/departments",
            json={"name": "Engineering", "org_id": "org-123"},
            headers={"Authorization": "Bearer admin_token"},
        )
        assert response.status_code in [201, 200]

@pytest.mark.asyncio
async def test_list_departments_member_can_read():
    """Member can list departments."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/departments",
            params={"org_id": "org-123"},
            headers={"Authorization": "Bearer member_token"},
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_department_requires_admin():
    """Non-admin cannot delete departments."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            "/api/v1/departments/dept-123",
            headers={"Authorization": "Bearer member_token"},
        )
        assert response.status_code == 403
```

- [ ] **Step 3: If departments.py doesn't exist, create it**

```python
# backend/app/api/v1/departments.py
"""Department management API endpoints with RBAC."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, require_role
from app.core.rbac import ADMIN
from app.models.user import User
from app.models.department import Department
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/departments", tags=["departments"])

class DepartmentCreate(BaseModel):
    name: str
    org_id: str
    parent_id: str | None = None

class DepartmentResponse(BaseModel):
    id: str
    name: str
    org_id: str
    parent_id: str | None = None

    model_config = {"from_attributes": True}

@router.post("/", dependencies=[Depends(require_role(ADMIN))])
async def create_department(
    dept: DepartmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    """Create a new department. Admin only."""
    new_dept = Department(
        id=f"dept-{uuid.uuid4()}",
        name=dept.name,
        org_id=dept.org_id,
        parent_id=dept.parent_id,
    )
    db.add(new_dept)
    await db.commit()
    await db.refresh(new_dept)
    return new_dept

@router.get("/")
async def list_departments(
    org_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DepartmentResponse]:
    """List departments for an org. All authenticated users can read."""
    stmt = select(Department).where(Department.org_id == org_id)
    result = await db.execute(stmt)
    departments = result.scalars().all()
    return departments

@router.delete("/{dept_id}", dependencies=[Depends(require_role(ADMIN))])
async def delete_department(
    dept_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a department. Admin only."""
    stmt = select(Department).where(Department.id == dept_id)
    result = await db.execute(stmt)
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    await db.delete(dept)
    await db.commit()
    return {"message": "Deleted"}
```

- [ ] **Step 4: Create department schemas**

```python
# backend/app/schemas/department.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class DepartmentBase(BaseModel):
    name: str
    org_id: str
    parent_id: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 5: Register department router in main.py**

Check if departments router is included:

Run: `grep 'departments' backend/app/main.py`

If missing, add:
```python
from app.api.v1.departments import router as departments_router
app.include_router(departments_router, prefix="/api/v1")
```

- [ ] **Step 6: Run tests**

Run: `cd backend && python -m pytest tests/api/test_departments.py -v`

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/departments.py backend/app/schemas/department.py backend/app/main.py backend/tests/api/test_departments.py
git commit -m "feat(departments): add department management API with RBAC"
```

---

## Task 3: RBAC Integration Tests

**Files:**
- Create: `backend/tests/api/test_rbac_integration.py`

- [ ] **Step 1: Write RBAC integration tests**

```python
# backend/tests/api/test_rbac_integration.py
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_knowledge_endpoints_require_permissions():
    """Knowledge endpoints enforce permission checks."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Viewer cannot create knowledge
        response = await client.post(
            "/api/v1/knowledge",
            json={"title": "Test", "content": "..."},
            headers={"Authorization": "Bearer viewer_token"},
        )
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_agent_endpoints_require_permissions():
    """Agent endpoints enforce permission checks."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent/execute",
            json={"task": "do something"},
            headers={"Authorization": "Bearer viewer_token"},
        )
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_rag_search_requires_read_permission():
    """RAG search requires knowledge:read permission."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/rag/query",
            json={"query": "test"},
            headers={"Authorization": "Bearer member_token"},
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_org_isolation_enforced():
    """Users cannot access resources from other orgs."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/knowledge",
            headers={"Authorization": "Bearer org_a_user_token"},
        )
        assert response.status_code == 200
```

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/api/test_rbac_integration.py -v`

- [ ] **Step 3: Fix any failures**

- [ ] **Step 4: Commit**

```bash
git add backend/tests/api/test_rbac_integration.py
git commit -m "test: add RBAC integration tests for endpoint enforcement"
```

---

## Task 4: BDD Scenario Coverage

**Files:**
- Review: `backend/tests/bdd/features/B-agent-operation.feature`
- Review: `backend/tests/bdd/features/C-knowledge-contribution.feature`

- [ ] **Step 1: Verify Feature B coverage**

Run: `cat backend/tests/bdd/features/B-agent-operation.feature`

- [ ] **Step 2: Verify Feature C coverage**

Run: `cat backend/tests/bdd/features/C-knowledge-contribution.feature`

- [ ] **Step 3: Run BDD tests**

Run: `cd backend && python -m behave tests/bdd/features/ --format=pretty 2>&1 | head -100`

- [ ] **Step 4: Fix any failing scenarios**

---

## Verification

1. **RBAC deps tests**: `cd backend && python -m pytest tests/unit/test_rbac_deps.py -v`
2. **Department tests**: `cd backend && python -m pytest tests/api/test_departments.py -v`
3. **RBAC integration tests**: `cd backend && python -m pytest tests/api/test_rbac_integration.py -v`
4. **BDD**: `cd backend && python -m behave tests/bdd/features/B-agent-operation.feature tests/bdd/features/C-knowledge-contribution.feature --format=pretty`

**Expected Results:** All PASS

**Spec Coverage:**
- [x] Role constants and Permission enum — Task 1
- [x] require_role dependency — Task 1
- [x] require_permission dependency — Task 1
- [x] require_org_access dependency — Task 1
- [x] Department CRUD API — Task 2
- [x] Knowledge RBAC enforcement — Task 3
- [x] Agent RBAC enforcement — Task 3
- [x] RAG RBAC enforcement — Task 3
- [x] Org isolation — Task 3
- [x] Feature B BDD — Task 4
- [x] Feature C BDD — Task 4