"""Shared test fixtures for Trakr tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hive.runtime.config import AppSettings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# Import entities to register them with SQLModel metadata
import trakr.entities  # noqa: F401


@pytest.fixture
async def db_settings(tmp_path: Path):
    """Create settings with temporary database and initialize tables.

    Uses a file-based SQLite database so the connection persists across
    multiple engine instances.
    """
    db_file = tmp_path / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_file}"
    settings = AppSettings(database_url=database_url)

    # Create tables using the same URL
    engine = create_async_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()

    return settings


async def create_fresh_db() -> AppSettings:
    """Create a fresh temporary database with tables.

    Each call creates a new unique database file.
    """
    # Create a temporary file that will be cleaned up automatically
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()

    database_url = f"sqlite+aiosqlite:///{tmp.name}"
    settings = AppSettings(database_url=database_url)

    engine = create_async_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()

    return settings
