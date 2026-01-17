"""
Hive Testing Utilities

Tools for testing Hive commands with property-based testing.

Example:
    from hive.testing import strategy_for_type, MockExecutionContext
    from hive.types import PositiveInt
    from hypothesis import given

    @given(x=strategy_for_type(PositiveInt))
    def test_my_function(x):
        assert my_function(x) > 0

    async def test_my_command():
        async with MockExecutionContext() as ctx:
            result = await my_command(ctx, arg="value")
            assert result is not None
"""

from hive.testing.strategies import strategy_for_type
from hive.testing.mocks import MockExecutionContext

__all__ = ["strategy_for_type", "MockExecutionContext"]
