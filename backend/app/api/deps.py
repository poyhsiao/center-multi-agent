"""Authentication dependencies for API endpoints."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import TokenExpiredException, TokenInvalidException
from app.core.security import verify_access_token


class User(BaseModel):
    """Authenticated user context from JWT."""
    user_id: str
    tenant_id: str
    device_id: str
    role: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate JWT token and return current user.

    Args:
        token: JWT access token from Authorization header

    Returns:
        User object with extracted claims

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidException:
        raise credentials_exception

    return User(
        user_id=user_id,
        tenant_id=payload.get("tid", ""),
        device_id=payload.get("did", ""),
        role=payload.get("role"),
    )


# Annotated dependency for type-safe injection
CurrentUser = Annotated[User, Depends(get_current_user)]