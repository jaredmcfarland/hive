"""Base screen and context classes for Hive TUI.

Provides HiveScreen with reactive data binding and ScreenContext
for TUI-specific operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.worker import Worker, WorkerState

from hive.core.types import QueryBinding
from hive.tui.binding import QueryBindingExecutor

if TYPE_CHECKING:
    from hive.core.registry import ApplicationRegistry
    from hive.runtime.context import ExecutionContext
    from hive.tui.app import HiveApp


class DataLoaded(Message):
    """Posted when query data is successfully loaded."""

    def __init__(self, data: Any) -> None:
        """Initialize DataLoaded message.

        Args:
            data: The loaded data from the query.
        """
        self.data = data
        super().__init__()


class DataError(Message):
    """Posted when query loading fails."""

    def __init__(self, error: str) -> None:
        """Initialize DataError message.

        Args:
            error: The error message.
        """
        self.error = error
        super().__init__()


class ScreenContext:
    """TUI-specific execution context extension.

    Provides screen-aware operations like navigation and notifications
    while delegating database and service access to the base context.
    """

    def __init__(
        self,
        base_context: ExecutionContext,
        app: HiveApp,
        screen: HiveScreen[Any],
    ) -> None:
        """Initialize screen context.

        Args:
            base_context: The underlying execution context.
            app: The parent HiveApp.
            screen: The current screen.
        """
        self._base = base_context
        self._app = app
        self._screen = screen

    @property
    def db(self) -> Any:
        """Database session from base context."""
        return self._base.db

    @property
    def config(self) -> Any:
        """Application configuration from base context."""
        return self._base.config

    @property
    def output(self) -> Any:
        """Output formatter from base context."""
        return self._base.output

    @property
    def services(self) -> Any:
        """Service proxy from base context."""
        return self._base.services

    async def navigate(self, screen_name: str) -> None:
        """Navigate to a named screen.

        Args:
            screen_name: The name of the screen to navigate to.
        """
        self._app.navigate_to(screen_name)

    async def go_back(self) -> None:
        """Navigate to the previous screen."""
        self._app.pop_screen()

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: Literal["information", "warning", "error"] = "information",
        timeout: float = 5.0,
    ) -> None:
        """Show a notification toast.

        Args:
            message: The notification message.
            title: Optional title for the notification.
            severity: Severity level (information, warning, error).
            timeout: How long to show the notification.
        """
        self._app.notify(message, title=title, severity=severity, timeout=timeout)


class HiveScreen[T](Screen[T]):
    """Base class for Hive TUI screens with reactive data binding.

    Provides reactive properties for data, loading state, and errors.
    Automatically loads bound queries on mount.

    Attributes:
        data: Query results, updated reactively.
        loading: True while query is being loaded.
        error: Error message if query failed, None otherwise.
        ctx: ScreenContext for database, navigation, notifications.
    """

    # Reactive properties for data binding
    data: reactive[list[Any]] = reactive(list, init=False)
    is_loading: reactive[bool] = reactive(False)
    error: reactive[str | None] = reactive(None)

    # Query names bound to this screen (set by registry)
    _query_names: list[str] = []

    # Registry reference for query execution (set by HiveApp)
    _registry: ApplicationRegistry | None = None

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize the screen.

        Args:
            name: Optional screen name.
            id: Optional screen ID for CSS.
            classes: Optional CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._ctx: ScreenContext | None = None
        self._data_worker: Worker[Any] | None = None

    @property
    def ctx(self) -> ScreenContext:
        """Get the screen context.

        Returns:
            The ScreenContext for this screen.

        Raises:
            RuntimeError: If context not initialized.
        """
        if self._ctx is None:
            raise RuntimeError("Screen context not initialized. Use on_mount().")
        return self._ctx

    def _set_context(self, ctx: ScreenContext) -> None:
        """Set the screen context (called by HiveApp).

        Args:
            ctx: The screen context to use.
        """
        self._ctx = ctx

    async def on_mount(self) -> None:
        """Called when screen is mounted. Loads bound queries."""
        if self._query_names:
            await self.refresh_data()

    async def refresh_data(self) -> None:
        """Reload data from bound queries.

        Cancels any in-progress load and starts a new one.
        """
        # Cancel existing worker if running
        if self._data_worker and self._data_worker.state == WorkerState.RUNNING:
            self._data_worker.cancel()

        self.is_loading = True
        self.error = None

        # Start worker to load query
        self._data_worker = self.run_worker(
            self._load_queries(),
            exclusive=True,
            name="load_queries",
        )

    async def _load_queries(self) -> None:
        """Worker method to load all bound queries."""
        try:
            if not self._query_names or self._registry is None:
                self.post_message(DataLoaded(self.data))
                return

            # Create executor for this load
            executor = QueryBindingExecutor(self._registry)

            # Load the first query (primary binding)
            # Future: support multiple query bindings
            query_name = self._query_names[0]
            binding = QueryBinding(
                screen_name=self.__class__.__name__,
                query_name=query_name,
            )

            # Execute the query with a mock context for now
            # In full implementation, ScreenContext would be used
            result = await executor.execute(binding, ctx=self._ctx)

            # Update data reactive property
            if isinstance(result, list):
                self.data = result
            else:
                self.data = [result] if result is not None else []

            self.post_message(DataLoaded(self.data))
        except Exception as e:  # noqa: BLE001 - Catch all for worker error handling
            self.error = str(e)
            self.post_message(DataError(str(e)))
        finally:
            self.is_loading = False

    def on_data_loaded(self, event: DataLoaded) -> None:
        """Handle data loaded event.

        Override to customize behavior when data loads.

        Args:
            event: The DataLoaded message.
        """

    def on_data_error(self, event: DataError) -> None:
        """Handle data error event.

        Override to customize error handling.

        Args:
            event: The DataError message.
        """
