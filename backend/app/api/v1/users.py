"""User management API endpoints with RBAC."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role, require_permission
from app.core.rbac import ADMIN, Role, Permission
from app.models.user import User
from app.schemas.user import UserResponse, RoleUpdate, UserListResponse, UserRoleResponse
from app.db.database import get_db
from sqlalchemy import select


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

    stmt = select(User).where(User.id == user_id, User.org_id == user.org_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        new_role = Role(role_update.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role_update.role}")

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