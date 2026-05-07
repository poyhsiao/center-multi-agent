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