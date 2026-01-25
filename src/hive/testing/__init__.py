"""Hive Testing Utilities.

Tools for testing Hive commands with property-based testing.

Example:
    from hive.testing import strategy_for_type, MockExecutionContext, TestClient
    from hive.types import PositiveInt
    from hypothesis import given

    @given(x=strategy_for_type(PositiveInt))
    def test_my_function(x):
        assert my_function(x) > 0

    async def test_my_command():
        async with MockExecutionContext() as ctx:
            result = await my_command(ctx, arg="value")
            assert result is not None

TestClient for high-level testing:
    from hive.testing import TestClient

    async def test_create_task():
        async with TestClient(app) as client:
            result = await client.invoke("create_task", title="Test")
            assert result.id is not None

TUI Testing:
    from hive.testing import create_test_app, TUITestHelper

    async def test_my_screen():
        app = create_test_app(screens=[MyScreen])
        async with TUITestHelper(app) as helper:
            await helper.navigate_to("MyScreen")
"""

from hive.testing.client import TestClient as TestClient
from hive.testing.client import TestSession as TestSession
from hive.testing.conformance import ConformanceGenerator as ConformanceGenerator
from hive.testing.conformance import ConformanceGeneratorResult as ConformanceGeneratorResult
from hive.testing.conformance import ConformanceTestCase as ConformanceTestCase
from hive.testing.conformance import ContractInfo as ContractInfo
from hive.testing.mocks import MockExecutionContext
from hive.testing.properties import PropertyGenerator as PropertyGenerator
from hive.testing.properties import PropertyGeneratorResult as PropertyGeneratorResult
from hive.testing.properties import PropertyTestCase as PropertyTestCase
from hive.testing.strategies import strategy_for_type
from hive.testing.tui import (
    MockScreenContext,
    TUITestHelper,
    create_test_app,
    register_test_command,
    register_test_query,
    register_test_screen,
)

__all__ = [
    "ConformanceGenerator",
    "ConformanceGeneratorResult",
    "ConformanceTestCase",
    "ContractInfo",
    "MockExecutionContext",
    "MockScreenContext",
    "PropertyGenerator",
    "PropertyGeneratorResult",
    "PropertyTestCase",
    "TUITestHelper",
    "TestClient",
    "TestSession",
    "create_test_app",
    "register_test_command",
    "register_test_query",
    "register_test_screen",
    "strategy_for_type",
]
