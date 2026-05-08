"""User Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    role: str = "member"


class UserCreate(UserBase):
    password: str
    org_id: str
    dept_id: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: str | None = None
    dept_id: str | None = None
    status: str | None = None


class UserResponse(UserBase):
    id: str
    org_id: str
    dept_id: str | None
    status: str
    totp_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_fingerprint: str | None = None


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
    users: list["UserResponse"]
    total: int
