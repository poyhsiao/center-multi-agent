"""Pytest configuration for integration tests."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.db.database import Base


@pytest_asyncio.fixture
async def db_engine():
    """Create async engine for testing with PostgreSQL."""
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5433/center_multi_agent_test",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create async session for testing."""
    async with AsyncSession(db_engine) as session:
        yield session


@pytest.fixture(scope="session")
def redis_url():
    """Redis URL for integration tests."""
    return "redis://localhost:6380/0"


@pytest_asyncio.fixture
async def redis_client(redis_url, monkeypatch):
    """Create async Redis client for tests."""
    import redis.asyncio as redis
    from app import config

    # Override settings.redis_url so app code uses correct port
    monkeypatch.setattr(config.settings, "redis_url", redis_url)

    client = redis.from_url(redis_url, decode_responses=True)
    yield client
    await client.flushdb()  # Clean up after test
    await client.close()
