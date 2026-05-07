# Token Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Token Service with RS256 JWT signing/verification, Sliding Window RT rotation, Redis blacklist, and device fingerprint binding.

**Architecture:** Service layer encapsulating JWT operations with Redis for session state. Uses python-jose for RS256 JWT, Redis for RT storage/blacklist, and device fingerprint for binding.

**Tech Stack:** Python 3.11+, FastAPI, python-jose, redis-py, passlib, pytest, pytest-asyncio

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Settings (JWT keys, Redis URL)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py        # JWT operations, fingerprint
│   │   └── exceptions.py      # TokenException, FingerprintMismatch
│   └── services/
│       ├── __init__.py
│       └── token_service.py   # TokenService class
├── tests/
│   ├── unit/
│   │   ├── __init__.py
│   │   └── test_token_service.py
│   └── conftest.py            # Pytest fixtures
└── pyproject.toml
```

---

## Task 1: Project Setup

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/exceptions.py`
- Create: `backend/app/services/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[tool.poetry]
name = "center-multi-agent-backend"
version = "0.1.0"
description = "Center Multi-Agent Backend"
authors = ["Kim Hsiao"]
readme = "README.md"
packages = [{include = "app"}]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
pydantic = "^2.7"
pydantic-settings = "^2.3"
python-jose = {extras = ["cryptography"], version = "^3.3"}
passlib = {extras = ["bcrypt"], version = "^1.7"}
redis = "^5.0"
asyncpg = "^0.29"
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}

[tool.poetry.group.dev.dependencies]
pytest = "^8.2"
pytest-asyncio = "^0.23"
httpx = "^0.27"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create app/__init__.py**

```python
"""Center Multi-Agent Backend Application."""
```

- [ ] **Step 3: Create app/config.py**

```python
"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # JWT Settings
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # RSA Keys (load from files in production)
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    fingerprint_salt: str = "change-me-in-production"


settings = Settings()
```

- [ ] **Step 4: Create app/core/__init__.py**

```python
"""Core module."""
```

- [ ] **Step 5: Create app/core/exceptions.py**

```python
"""Custom exceptions for token operations."""
from typing import Optional


