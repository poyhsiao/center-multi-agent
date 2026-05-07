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