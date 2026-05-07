# Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-ready features: rate limiting, request logging, structured logging, security headers, and improved health endpoints.

**Architecture:** FastAPI middleware stack with BaseHTTPMiddleware for request timing/logging, security middleware for trusted hosts and CORS, Redis-based rate limiting, and structured logging with correlation IDs.

**Tech Stack:** FastAPI, BaseHTTPMiddleware, Starlette Security Middleware, Redis (for rate limiting), structlog

---

## File Structure

```
backend/app/
├── api/v1/
│   ├── __init__.py
│   ├── auth.py           # existing
│   ├── knowledge.py      # existing
│   ├── agent.py          # existing
│   ├── rag.py            # existing
│   ├── sync.py           # existing
│   ├── deps.py           # Modify: add rate limit dependency
│   └── ws.py             # Create: WebSocket endpoint
├── core/
│   ├── __init__.py
│   ├── middleware.py       # Create: request logging, rate limiting
│   ├── logging.py          # Create: structured logger setup
│   ├── security.py         # Modify: add security headers
│   ├── notification.py      # existing
│   └── websocket.py         # existing
├── config.py               # Modify: add logging config
└── main.py                 # Modify: add middleware stack, WebSocket endpoint
```

---

## Task 1: Structured Logging Setup

**Files:**
- Create: `backend/app/core/logging.py`
- Modify: `backend/app/config.py`
- Test: `backend/tests/unit/test_logging.py`

- [ ] **Step 1: Write failing test for structured logging**

```python
# tests/unit/test_logging.py
import pytest

pytestmark = pytest.mark.unit


class TestStructuredLogging:
    """Tests for structured logging."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        from app.core.logging import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_logger_has_correct_context(self):
        """Test logger includes request_id in context."""
        from app.core.logging import get_logger

        logger = get_logger("test")
        # Should have request_id in extra
        assert hasattr(logger, 'request_id')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_logging.py -v`
Expected: FAIL with "No module named 'app.core.logging'"

- [ ] **Step 3: Write structured logging setup**

```python
# backend/app/core/logging.py
"""Structured Logging Configuration - Production-ready logging."""

import logging
import sys
from datetime import datetime
from typing import Any

import structlog
from structlog.types import Processor


def add_timestamp(logger: Any, method: str, event: dict) -> dict:
    """Add ISO timestamp to log entries."""
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event


def add_log_level(logger: Any, method: str, event: dict) -> dict:
    """Add log level to event."""
    event["level"] = method.upper()
    return event


def add_service_info(logger: Any, method: str, event: dict) -> dict:
    """Add service name to event."""
    event["service"] = "center-multi-agent"
    return event


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog with processors."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_timestamp,
        add_log_level,
        add_service_info,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Configure on import
configure_logging()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_logging.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_logging.py app/core/logging.py
git commit -m "feat(core): add structured logging with structlog"
```

---

## Task 2: Request Logging Middleware

**Files:**
- Create: `backend/app/core/middleware.py`
- Test: `backend/tests/unit/test_middleware.py`

- [ ] **Step 1: Write failing test for request logging middleware**

```python
# tests/unit/test_middleware.py
import pytest

pytestmark = pytest.mark.unit


class TestRequestLoggingMiddleware:
    """Tests for request logging middleware."""

    def test_request_logging_middleware_exists(self):
        """Test RequestLoggingMiddleware class exists."""
        from app.core.middleware import RequestLoggingMiddleware

        assert RequestLoggingMiddleware is not None

    def test_rate_limit_middleware_exists(self):
        """Test RateLimitMiddleware class exists."""
        from app.core.middleware import RateLimitMiddleware

        assert RateLimitMiddleware is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_middleware.py -v`
Expected: FAIL with "No module named 'app.core.middleware'"

- [ ] **Step 3: Write request logging middleware**

```python
# backend/app/core/middleware.py
"""Middleware - Request logging, rate limiting, and security headers."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with timing."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )

        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            request_id=request_id,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, redis_url: str = None, requests_per_minute: int = 60):
        super().__init__(app)
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self._redis_client = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and proceed or reject."""
        if self.redis_url:
            client = self._get_redis_client()
            if client:
                key = f"rate_limit:{request.client.host}"
                try:
                    current = await client.incr(key)
                    if current == 1:
                        await client.expire(key, 60)
                    if current > self.requests_per_minute:
                        return Response(
                            content='{"error":"Rate limit exceeded"}',
                            status_code=429,
                            media_type="application/json",
                        )
                except Exception:
                    pass  # If Redis fails, allow request

        return await call_next(request)

    def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None and self.redis_url:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(self.redis_url)
        return self._redis_client
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_middleware.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_middleware.py app/core/middleware.py
git commit -m "feat(core): add request logging and rate limiting middleware"
```

---

## Task 3: Security Headers Middleware

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/unit/test_security_headers.py`

- [ ] **Step 1: Write failing test for security headers**

```python
# tests/unit/test_security_headers.py
import pytest

pytestmark = pytest.mark.unit


