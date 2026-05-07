"""Authentication API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from app.core.security import verify_access_token, extract_standard_claims
from app.core.fingerprint import generate_fingerprint
from app.core.exceptions import (
    InvalidCredentialsException,
    TOTPRequiredException,
    TokenExpiredException,
    TokenRevokedException,
    FingerprintMismatchException,
)
from app.services.auth_service import authenticate_user, LoginCredentials
from app.services.token_service import TokenService


router = APIRouter(prefix="/auth", tags=["auth"])


class TOTPRequestForm(OAuth2PasswordRequestForm):
    """Extended form with optional TOTP code."""

    def __init__(self, **data):
        super().__init__(**data)
        self.totp_code = data.get("totp_code")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    """
    Dependency to extract and verify user_id from access token.

    Args:
        token: Bearer token from Authorization header

    Returns:
        user_id from token claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        claims = verify_access_token(token)
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        return user_id
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


@router.post("/token")
async def login(
    form_data: Annotated[TOTPRequestForm, Depends()],
) -> dict:
    """
    OAuth2 login endpoint.

    Returns access_token and refresh_token on successful authentication.
    Supports optional TOTP code for 2FA.
    """
    # Generate fingerprint from user agent
    fingerprint = generate_fingerprint(
        user_agent=form_data.scopes[0] if form_data.scopes else "",
        client_version=form_data.scopes[1] if len(form_data.scopes) > 1 else "1.0.0",
        client_type=form_data.scopes[2] if len(form_data.scopes) > 2 else "web",
    )

    credentials = LoginCredentials(
        email=form_data.username,
        password=form_data.password,
        device_fingerprint=fingerprint,
        totp_code=getattr(form_data, "totp_code", None),
    )

    try:
        result = authenticate_user(credentials)
        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": "bearer",
            "expires_in": result.expires_in,
        }
    except TOTPRequiredException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TOTP code required",
            headers={"X-MFA-Required": "true"},
        )
    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    fingerprint: str,
) -> dict:
    """
    Refresh access token using a valid refresh token.

    Performs sliding window refresh: old refresh token is invalidated,
    new token pair is issued.
    """
    token_service = TokenService()

    try:
        result = token_service.refresh_tokens(
            refresh_token=refresh_token,
            fingerprint=fingerprint,
        )
        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": "bearer",
            "expires_in": result.expires_in,
        }
    except TokenRevokedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    except FingerprintMismatchException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device fingerprint mismatch",
        )
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )


@router.post("/logout")
async def logout(
    refresh_token: str,
) -> dict:
    """
    Logout by revoking the refresh token.

    The access token remains valid until its expiry (15 min default).
    """
    token_service = TokenService()

    try:
        token_service.revoke_refresh_token(refresh_token)
        return {"message": "Successfully logged out"}
    except TokenExpiredException:
        # Token already expired, consider it revoked
        return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """
    Get current authenticated user information.

    Returns user_id, tenant_id, and device_id from the access token.
    """
    try:
        claims = extract_standard_claims(token)
        return {
            "user_id": claims.user_id,
            "tenant_id": claims.tenant_id,
            "device_id": claims.device_id,
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user information",
        )