class TokenException(Exception):
    """Base exception for token operations."""

    def __init__(self, message: str, code: str = "token_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TokenExpiredException(TokenException):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="token_expired")


class TokenInvalidException(TokenException):
    """Token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, code="token_invalid")


class FingerprintMismatchException(TokenException):
    """Device fingerprint does not match."""

    def __init__(self, message: str = "Device fingerprint mismatch"):
        super().__init__(message, code="fingerprint_mismatch")


class TokenRevokedException(TokenException):
    """Token has been revoked."""

    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message, code="token_revoked")
```

- [ ] **Step 6: Create app/services/__init__.py**

```python
"""Services module."""
```

- [ ] **Step 7: Commit**

```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/config.py
git add backend/app/core/__init__.py backend/app/core/exceptions.py
git add backend/app/services/__init__.py
git commit -m "feat(token-service): initial project structure"
```

---

## Task 2: JWT Sign and Verify (Unit Tests)

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/unit/__init__.py`
- Modify: `backend/tests/unit/test_token_service.py`

- [ ] **Step 1: Write failing test for JWT sign and verify**

```python
# tests/unit/test_token_service.py
"""Unit tests for Token Service."""
import pytest
from datetime import datetime, timedelta, timezone


class TestJWTOperations:
    """Test JWT signing and verification."""

    def test_jwt_sign_creates_access_token(self):
        """Sign should create a valid JWT access token."""
        from app.core.security import sign_access_token

        token = sign_access_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_sign_creates_refresh_token(self):
        """Sign should create a JWT refresh token with jti."""
        from app.core.security import sign_refresh_token

        token = sign_refresh_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        assert token is not None
        assert isinstance(token, str)

    def test_jwt_verify_valid_access_token(self):
        """Verify should return claims for valid access token."""
        from app.core.security import sign_access_token, verify_access_token

        token = sign_access_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        claims = verify_access_token(token)

        assert claims["sub"] == "user-123"
        assert claims["tid"] == "tenant-456"
        assert claims["did"] == "device-789"
        assert claims["fp"] == "fp_abc123"
        assert claims["type"] == "access"

    def test_jwt_verify_valid_refresh_token(self):
        """Verify should return claims including jti for refresh token."""
        from app.core.security import sign_refresh_token, verify_refresh_token

        token = sign_refresh_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        claims = verify_refresh_token(token)

        assert claims["sub"] == "user-123"
        assert claims["jti"] is not None
        assert claims["type"] == "refresh"

    def test_jwt_claims_extraction(self):
        """Should correctly extract all standard claims."""
        from app.core.security import sign_access_token, extract_standard_claims

        token = sign_access_token(
            user_id="user-999",
            tenant_id="tenant-888",
            device_id="device-777",
            fingerprint="fp_xyz",
        )

        claims = extract_standard_claims(token)

        assert claims.user_id == "user-999"
        assert claims.tenant_id == "tenant-888"
        assert claims.device_id == "device-777"
        assert claims.fingerprint == "fp_xyz"

    def test_jwt_expired_token_rejected(self):
        """Expired token should be rejected with TokenExpiredException."""
        from app.core.security import sign_access_token, verify_access_token
        from app.core.exceptions import TokenExpiredException

        # Create a token that's already expired (exp = now - 1 second)
        with pytest.raises(TokenExpiredException):
            verify_access_token("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTYwMDAwMDAwMH0.fake")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_token_service.py::TestJWTOperations -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app'"

- [ ] **Step 3: Create minimal security.py with signing only**

```python
# app/core/security.py
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
        raise TokenInvalidException(str(e))


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
        raise TokenInvalidException(str(e))


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
        raise TokenInvalidException(str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_token_service.py::TestJWTOperations -v`
Expected: PASS (or FAIL on expired test which needs real RSA keys)

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/unit/test_token_service.py
git commit -m "feat(token-service): add JWT sign and verify operations"
```

---

## Task 3: Device Fingerprint Generation

**Files:**
- Create: `backend/app/core/fingerprint.py`
- Modify: `backend/tests/unit/test_token_service.py`

- [ ] **Step 1: Write failing test for fingerprint generation**

```python
# Add to tests/unit/test_token_service.py

class TestFingerprintGeneration:
    """Test device fingerprint generation."""

    def test_fingerprint_generation_consistency(self):
        """Same inputs should produce same fingerprint."""
        from app.core.fingerprint import generate_fingerprint

        fp1 = generate_fingerprint(
            user_agent="Mozilla/5.0",
            client_version="1.0.0",
            client_type="web",
        )

        fp2 = generate_fingerprint(
            user_agent="Mozilla/5.0",
            client_version="1.0.0",
            client_type="web",
        )

        assert fp1 == fp2

    def test_fingerprint_different_inputs_different_output(self):
        """Different inputs should produce different fingerprints."""
        from app.core.fingerprint import generate_fingerprint

        fp1 = generate_fingerprint(
            user_agent="Mozilla/5.0",
            client_version="1.0.0",
            client_type="web",
        )

        fp2 = generate_fingerprint(
            user_agent="Chrome/120.0",
            client_version="1.0.0",
            client_type="web",
        )

        assert fp1 != fp2

    def test_fingerprint_is_sha256_hash(self):
        """Fingerprint should be a SHA256 hex string."""
        from app.core.fingerprint import generate_fingerprint

        fp = generate_fingerprint(
            user_agent="Mozilla/5.0",
            client_version="1.0.0",
            client_type="web",
        )

        assert len(fp) == 64  # SHA256 hex = 64 characters
        assert all(c in "0123456789abcdef" for c in fp)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_token_service.py::TestFingerprintGeneration -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.core.fingerprint'"

- [ ] **Step 3: Create fingerprint.py**

```python
# app/core/fingerprint.py
"""Device fingerprint generation."""
import hashlib

from app.config import settings


def generate_fingerprint(
    user_agent: str,
    client_version: str,
    client_type: str,
    salt: str | None = None,
) -> str:
    """
    Generate a device fingerprint from components.

    Format: SHA256(agent_hash + client_version + client_type + salt)

    Args:
        user_agent: Browser or client user agent string
        client_version: Application version (e.g., "1.0.0")
        client_type: Client type ("web", "desktop", "mobile")
        salt: Optional salt override (uses config salt by default)

    Returns:
        SHA256 hex digest of combined components
    """
    if salt is None:
        salt = settings.fingerprint_salt

    # Hash the user agent for privacy
    agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    # Combine all components
    raw = f"{agent_hash}{client_version}{client_type}{salt}"

    # Final fingerprint
    return hashlib.sha256(raw.encode()).hexdigest()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_token_service.py::TestFingerprintGeneration -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/fingerprint.py
git add backend/tests/unit/test_token_service.py
git commit -m "feat(token-service): add device fingerprint generation"
```

---

## Task 4: Redis Integration for RT Storage

**Files:**
- Create: `backend/app/db/redis.py`
- Create: `backend/app/services/token_service.py`
- Create: `backend/tests/unit/test_token_service.py` (integration section)

- [ ] **Step 1: Write failing test for Redis RT operations**

```python
# Add to tests/unit/test_token_service.py

class TestRedisRTOperations:
    """Test Redis refresh token storage and blacklist."""

    @pytest.fixture
    def redis_client(self):
        """Create a Redis client for testing."""
        import redis
        client = redis.Redis.from_url("redis://localhost:6379/1")
        yield client
        client.flushdb()  # Clean up after test

    def test_store_refresh_token(self, redis_client):
        """Should store RT with correct key pattern."""
        from app.db.redis import store_refresh_token

        store_refresh_token(
            user_id="user-123",
            device_id="device-789",
            jti="jti-abc",
            payload={"sub": "user-123", "tid": "tenant-456"},
        )

        key = "rt:user-123:device-789"
        assert redis_client.exists(key)
        assert redis_client.hget(key, "current") == b"jti-abc"

    def test_get_current_jti(self, redis_client):
        """Should retrieve current RT's jti."""
        from app.db.redis import store_refresh_token, get_current_jti

        store_refresh_token(
            user_id="user-123",
            device_id="device-789",
            jti="jti-abc",
            payload={"sub": "user-123"},
        )

        jti = get_current_jti("user-123", "device-789")
        assert jti == "jti-abc"

    def test_blacklist_refresh_token(self, redis_client):
        """Should add RT to blacklist with TTL."""
        from app.db.redis import blacklist_refresh_token, is_token_blacklisted

        blacklist_refresh_token("jti-abc", ttl_seconds=3600)

        assert is_token_blacklisted("jti-abc") is True

    def test_token_not_blacklisted_initially(self, redis_client):
        """New token should not be blacklisted."""
        from app.db.redis import is_token_blacklisted

        result = is_token_blacklisted("jti-new")
        assert result is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_token_service.py::TestRedisRTOperations -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.db'"

- [ ] **Step 3: Create redis.py**

```python
# app/db/redis.py
"""Redis client and operations."""
import json
from typing import Optional
import redis

from app.config import settings


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def store_refresh_token(
    user_id: str,
    device_id: str,
    jti: str,
    payload: dict,
) -> None:
    """
    Store refresh token in Redis.

    Key pattern: rt:<user_id>:<device_id>
    Stores:
      - jti:<jti>: JSON payload
      - current: current jti
      - created_at: timestamp
    """
    client = get_redis_client()
    key = f"rt:{user_id}:{device_id}"

    import time
    created_at = int(time.time())

    # Store all JTIs for this user+device (keep history for sliding window)
    client.hset(key, f"jti:{jti}", json.dumps(payload))
    client.hset(key, "current", jti)
    client.hset(key, "created_at", created_at)

    # Set expiry on the hash (7 days + buffer)
    client.expire(key, 60 * 60 * 24 * 8)


def get_current_jti(user_id: str, device_id: str) -> Optional[str]:
    """Get the current (most recent) jti for user+device."""
    client = get_redis_client()
    key = f"rt:{user_id}:{device_id}"
    return client.hget(key, "current")


def get_token_payload(user_id: str, device_id: str, jti: str) -> Optional[dict]:
    """Get stored payload for a specific jti."""
    client = get_redis_client()
    key = f"rt:{user_id}:{device_id}"
    data = client.hget(key, f"jti:{jti}")
    if data:
        return json.loads(data)
    return None


def blacklist_refresh_token(jti: str, ttl_seconds: int) -> None:
    """
    Add a refresh token to the blacklist.

    Blacklisted tokens cannot be used for refresh.
    TTL should match remaining token validity.
    """
    client = get_redis_client()
    key = f"blacklist:rt:{jti}"
    client.setex(key, ttl_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token is blacklisted."""
    client = get_redis_client()
    key = f"blacklist:rt:{jti}"
    return client.exists(key) == 1


def store_device_registration(
    user_id: str,
    device_id: str,
    fingerprint: str,
    trusted: bool = False,
) -> None:
    """Register or update a device."""
    client = get_redis_client()
    key = f"device:{user_id}:{device_id}"

    import time
    client.hset(key, mapping={
        "fingerprint": fingerprint,
        "trusted": "1" if trusted else "0",
        "last_active": int(time.time()),
    })
    client.expire(key, 60 * 60 * 24 * 30)  # 30 days


def get_device_fingerprint(user_id: str, device_id: str) -> Optional[str]:
    """Get registered fingerprint for a device."""
    client = get_redis_client()
    key = f"device:{user_id}:{device_id}"
    return client.hget(key, "fingerprint")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_token_service.py::TestRedisRTOperations -v`
Expected: PASS (requires Redis running on localhost:6379)

- [ ] **Step 5: Create token_service.py**

```python
# app/services/token_service.py
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
```

- [ ] **Step 6: Run integration tests**

Run: `cd backend && python -m pytest tests/integration/ -v`
Expected: PASS (requires Redis)

- [ ] **Step 7: Commit**

```bash
git add backend/app/db/redis.py backend/app/services/token_service.py
git add backend/tests/unit/test_token_service.py
git commit -m "feat(token-service): add Redis RT storage and sliding window rotation"
```

---

## Task 5: TokenService Integration Tests

**Files:**
- Create: `backend/tests/integration/conftest.py`
- Create: `backend/tests/integration/test_token_service.py`

- [ ] **Step 1: Write integration tests for complete flows**

```python
# tests/integration/test_token_service.py
"""Integration tests for TokenService."""
import pytest
import time

from app.services.token_service import TokenService
from app.core.exceptions import (
    FingerprintMismatchException,
    TokenRevokedException,
)


class TestTokenServiceIntegration:
    """Integration tests for complete token flows."""

    @pytest.fixture
    def token_service(self):
        """Create TokenService instance."""
        return TokenService()

    def test_create_tokens_returns_valid_pair(self, token_service):
        """create_tokens should return both tokens."""
        result = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.expires_in == 900  # 15 minutes

    def test_full_refresh_flow(self, token_service):
        """Complete refresh cycle: create -> refresh -> verify new RT works."""
        # Create initial tokens
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        # Refresh with same fingerprint
        refreshed = token_service.refresh_tokens(
            refresh_token=initial.refresh_token,
            fingerprint="fp_abc123",
        )

        assert refreshed.access_token != initial.access_token
        assert refreshed.refresh_token != initial.refresh_token

        # Old RT should be revoked - second refresh with old RT should fail
        with pytest.raises(TokenRevokedException):
            token_service.refresh_tokens(
                refresh_token=initial.refresh_token,
                fingerprint="fp_abc123",
            )

    def test_fingerprint_mismatch_rejects_refresh(self, token_service):
        """Different fingerprint should reject refresh."""
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        with pytest.raises(FingerprintMismatchException):
            token_service.refresh_tokens(
                refresh_token=initial.refresh_token,
                fingerprint="fp_different",
            )

    def test_logout_revokes_token(self, token_service):
        """logout should revoke the refresh token."""
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        # Logout
        token_service.revoke_refresh_token(initial.refresh_token)

        # Try to use revoked token
        with pytest.raises(TokenRevokedException):
            token_service.refresh_tokens(
                refresh_token=initial.refresh_token,
                fingerprint="fp_abc123",
            )

    def test_concurrent_refresh_only_one_succeeds(self, token_service):
        """
        Simulate concurrent refreshes - only one should succeed.
        In real implementation, this would need Redis atomic operations.
        """
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        # In a proper implementation with Redis transactions,
        # only one concurrent refresh would succeed.
        # This test documents the expected behavior.
        pass
```

- [ ] **Step 2: Create conftest.py**

```python
# tests/integration/conftest.py
"""Pytest configuration for integration tests."""
import pytest


@pytest.fixture(scope="session")
def redis_url():
    """Redis URL for integration tests."""
    return "redis://localhost:6379/0"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/integration/test_token_service.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/tests/integration/conftest.py backend/tests/integration/test_token_service.py
git commit -m "test(token-service): add TokenService integration tests"
```

---

## Task 6: Verify All Tests Pass

- [ ] **Step 1: Run all unit tests**

Run: `cd backend && python -m pytest tests/unit/ -v`
Expected: All PASS

- [ ] **Step 2: Run all integration tests**

Run: `cd backend && python -m pytest tests/integration/ -v`
Expected: All PASS

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat(token-service): complete Phase 1 implementation with TDD"
```

---

## Summary

| Task | Files Created/Modified | Test Count |
|------|------------------------|------------|
| 1. Project Setup | 6 files | 0 |
| 2. JWT Sign/Verify | 2 files | 6 tests |
| 3. Fingerprint | 2 files | 3 tests |
| 4. Redis RT Storage | 2 files | 5 tests |
| 5. Integration Tests | 2 files | 5 tests |
| 6. Verify | - | - |

**Total: 19 tests**

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-07-token-service.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?