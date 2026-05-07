"""JWT and security operations."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import (
    TokenExpiredException,
    TokenInvalidException,
)


class TokenClaims(BaseModel):
    """Standard token claims."""
    user_id: str
    tenant_id: str
    device_id: str
    fingerprint: str


def sign_access_token(
    user_id: str,
    tenant_id: str,
    device_id: str,
    fingerprint: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Sign an access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "did": device_id,
        "fp": fingerprint,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, "secret", algorithm=settings.jwt_algorithm)


def sign_refresh_token(
    user_id: str,
    tenant_id: str,
    device_id: str,
    fingerprint: str,
) -> str:
    """Sign a refresh token with unique jti."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    jti = str(uuid.uuid4())

    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "did": device_id,
        "fp": fingerprint,
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, "secret", algorithm=settings.jwt_algorithm)


def verify_access_token(token: str) -> dict:
    """Verify an access token."""
    try:
        payload = jwt.decode(
            token,
            "secret",
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise TokenInvalidException("Not an access token")
        return payload
    except JWTError as e:
        raise TokenExpiredException(str(e)) from e


def verify_refresh_token(token: str) -> dict:
    """Verify a refresh token."""
    try:
        payload = jwt.decode(
            token,
            "secret",
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "refresh":
            raise TokenInvalidException("Not a refresh token")
        return payload
    except JWTError as e:
        raise TokenExpiredException(str(e)) from e


def extract_standard_claims(token: str) -> TokenClaims:
    """Extract standard claims from any token."""
    try:
        payload = jwt.decode(
            token,
            "secret",
            algorithms=[settings.jwt_algorithm],
        )
        return TokenClaims(
            user_id=payload["sub"],
            tenant_id=payload["tid"],
            device_id=payload["did"],
            fingerprint=payload["fp"],
        )
    except JWTError as e:
        raise TokenExpiredException(str(e)) from e
