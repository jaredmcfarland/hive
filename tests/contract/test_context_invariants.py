"""Test ExecutionContext invariants enforced by deal."""

import pytest


class TestExecutionContextInvariants:
    """Tests for ExecutionContext deal invariants."""

    @pytest.mark.asyncio
    async def test_cannot_access_db_when_closed(self) -> None:
        """Accessing db after close raises error."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.config import AppSettings

        settings = AppSettings(database_url="sqlite+aiosqlite:///:memory:")

        async with ExecutionContext(settings=settings, command_name="test") as ctx:
            # Should work while open
            _ = ctx.db

        # After exit, context is closed - accessing db should fail
        # deal.pre will raise PreContractError
        with pytest.raises(Exception):  # deal.PreContractError
            _ = ctx.db

    @pytest.mark.asyncio
    async def test_cannot_commit_when_closed(self) -> None:
        """Calling commit after close raises error."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.config import AppSettings

        settings = AppSettings(database_url="sqlite+aiosqlite:///:memory:")

        async with ExecutionContext(settings=settings, command_name="test") as ctx:
            pass  # Normal exit

        with pytest.raises(Exception):
            await ctx.commit()

    @pytest.mark.asyncio
    async def test_cannot_commit_twice(self) -> None:
        """Calling commit after already committed raises error."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.config import AppSettings

        settings = AppSettings(database_url="sqlite+aiosqlite:///:memory:")

        async with ExecutionContext(settings=settings, command_name="test") as ctx:
            await ctx.commit()
            # Second commit should fail
            with pytest.raises(Exception):
                await ctx.commit()
