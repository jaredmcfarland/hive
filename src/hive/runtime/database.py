"""Database session management."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool


def create_session_factory(
    database_url: str,
    echo: bool = False,
    *,
    allow_concurrent: bool = False,
) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the given database URL.

    Args:
        database_url: Database connection URL.
        echo: If True, log all SQL statements.
        allow_concurrent: If True, use NullPool to allow concurrent sessions.
            Set this to True for TUI applications where multiple operations
            may run simultaneously.

    Returns:
        An async session factory.
    """
    # Handle SQLite specially for async support
    if database_url.startswith("sqlite"):
        # Ensure we're using the async driver
        if "aiosqlite" not in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # Use NullPool for concurrent access (TUI), StaticPool for CLI
        poolclass = NullPool if allow_concurrent else StaticPool

        engine = create_async_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=poolclass,
        )
    else:
        engine = create_async_engine(database_url, echo=echo)

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
