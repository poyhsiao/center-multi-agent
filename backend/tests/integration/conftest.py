"""Pytest configuration for integration tests."""
import pytest


@pytest.fixture(scope="session")
def redis_url():
    """Redis URL for integration tests."""
    return "redis://localhost:6379/0"
