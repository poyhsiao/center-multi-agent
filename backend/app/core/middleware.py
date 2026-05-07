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
            import redis.asyncio as aioredis
            self._redis_client = aioredis.from_url(self.redis_url)
        return self._redis_client