"""Department management API endpoints with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import require_permission
from app.core.rbac import Permission
from app.models.user import User
from app.models.department import Department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)
from app.db.database import get_db
from uuid import uuid4


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
    if org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Cannot access departments in another organization")
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
    if dept_data.org_id != user.org_id:
        raise HTTPException(status_code=403, detail="Cannot create department in another organization")
    department = Department(
        id=str(uuid4()),
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
    stmt = select(Department).where(
        Department.id == department_id,
        Department.org_id == user.org_id,
    )
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