"""Unit tests for TestClient.

Tests that TestClient provides a convenient testing interface
for Hive applications.
"""

import pytest


class TestTestClient:
    """Unit tests for TestClient class."""

    @pytest.mark.asyncio
    async def test_client_initialization(self) -> None:
        """TestClient initializes with app."""
        from hive.app import App
        from hive.testing import TestClient

        app = App("test-app")
        client = TestClient(app)

        assert client.app is app
        assert client.services == {}
        assert client.db_url == "sqlite+aiosqlite:///:memory:"

    @pytest.mark.asyncio
    async def test_client_as_context_manager(self) -> None:
        """TestClient works as async context manager."""
        from hive.app import App
        from hive.testing import TestClient

        app = App("test-app")

        async with TestClient(app) as client:
            assert client._session is not None
            assert client._context is not None

    @pytest.mark.asyncio
    async def test_invoke_command(self) -> None:
        """invoke() executes commands by name."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("test-app")

        @command(app)
        async def greet(ctx: ExecutionContext, name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        async with TestClient(app) as client:
            result = await client.invoke("greet", name="World")
            assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_invoke_command_not_found(self) -> None:
        """invoke() raises ValueError for unknown commands."""
        from hive.app import App
        from hive.testing import TestClient

        app = App("test-app")

        async with TestClient(app) as client:
            with pytest.raises(ValueError, match="not found"):
                await client.invoke("nonexistent_command")

    @pytest.mark.asyncio
    async def test_query_method(self) -> None:
        """query() executes queries by name."""
        from hive.app import App
        from hive.core.decorators import query
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("test-app")

        @query(app)
        async def get_value(ctx: ExecutionContext) -> int:
            """Get a value."""
            return 42

        async with TestClient(app) as client:
            result = await client.query("get_value")
            assert result == 42

    @pytest.mark.asyncio
    async def test_query_not_found(self) -> None:
        """query() raises ValueError for unknown queries."""
        from hive.app import App
        from hive.testing import TestClient

        app = App("test-app")

        async with TestClient(app) as client:
            with pytest.raises(ValueError, match="not found"):
                await client.query("nonexistent_query")

    @pytest.mark.asyncio
    async def test_invocation_count(self) -> None:
        """invocation_count tracks number of invocations."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("test-app")

        @command(app)
        async def noop(ctx: ExecutionContext) -> None:
            """Do nothing."""

        async with TestClient(app) as client:
            assert client.invocation_count == 0
            await client.invoke("noop")
            assert client.invocation_count == 1
            await client.invoke("noop")
            assert client.invocation_count == 2

    @pytest.mark.asyncio
    async def test_last_result(self) -> None:
        """last_result contains most recent return value."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("test-app")

        @command(app)
        async def return_value(ctx: ExecutionContext, val: int) -> int:
            """Return the value."""
            return val

        async with TestClient(app) as client:
            assert client.last_result is None
            await client.invoke("return_value", val=10)
            assert client.last_result == 10
            await client.invoke("return_value", val=20)
            assert client.last_result == 20

    @pytest.mark.asyncio
    async def test_service_mock_injection(self) -> None:
        """Services can be mocked and injected."""
        from unittest.mock import MagicMock

        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("test-app")

        @command(app)
        async def use_service(ctx: ExecutionContext) -> str:
            """Use an external service."""
            return ctx.api_client.fetch()  # type: ignore[attr-defined]

        mock_api = MagicMock()
        mock_api.fetch.return_value = "mocked data"

        async with TestClient(app, services={"api_client": mock_api}) as client:
            result = await client.invoke("use_service")
            assert result == "mocked data"
            mock_api.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_requires_context_manager(self) -> None:
        """invoke() fails outside context manager."""
        from hive.app import App
        from hive.testing import TestClient

        app = App("test-app")
        client = TestClient(app)

        with pytest.raises(RuntimeError, match="context manager"):
            await client.invoke("anything")


class TestTestSession:
    """Unit tests for TestSession dataclass."""

    def test_session_default_values(self) -> None:
        """TestSession has correct default values."""
        from hive.testing import TestSession

        session = TestSession()

        assert session.captured_output == []
        assert session.invocation_count == 0
        assert session.last_result is None

    def test_session_mutable_output(self) -> None:
        """captured_output list is mutable."""
        from hive.testing import TestSession

        session = TestSession()
        session.captured_output.append("Hello")

        assert session.captured_output == ["Hello"]
