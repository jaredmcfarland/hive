"""High-level testing client for Hive applications.

This module provides TestClient, a user-friendly testing interface
that makes it easy to test Hive commands and queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from hive.app import App


@dataclass
class TestSession:
    """Internal session state for TestClient.

    Tracks captured output and invocation count during a test session.

    Attributes:
        captured_output: Lines of output captured during the session.
        invocation_count: Number of commands/queries invoked.
        last_result: Result of the most recent invocation.
    """

    captured_output: list[str] = field(default_factory=list)
    invocation_count: int = 0
    last_result: Any = None


class TestClient:
    """High-level testing interface for Hive applications.

    Provides a convenient way to test commands and queries without
    boilerplate setup. Uses MockExecutionContext internally for fast,
    isolated unit testing.

    Note:
        The `db_url` parameter is currently reserved for future use.
        This client always uses MockExecutionContext with mocked database
        operations (ctx.db is an AsyncMock). For integration tests requiring
        a real database, use MockExecutionContext directly with a real
        SQLModel session, or wait for real database support in a future version.

    Attributes:
        app: The Hive application being tested.
        services: Mock services to inject.
        db_url: Database URL (reserved for future real database support).

    Example:
        >>> from hive.testing import TestClient
        >>> from myapp import app
        >>>
        >>> async def test_create_task():
        ...     async with TestClient(app) as client:
        ...         result = await client.invoke("create_task", title="Test")
        ...         assert result.id is not None
        >>> async def test_with_mock_service():
        ...     mock_api = MagicMock()
        ...     async with TestClient(app, services={"api": mock_api}) as client:
        ...         await client.invoke("fetch_data")
        ...         mock_api.get.assert_called_once()
    """

    def __init__(
        self,
        app: App,
        *,
        services: dict[str, Any] | None = None,
        db_url: str = "sqlite+aiosqlite:///:memory:",
    ) -> None:
        """Initialize the test client.

        Args:
            app: Hive application to test.
            services: Dictionary of service mocks to inject.
            db_url: Reserved for future database support. Currently ignored;
                the client always uses MockExecutionContext with mocked db.
        """
        self.app = app
        self.services = services or {}
        self.db_url = db_url
        self._session: TestSession | None = None
        self._context: Any = None
        self._output_buffer: StringIO | None = None

    async def __aenter__(self) -> Self:
        """Enter the test context.

        Sets up the database and execution context.
        """
        self._session = TestSession()
        self._output_buffer = StringIO()
        self._context = await self._create_context()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the test context.

        Cleans up database connections and resources.
        """
        if self._context is not None:
            # Close database connection if we created one
            if hasattr(self._context, "db") and hasattr(self._context.db, "close"):
                await self._context.db.close()
        self._context = None
        self._session = None
        self._output_buffer = None

    async def invoke(self, command_name: str, **kwargs: Any) -> Any:
        """Execute a command by name.

        Looks up the command in the registry and executes it with the
        provided arguments.

        Args:
            command_name: Name of the command to execute.
            **kwargs: Arguments to pass to the command.

        Returns:
            The command's return value.

        Raises:
            ValueError: If the command is not found.
            Exception: Any exception raised by the command.

        Example:
            >>> async with TestClient(app) as client:
            ...     result = await client.invoke("create_task", title="My Task")
            ...     assert result.id is not None
        """
        if self._session is None or self._context is None:
            msg = "TestClient must be used as async context manager"
            raise RuntimeError(msg)

        # Find the command
        cmd_reg = self._find_command(command_name)
        if cmd_reg is None:
            available = [c.name for c in self.app.registry.list_commands()]
            msg = f"Command '{command_name}' not found. Available: {available}"
            raise ValueError(msg)

        # Execute the command
        try:
            result = await cmd_reg.func(self._context, **kwargs)
            self._session.invocation_count += 1
            self._session.last_result = result
            return result
        except Exception as e:
            # Provide helpful error message for validation failures
            self._enhance_error(e, command_name, kwargs)
            raise

    async def query(self, query_name: str, **kwargs: Any) -> Any:
        """Execute a query by name.

        Looks up the query in the registry and executes it with the
        provided arguments.

        Args:
            query_name: Name of the query to execute.
            **kwargs: Arguments to pass to the query.

        Returns:
            The query's return value.

        Raises:
            ValueError: If the query is not found.
            Exception: Any exception raised by the query.

        Example:
            >>> async with TestClient(app) as client:
            ...     tasks = await client.query("list_tasks", status="active")
            ...     assert len(tasks) > 0
        """
        if self._session is None or self._context is None:
            msg = "TestClient must be used as async context manager"
            raise RuntimeError(msg)

        # Find the query
        query_reg = self._find_query(query_name)
        if query_reg is None:
            available = [q.name for q in self.app.registry.list_queries()]
            msg = f"Query '{query_name}' not found. Available: {available}"
            raise ValueError(msg)

        # Execute the query
        try:
            result = await query_reg.func(self._context, **kwargs)
            self._session.invocation_count += 1
            self._session.last_result = result
            return result
        except Exception as e:
            self._enhance_error(e, query_name, kwargs)
            raise

    def get_output(self) -> list[str]:
        """Get captured output lines.

        Returns all output that was captured during the test session.

        Returns:
            List of output lines.

        Example:
            >>> async with TestClient(app) as client:
            ...     await client.invoke("hello", name="World")
            ...     output = client.get_output()
            ...     assert "Hello, World!" in output
        """
        if self._session is None:
            return []
        return self._session.captured_output.copy()

    @property
    def invocation_count(self) -> int:
        """Number of commands/queries invoked in this session."""
        if self._session is None:
            return 0
        return self._session.invocation_count

    @property
    def last_result(self) -> Any:
        """Result of the most recent invocation."""
        if self._session is None:
            return None
        return self._session.last_result

    def _find_command(self, name: str) -> Any:
        """Find a command registration by name."""
        for cmd in self.app.registry.list_commands():
            if cmd.name == name:
                return cmd
            if name in cmd.aliases:
                return cmd
        return None

    def _find_query(self, name: str) -> Any:
        """Find a query registration by name."""
        for query in self.app.registry.list_queries():
            if query.name == name:
                return query
        return None

    async def _create_context(self) -> Any:
        """Create an execution context for testing.

        Returns a mock context with service mocks injected.
        """
        from hive.testing.mocks import MockExecutionContext  # noqa: PLC0415

        ctx = MockExecutionContext()

        # Inject service mocks
        for name, mock in self.services.items():
            setattr(ctx, name, mock)

        # Capture output
        if self._output_buffer is not None and self._session is not None:
            original_output = ctx.output

            def capture_write(text: str) -> None:
                if self._session is not None:
                    self._session.captured_output.append(text)
                original_output.write(text)

            ctx.output.write = capture_write

        return ctx

    def _enhance_error(self, error: Exception, operation: str, kwargs: dict[str, Any]) -> None:
        """Enhance error messages with context for better debugging.

        Modifies the exception args to include helpful debugging info.
        """
        # Check for beartype validation errors
        error_str = str(error)
        if "beartype" in error_str.lower() or "type" in type(error).__name__.lower():
            # Add context about what was being called
            context = f"\n\nWhile calling '{operation}' with arguments: {kwargs}"
            if error.args:
                error.args = (error.args[0] + context,) + error.args[1:]
