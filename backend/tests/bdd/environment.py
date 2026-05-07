"""Behave environment configuration."""
import os
from unittest.mock import MagicMock, patch
from behave import fixture, use_fixture

from app.services.auth_service import UserRepository
from app.core.security import sign_refresh_token


# Mock user data store for tests
_MOCK_USERS: dict[str, dict] = {}
_REVOKED_TOKENS: set[str] = {}


def clear_mock_data():
    """Clear all mock data between scenarios."""
    global _MOCK_USERS, _REVOKED_TOKENS
    _MOCK_USERS = {}
    _REVOKED_TOKENS = set()


@fixture
def app_client(context):
    """Provide test client fixture with mocked dependencies."""
    clear_mock_data()

    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.hset = MagicMock(return_value=True)
    mock_redis.hget = MagicMock(return_value=None)
    mock_redis.exists = MagicMock(return_value=0)
    mock_redis.setex = MagicMock(return_value=True)
    mock_redis.expire = MagicMock(return_value=True)

    with patch("app.db.redis.get_redis_client", return_value=mock_redis):
        context.mock_redis = mock_redis
        context.mock_users = _MOCK_USERS
        context.revoked_tokens = _REVOKED_TOKENS
        context.fingerprints = {}  # device_id -> fingerprint
        yield


@fixture
def mock_user_repository(context):
    """Provide a mock user repository."""
    from app.services.auth_service import UserRepository

    class MockUserRepo(UserRepository):
        def __init__(self, users_store: dict):
            self._users = users_store

        def find_by_email(self, email: str):
            return self._users.get(email)

    return MockUserRepo(_MOCK_USERS)


def before_all(context):
    """Setup before all features."""
    os.environ.setdefault("TESTING", "true")
    use_fixture(app_client, context)


def before_feature(context, feature):
    """Setup before each feature."""
    pass


def before_scenario(context, scenario):
    """Setup before each scenario."""
    clear_mock_data()


def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    pass


def after_feature(context, feature):
    """Cleanup after each feature."""
    pass


def after_all(context):
    """Cleanup after all features."""
    pass
