"""Test MockExecutionContext for testing commands."""

import pytest


class TestMockExecutionContext:
    """Tests for MockExecutionContext."""

    @pytest.mark.asyncio
    async def test_can_use_as_async_context_manager(self) -> None:
        """MockExecutionContext works as async context manager."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx is not None

    @pytest.mark.asyncio
    async def test_has_db_property(self) -> None:
        """MockExecutionContext has mock db."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx.db is not None

    @pytest.mark.asyncio
    async def test_has_config_property(self) -> None:
        """MockExecutionContext has mock config."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx.config is not None

    @pytest.mark.asyncio
    async def test_has_output_property(self) -> None:
        """MockExecutionContext has mock output."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx.output is not None

    @pytest.mark.asyncio
    async def test_can_track_db_calls(self) -> None:
        """MockExecutionContext tracks db method calls."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            ctx.db.add("something")

        assert ctx.db.add.called
