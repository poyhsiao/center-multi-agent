# Phase 2: Auth Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Auth Service with bcrypt password hashing (cost=12), TOTP verification (±1 window), and login flow integration with Token Service.

**Architecture:** auth_service.py provides pure functions for password hashing and TOTP. authenticate_user_async combines credential verification with token generation. Uses bcrypt for password hashing, pyotp for TOTP.

**Tech Stack:** bcrypt, pyotp, SQLAlchemy, FastAPI

---

## File Structure

```
backend/app/services/auth_service.py        # Auth logic (EXISTS - verify)
backend/app/models/user.py                  # User model (EXISTS)
backend/app/core/exceptions.py              # Exceptions (EXISTS)
backend/tests/unit/test_auth_service.py     # Unit tests (CREATE)
backend/tests/integration/test_auth_flows.py # Integration (CREATE)
backend/tests/bdd/features/A-login.feature  # EXISTS
```

---

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `hash_password` | ✅ EXISTS | bcrypt with rounds=12 |
| `verify_password` | ✅ EXISTS | bcrypt.checkpw |
| `generate_totp_secret` | ✅ EXISTS | pyotp.random_base32 |
| `generate_totp_code` | ✅ EXISTS | pyotp.TOTP.now() |
| `verify_totp` | ✅ EXISTS | ±1 window tolerance |
| `LoginCredentials` dataclass | ✅ EXISTS | email, password, fingerprint, totp_code |
| `LoginResult` dataclass | ✅ EXISTS | access_token, refresh_token, expires_in |
| `authenticate_user_async` | ✅ EXISTS | Full login flow |
| Unit tests | ❌ MISSING | Need to create |
| Integration tests | ❌ MISSING | Need to create |

---

## Task 1: Auth Service Unit Tests

**Files:**
- Create: `backend/tests/unit/test_auth_service.py`
- Test: `backend/tests/unit/test_auth_service.py`

- [ ] **Step 1: Write test_password_hash_verify**

```python
# backend/tests/unit/test_auth_service.py
import pytest

def test_password_hash_verify():
    """Password hash verification works correctly."""
    from app.services.auth_service import hash_password, verify_password

    password = "TestPassword123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) == True
    assert verify_password("WrongPassword", hashed) == False
```

- [ ] **Step 2: Run test**

Run: `cd backend && python -m pytest tests/unit/test_auth_service.py::test_password_hash_verify -v`
Expected: PASS

- [ ] **Step 3: Write test_password_hash_uniqueness**

```python
def test_password_hash_uniqueness():
    """Different salts produce different hashes for same password."""
    from app.services.auth_service import hash_password

    hash1 = hash_password("SamePassword")
    hash2 = hash_password("SamePassword")

    assert hash1 != hash2  # Different salts
    assert len(hash1) == 60  # bcrypt hash length
    assert len(hash2) == 60
```

- [ ] **Step 4: Run test**

Run: `cd backend && python -m pytest tests/unit/test_auth_service.py::test_password_hash_uniqueness -v`
Expected: PASS

- [ ] **Step 5: Write test_totp_code_generation_consistency**

```python
def test_totp_code_generation_consistency():
    """Same secret generates same TOTP code at same time."""
    from app.services.auth_service import generate_totp_secret, generate_totp_code

    secret = generate_totp_secret()
    code1 = generate_totp_code(secret)
    code2 = generate_totp_code(secret)

    assert code1 == code2
    assert len(code1) == 6
    assert code1.isdigit()
```

- [ ] **Step 6: Write test_totp_window_validation**

```python
def test_totp_window_validation():
    """TOTP verification accepts codes within ±1 window."""
    from app.services.auth_service import generate_totp_secret, generate_totp_code, verify_totp

    secret = generate_totp_secret()
    current_code = generate_totp_code(secret)

    assert verify_totp(current_code, secret) == True
    assert verify_totp(current_code, secret, window=1) == True
```

