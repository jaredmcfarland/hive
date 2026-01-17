"""Test user-facing contract decorators."""

import pytest
from hive.errors import CommandError


class TestRequiresDecorator:
    """Tests for @requires precondition decorator."""

    @pytest.mark.asyncio
    async def test_passes_when_condition_met(self) -> None:
        """@requires allows execution when condition is True."""
        from hive.contracts import requires

        @requires(lambda ctx, x: x > 0, "x must be positive")
        async def fn(ctx, x: int) -> int:
            return x * 2

        result = await fn(None, 5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_raises_command_error_when_condition_fails(self) -> None:
        """@requires raises CommandError when condition is False."""
        from hive.contracts import requires

        @requires(lambda ctx, x: x > 0, "x must be positive")
        async def fn(ctx, x: int) -> int:
            return x * 2

        with pytest.raises(CommandError) as exc_info:
            await fn(None, -5)

        assert "x must be positive" in str(exc_info.value)


class TestEnsuresDecorator:
    """Tests for @ensures postcondition decorator."""

    @pytest.mark.asyncio
    async def test_passes_when_postcondition_met(self) -> None:
        """@ensures allows return when condition is True."""
        from hive.contracts import ensures

        @ensures(lambda ctx, x, result: result > x, "result must be greater than input")
        async def fn(ctx, x: int) -> int:
            return x * 2

        result = await fn(None, 5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_raises_command_error_when_postcondition_fails(self) -> None:
        """@ensures raises CommandError when postcondition is False."""
        from hive.contracts import ensures

        @ensures(lambda ctx, x, result: result > x, "result must be greater than input")
        async def fn(ctx, x: int) -> int:
            return x  # Returns same value, not greater

        with pytest.raises(CommandError) as exc_info:
            await fn(None, 5)

        assert "result must be greater than input" in str(exc_info.value)
