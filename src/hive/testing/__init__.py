"""
Hive Testing Utilities

Tools for testing Hive commands with property-based testing.

Example:
    from hive.testing import strategy_for_type
    from hive.types import PositiveInt
    from hypothesis import given

    @given(x=strategy_for_type(PositiveInt))
    def test_my_function(x):
        assert my_function(x) > 0
"""

from hive.testing.strategies import strategy_for_type

__all__ = ["strategy_for_type"]