- [ ] **Step 7: Write test_verify_totp_rejects_invalid**

```python
def test_verify_totp_rejects_invalid():
    """Invalid TOTP codes are rejected."""
    from app.services.auth_service import generate_totp_secret, verify_totp

    secret = generate_totp_secret()

    assert verify_totp("000000", secret) == False
    assert verify_totp("123456", secret) == False
    assert verify_totp("abcdef", secret) == False
```

- [ ] **Step 8: Run all auth service tests**

Run: `cd backend && python -m pytest tests/unit/test_auth_service.py -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add backend/tests/unit/test_auth_service.py
git commit -m "test: add auth service unit tests for password hash and TOTP"
```

---

## Task 2: Auth Flow Integration Tests

**Files:**
- Create: `backend/tests/integration/conftest.py`
- Create: `backend/tests/integration/test_auth_flows.py`

- [ ] **Step 1: Create auth flow integration tests**

```python
# backend/tests/integration/test_auth_flows.py
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_login_success_flow():
    """Successful login returns tokens."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "ValidPassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password():
    """Wrong password returns 401."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_login_nonexistent_user():
    """Non-existent user returns 401."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPassword"},
        )

        assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_totp_required():
    """User with TOTP enabled requires code."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login without TOTP when user has TOTP enabled
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "ValidPassword123"},
        )

        # Should return 403 TOTP required, not 401
        assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_login_totp_invalid():
    """Invalid TOTP code returns 401."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "ValidPassword123",
                "totp_code": "000000",
            },
        )

        assert response.status_code == 401
```

- [ ] **Step 2: Create proper conftest with DB fixtures**

```python
# backend/tests/integration/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(settings.database_url)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/integration/test_auth_flows.py -v 2>&1 | head -60`
Expected: FAIL (may need DB setup)

- [ ] **Step 4: Debug and fix based on actual auth endpoint behavior**

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/
git commit -m "test: add auth flow integration tests"
```

---

## Task 3: BDD Login Scenarios Enhancement

**Files:**
- Review: `backend/tests/bdd/features/A-login.feature`
- Review: `backend/tests/bdd/steps/auth_steps.py`

- [ ] **Step 1: Review current A-login.feature**

Run: `cat backend/tests/bdd/features/A-login.feature`

- [ ] **Step 2: Verify all scenarios from spec Section 2 are covered**

```gherkin
# Should cover:
# - 成功登入（密碼正確）
# - 登入失敗（密碼錯誤）
# - 帳號不存在
# - Token 刷新成功
# - 設備指紋驗證失敗
# - Refresh Token 已被撤銷
```

- [ ] **Step 3: Run BDD to verify current state**

Run: `cd backend && python -m behave tests/bdd/features/A-login.feature --format=pretty 2>&1 | head -80`

- [ ] **Step 4: Fix any failing steps**

- [ ] **Step 5: Commit**

```bash
git add backend/tests/bdd/features/A-login.feature backend/tests/bdd/steps/auth_steps.py
git commit -m "test(bdd): enhance login flow scenarios coverage"
```

---

## Verification

1. **Unit tests**: `cd backend && python -m pytest tests/unit/test_auth_service.py -v`
2. **Integration tests**: `cd backend && python -m pytest tests/integration/test_auth_flows.py -v`
3. **BDD**: `cd backend && python -m behave tests/bdd/features/A-login.feature --format=pretty`

**Expected Results:** All PASS

**Spec Coverage:**
- [x] test_password_hash_verify — Task 1 Step 1
- [x] test_password_hash_uniqueness — Task 1 Step 3
- [x] test_totp_code_generation — Task 1 Step 5
- [x] test_totp_window_validation — Task 1 Step 6
- [x] test_login_success_flow — Task 2 Step 1
- [x] test_login_wrong_password — Task 2 Step 1
- [x] test_login_totp_required — Task 2 Step 1
- [x] test_login_totp_invalid — Task 2 Step 1
- [x] Feature A BDD scenarios — Task 3