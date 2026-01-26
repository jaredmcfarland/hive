"""Database initialization for Trakr."""

from __future__ import annotations

from hive.runtime.database import create_session_factory
from sqlmodel import SQLModel


async def init_database(database_url: str = "sqlite+aiosqlite:///trakr.db") -> None:
    """Initialize database tables.

    Creates all tables defined by SQLModel classes.

    Args:
        database_url: Database connection URL.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    # Import entities to register them with SQLModel
    from trakr import entities  # pyright: ignore[reportUnusedImport] # noqa: F401

    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await engine.dispose()


def get_session_factory(database_url: str = "sqlite+aiosqlite:///trakr.db"):
    """Get a session factory for the database.

    Args:
        database_url: Database connection URL.

    Returns:
        Async session factory.
    """
    return create_session_factory(database_url)
