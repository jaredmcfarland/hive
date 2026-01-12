"""Shared pytest fixtures for Hive tests."""

import os
import tempfile
from collections.abc import Generator

import pytest


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Provide a temporary database path for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_db_url(temp_db_path: str) -> str:
    """Provide a SQLite database URL for testing."""
    return f"sqlite+aiosqlite:///{temp_db_path}"


@pytest.fixture
def env_override():
    """Context manager to temporarily override environment variables."""
    original = {}

    def _override(**kwargs):
        for key, value in kwargs.items():
            if key in os.environ:
                original[key] = os.environ[key]
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    yield _override

    # Restore original values
    for key, value in original.items():
        os.environ[key] = value