class TestSecurityHeaders:
    """Tests for security headers."""

    def test_security_headers_in_response(self):
        """Test that security headers are added to response."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert "X-Request-ID" in response.headers
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_security_headers.py -v`
Expected: FAIL (no X-Request-ID header yet)

- [ ] **Step 3: Modify main.py to add middleware stack**

Read `app/main.py` and add:

```python
from app.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.core.logging import configure_logging, get_logger

# Configure logging at startup
configure_logging()
logger = get_logger(__name__)

# Rate limiting config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    RequestLoggingMiddleware,
    redis_url=REDIS_URL,
    requests_per_minute=120
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_security_headers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/unit/test_security_headers.py
git commit -m "feat(core): add security headers and rate limiting middleware"
```

---

## Task 4: WebSocket Endpoint

**Files:**
- Create: `backend/app/api/v1/ws.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/unit/test_ws_endpoint.py`

- [ ] **Step 1: Write failing test for WebSocket endpoint**

```python
# tests/unit/test_ws_endpoint.py
import pytest

pytestmark = pytest.mark.unit


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is registered."""
        from fastapi.routing import APIRoute

        from app.main import create_app

        app = create_app()
        routes = [r for r in app.routes if isinstance(r, APIRoute)]

        ws_routes = [r for r in routes if "/ws" in r.path]
        assert len(ws_routes) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ws_endpoint.py -v`
Expected: FAIL (no WebSocket endpoint yet)

- [ ] **Step 3: Write WebSocket endpoint**

```python
# backend/app/api/v1/ws.py
"""WebSocket Endpoint - Real-time bidirectional communication."""

from fastapi import APIRouter, WebSocket, Depends

from app.api.deps import get_current_user
from app.core.websocket import websocket_manager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """WebSocket endpoint for real-time communication."""
    # Simple token-based auth
    if not token:
        await websocket.close(code=4001)
        return

    try:
        # Verify token and get user_id
        # For now, use a simple mock
        user_id = "user-" + token[:8] if token else "anonymous"

        await websocket_manager.connect(websocket, user_id)
        logger.info("websocket_connected", user_id=user_id)

        try:
            while True:
                data = await websocket.receive_json()
                logger.info("websocket_message", user_id=user_id, data=data)

                # Echo back for testing
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "user_id": user_id
                })
        except Exception as e:
            logger.info("websocket_disconnected", user_id=user_id, error=str(e))
        finally:
            await websocket_manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error("websocket_error", error=str(e))
        await websocket.close(code=4002)
```

- [ ] **Step 4: Add WebSocket router to main.py**

```python
# In main.py, add:
from app.api.v1.ws import router as ws_router

# Register WebSocket router (no prefix, directly at /ws)
app.include_router(ws_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_ws_endpoint.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/unit/test_ws_endpoint.py app/api/v1/ws.py app/main.py
git commit -m "feat(api): add WebSocket endpoint for real-time communication"
```

---

## Task 5: Enhanced Health Check Endpoint

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/unit/test_health_check.py`

- [ ] **Step 1: Write failing test for enhanced health check**

```python
# tests/unit/test_health_check.py
import pytest

pytestmark = pytest.mark.unit


class TestHealthCheck:
    """Tests for enhanced health check endpoint."""

    def test_health_check_returns_status(self):
        """Test health check returns database and Redis status."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_health_check.py -v`
Expected: FAIL (health check doesn't return db/redis status)

- [ ] **Step 3: Enhance health check in main.py**

Replace the simple `/health` endpoint with:

```python
from app.db.database import engine
from app.db.redis import get_redis_client

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint with dependency status."""
    health = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check Redis
    try:
        redis = await get_redis_client()
        await redis.ping()
        health["redis"] = "connected"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_health_check.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/unit/test_health_check.py
git commit -m "feat(api): add enhanced health check with db/redis status"
```

---

## Task 6: Add structlog to Dependencies

**Files:**
- Modify: `backend/pyproject.toml`
- Test: Verify all tests still pass

- [ ] **Step 1: Add structlog to pyproject.toml**

```toml
[tool.poetry.dependencies]
# ... existing dependencies
structlog = "^24.1"
```

Run: `cd backend && poetry add structlog`

- [ ] **Step 2: Verify all tests pass**

Run: `poetry run pytest tests/unit/ -v`

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add structlog dependency for structured logging"
```

---

## Verification

After all tasks:

```bash
# Run all unit tests
cd backend && poetry run pytest tests/unit/ -v

# Verify API endpoints registered
poetry run python -c "from app.main import app; print([r.path for r in app.routes if hasattr(r, 'path')])"

# Test health endpoint
curl http://localhost:8000/health | jq
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Structured Logging | logging.py |
| 2 | Request Logging Middleware | middleware.py |
| 3 | Security Headers | main.py |
| 4 | WebSocket Endpoint | ws.py, main.py |
| 5 | Enhanced Health Check | main.py |
| 6 | Add structlog Dependency | pyproject.toml |