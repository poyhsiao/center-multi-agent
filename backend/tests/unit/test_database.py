import pytest


@pytest.mark.asyncio
async def test_create_async_engine_sqlite():
    """Test create_async_engine with SQLite for unit testing."""
    from app.db.database import create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    assert engine is not None
    # Dispose sync to avoid async dispose issues with SQLite
    engine.sync_engine.dispose()


@pytest.mark.asyncio
async def test_get_session_context_manager():
    """Test that get_session yields a session properly."""
    from app.db.database import get_session, create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # get_session is an async generator, consume it with async for
    async for session in get_session(engine):
        assert session is not None
        break  # Just need one session to verify it works
    engine.sync_engine.dispose()


def test_base_declarative():
    """Test that Base can be used as declarative base."""
    from app.db.database import Base
    from sqlalchemy import Table, Column, Integer, String
    meta = Base.metadata
    test_table = Table("test", meta, Column("id", Integer, primary_key=True), Column("name", String))
    assert "test" in meta.tables
