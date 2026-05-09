"""Async SQLAlchemy database configuration."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine as _create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


def create_async_engine(url: str | None = None) -> AsyncEngine:
    """Create async engine with connection pooling."""
    database_url = url or settings.database_url_with_fallback
    engine_kwargs = {}
    # Only set pool params for non-SQLite databases
    if not database_url.startswith("sqlite"):
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_pre_ping"] = True
    return _create_async_engine(database_url, **engine_kwargs)


async def get_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Get async session for dependency injection."""
    async with AsyncSession(engine) as session:
        yield session


# Dependency for FastAPI - uses default engine
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    engine = create_async_engine()
    async with AsyncSession(engine) as session:
        yield session


async def init_db(engine: AsyncEngine) -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db(engine: AsyncEngine) -> None:
    """Close database connections."""
    await engine.dispose()
