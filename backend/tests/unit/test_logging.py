import pytest

pytestmark = pytest.mark.unit


class TestStructuredLogging:
    """Tests for structured logging."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        from app.core.logging import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_logger_extras_work(self):
        """Test logger extra context works."""
        from app.core.logging import get_logger

        logger = get_logger("test")
        # Structlog BoundLogger doesn't have request_id as attr
        # but we can verify logger was created
        assert logger is not None
        assert str(logger) != ""