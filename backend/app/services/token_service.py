"""Token Service - high-level token operations."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.security import (
    sign_access_token,
    sign_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.core.fingerprint import generate_fingerprint
from app.core.exceptions import (
    FingerprintMismatchException,
    TokenRevokedException,
    TokenExpiredException,
)
from app.db.redis import (
    store_refresh_token,
    get_current_jti,
    get_token_payload,
    blacklist_refresh_token,
    is_token_blacklisted,
    store_device_registration,
    get_device_fingerprint,
)


@dataclass
class TokenPair:
    """Access token and refresh token pair."""
    access_token: str
    refresh_token: str
    expires_in: int  # seconds


@dataclass
class RefreshResult:
    """Result of a refresh operation."""
    access_token: str
    refresh_token: str
    expires_in: int


class TokenService:
    """Service for token lifecycle management."""

    def __init__(self):
        self.access_expire_seconds = 15 * 60  # 15 minutes

    def create_tokens(
        self,
        user_id: str,
        tenant_id: str,
        device_id: str,
        fingerprint: str,
    ) -> TokenPair:
        """
        Create a new access + refresh token pair.

        Args:
            user_id: User identifier
            tenant_id: Tenant/organization identifier
            device_id: Device identifier
            fingerprint: Device fingerprint hash

        Returns:
            TokenPair with both tokens
        """
        at = sign_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            fingerprint=fingerprint,
        )

        rt = sign_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            fingerprint=fingerprint,
        )

        # Decode to get jti for storage
        import base64
        import json
        payload_b64 = rt.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64))
        jti = payload["jti"]

        # Store RT in Redis
        store_refresh_token(
            user_id=user_id,
            device_id=device_id,
            jti=jti,
            payload={"sub": user_id, "tid": tenant_id},
        )

        # Register device
        store_device_registration(
            user_id=user_id,
            device_id=device_id,
            fingerprint=fingerprint,
        )

        return TokenPair(
            access_token=at,
            refresh_token=rt,
            expires_in=self.access_expire_seconds,
        )

    def refresh_tokens(
        self,
        refresh_token: str,
        fingerprint: str,
    ) -> RefreshResult:
        """
        Perform sliding window refresh: invalidate old RT, issue new pair.

        Args:
            refresh_token: Current refresh token
            fingerprint: Current device fingerprint

        Returns:
            RefreshResult with new token pair

        Raises:
            TokenRevokedException: If token is blacklisted
            FingerprintMismatchException: If fingerprint doesn't match
        """
        # Verify RT
        claims = verify_refresh_token(refresh_token)

        user_id = claims["sub"]
        tenant_id = claims["tid"]
        device_id = claims["did"]
        stored_fp = claims["fp"]
        jti = claims["jti"]

        # Check fingerprint
        if stored_fp != fingerprint:
            raise FingerprintMismatchException()

        # Check blacklist
        if is_token_blacklisted(jti):
            raise TokenRevokedException()

        # Get remaining TTL for old RT to set blacklist expiry
        import time
        now = claims.get("exp", int(time.time()))
        remaining_ttl = max(1, now - int(time.time()))

        # Create new tokens
        new_at = sign_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            fingerprint=fingerprint,
        )

        new_rt = sign_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            fingerprint=fingerprint,
        )

        # Decode new RT to get new jti
        import base64
        import json
        payload_b64 = new_rt.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        new_payload = json.loads(base64.b64decode(payload_b64))
        new_jti = new_payload["jti"]

        # Store new RT
        store_refresh_token(
            user_id=user_id,
            device_id=device_id,
            jti=new_jti,
            payload={"sub": user_id, "tid": tenant_id},
        )

        # Blacklist old RT
        blacklist_refresh_token(jti, ttl_seconds=remaining_ttl)

        return RefreshResult(
            access_token=new_at,
            refresh_token=new_rt,
            expires_in=self.access_expire_seconds,
        )

    def revoke_refresh_token(self, refresh_token: str) -> None:
        """
        Revoke a refresh token (user logout).

        Args:
            refresh_token: Token to revoke
        """
        claims = verify_refresh_token(refresh_token)
        jti = claims["jti"]

        import time
        exp = claims.get("exp", int(time.time()))
        remaining_ttl = max(1, exp - int(time.time()))

        blacklist_refresh_token(jti, ttl_seconds=remaining_ttl)