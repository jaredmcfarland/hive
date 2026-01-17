"""Mock utilities for testing Hive commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockExecutionContext:
    """
    Mock ExecutionContext for testing commands without database.

    Example:
        async with MockExecutionContext() as ctx:
            result = await my_command(ctx, arg1="value")
            assert ctx.db.add.called
    """

    def __init__(self) -> None:
        self._session = AsyncMock()
        self._config = MagicMock()
        self._output = MagicMock()

    @property
    def db(self) -> AsyncMock:
        """Mock database session."""
        return self._session

    @property
    def config(self) -> MagicMock:
        """Mock configuration."""
        return self._config

    @property
    def output(self) -> MagicMock:
        """Mock output formatter."""
        return self._output

    async def __aenter__(self) -> MockExecutionContext:
        """Enter the mock context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the mock context (no-op)."""
        pass

    async def commit(self) -> None:
        """Mock commit (no-op)."""
        pass

    async def rollback(self) -> None:
        """Mock rollback (no-op)."""
        pass
