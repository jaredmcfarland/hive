"""Tests for database session management."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from hive.runtime.database import create_session_factory


class TestCreateSessionFactory:
    """Tests for create_session_factory function."""

    def test_sqlite_url_gets_aiosqlite_driver(self) -> None:
        """SQLite URLs get aiosqlite driver added."""
        factory = create_session_factory("sqlite:///test.db")
        assert factory is not None

    def test_sqlite_memory_url_gets_aiosqlite_driver(self) -> None:
        """SQLite memory URLs get aiosqlite driver added."""
        factory = create_session_factory("sqlite:///:memory:")
        assert factory is not None

    def test_sqlite_with_aiosqlite_unchanged(self) -> None:
        """SQLite URLs with aiosqlite already present are not modified."""
        factory = create_session_factory("sqlite+aiosqlite:///:memory:")
        assert factory is not None

    def test_echo_parameter_accepted(self) -> None:
        """Echo parameter is accepted."""
        factory = create_session_factory("sqlite:///:memory:", echo=True)
        assert factory is not None

    @pytest.mark.asyncio
    async def test_factory_creates_sessions(self) -> None:
        """Factory creates valid async sessions."""
        factory = create_session_factory("sqlite+aiosqlite:///:memory:")
        async with factory() as session:
            # Session should be usable
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
