"""TUI testing utilities for Hive applications.

Provides helpers for testing Textual-based TUI applications generated
by the Hive framework.

Public API:
    create_test_app: Create a minimal test TUI application
    MockScreenContext: Mock screen context for testing
    TUITestHelper: Async context manager for TUI testing

Example:
    from hive.testing.tui import create_test_app, TUITestHelper

    async def test_my_screen():
        app = create_test_app(
            screens=[MyScreen],
            commands=[my_command],
            queries=[my_query],
        )
        async with TUITestHelper(app) as helper:
            await helper.navigate_to("MyScreen")
            assert helper.current_screen_name == "MyScreen"
"""

from __future__ import annotations

import asyncio
import types
from typing import TYPE_CHECKING, Any, Self
from unittest.mock import AsyncMock, MagicMock

from textual.pilot import Pilot

from hive.app import App
from hive.core.decorators import command, query, screen
from hive.generators.tui import generate_tui_app
from hive.tui.app import HiveApp
from hive.tui.screens import HiveScreen

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = [
    "MockScreenContext",
    "TUITestHelper",
    "create_test_app",
    "register_test_command",
    "register_test_query",
    "register_test_screen",
]


class MockScreenContext:
    """Mock ScreenContext for testing screen behavior without full app.

    Provides mock implementations of navigation, notifications, and
    database access for isolated screen testing.

    Example:
        ctx = MockScreenContext()
        await my_screen_method(ctx)
        assert ctx.notifications == [("Success!", "information")]
    """

    def __init__(self) -> None:
        """Initialize mock screen context."""
        self._db = AsyncMock()
        self._config = MagicMock()
        self._output = MagicMock()
        self._notifications: list[tuple[str, str, str]] = []
        self._navigations: list[str] = []
        self._back_count = 0

    @property
    def db(self) -> AsyncMock:
        """Mock database session."""
        return self._db

    @property
    def config(self) -> MagicMock:
        """Mock configuration."""
        return self._config

    @property
    def output(self) -> MagicMock:
        """Mock output formatter."""
        return self._output

    @property
    def notifications(self) -> list[tuple[str, str, str]]:
        """List of (message, title, severity) notifications sent."""
        return self._notifications

    @property
    def navigations(self) -> list[str]:
        """List of screen names navigated to."""
        return self._navigations

    @property
    def back_count(self) -> int:
        """Number of times go_back was called."""
        return self._back_count

    async def navigate(self, screen_name: str) -> None:
        """Record navigation to a screen.

        Args:
            screen_name: Name of screen to navigate to.
        """
        self._navigations.append(screen_name)

    async def go_back(self) -> None:
        """Record back navigation."""
        self._back_count += 1

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: str = "information",
        timeout: float = 5.0,  # noqa: ARG002
    ) -> None:
        """Record a notification.

        Args:
            message: Notification message.
            title: Optional title.
            severity: Severity level.
            timeout: Display timeout (ignored in mock).
        """
        self._notifications.append((message, title, severity))


class TUITestHelper:
    """Async context manager for TUI testing.

    Wraps a HiveApp and provides convenient methods for testing
    navigation, command palette, and screen interactions.

    Example:
        async with TUITestHelper(app) as helper:
            await helper.press("ctrl+p")  # Open command palette
            await helper.type_text("add")
            await helper.press("enter")
    """

    def __init__(self, app: HiveApp) -> None:
        """Initialize test helper.

        Args:
            app: The HiveApp to test.
        """
        self._app = app
        self._pilot: Pilot[None] | None = None
        self._context: Any = None

    async def __aenter__(self) -> Self:
        """Enter the test context and start the app.

        Returns:
            Self for method chaining.
        """
        # run_test() returns an async context manager that yields Pilot
        self._context = self._app.run_test()
        self._pilot = await self._context.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the test context."""
        if hasattr(self, "_context"):
            await self._context.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def pilot(self) -> Pilot[None]:
        """Get the Textual Pilot instance.

        Returns:
            The Pilot for direct control.

        Raises:
            RuntimeError: If not in async context.
        """
        if self._pilot is None:
            msg = "TUITestHelper must be used as async context manager"
            raise RuntimeError(msg)
        return self._pilot

    @property
    def app(self) -> HiveApp:
        """Get the HiveApp being tested.

        Returns:
            The HiveApp instance.
        """
        return self._app

    @property
    def current_screen_name(self) -> str:
        """Get the name of the current screen.

        Returns:
            Current screen class name.
        """
        return type(self._app.screen).__name__

    async def press(self, key: str) -> None:
        """Press a key.

        Args:
            key: Key to press (e.g., "enter", "ctrl+p", "escape").
        """
        await self.pilot.press(key)

    async def type_text(self, text: str) -> None:
        """Type text into focused input.

        Args:
            text: Text to type.
        """
        for char in text:
            await self.pilot.press(char)

    async def navigate_to(self, screen_name: str) -> None:
        """Navigate to a named screen.

        Args:
            screen_name: Name of screen to navigate to.
        """
        self._app.navigate_to(screen_name)
        await self.pilot.pause()

    async def open_command_palette(self) -> None:
        """Open the command palette."""
        await self.press("ctrl+p")
        await self.pilot.pause()

    async def close_command_palette(self) -> None:
        """Close the command palette."""
        await self.press("escape")
        await self.pilot.pause()

    async def wait_for_loading(self, max_wait: float = 5.0) -> None:
        """Wait for loading state to complete.

        Args:
            max_wait: Maximum seconds to wait.
        """
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < max_wait:
            screen = self._app.screen
            if hasattr(screen, "is_loading") and not getattr(screen, "is_loading", True):
                return
            await asyncio.sleep(0.05)


def create_test_app(
    name: str = "test-app",
    *,
    screens: list[type[HiveScreen[Any]]] | None = None,
    commands: list[Callable[..., Awaitable[Any]]] | None = None,
    queries: list[Callable[..., Awaitable[Any]]] | None = None,
    default_screen: str | None = None,
) -> HiveApp:
    """Create a minimal test TUI application.

    Convenience function for creating a HiveApp with specified
    screens, commands, and queries for testing.

    Args:
        name: Application name.
        screens: Screen classes to register.
        commands: Command functions to register.
        queries: Query functions to register.
        default_screen: Name of default screen (first screen if None).

    Returns:
        Configured HiveApp ready for testing.

    Example:
        app = create_test_app(
            screens=[DashboardScreen, SettingsScreen],
            commands=[add_item, delete_item],
            queries=[list_items],
        )
    """
    app = App(name)

    # Register screens
    if screens:
        for i, screen_cls in enumerate(screens):
            is_default = default_screen == screen_cls.__name__ if default_screen else i == 0
            screen(app, default=is_default)(screen_cls)

    # Register commands
    if commands:
        for cmd_func in commands:
            command(app)(cmd_func)

    # Register queries
    if queries:
        for query_func in queries:
            query(app)(query_func)

    return generate_tui_app(app)


def register_test_screen(
    app: App,
    screen_cls: type[HiveScreen[Any]],
    *,
    default: bool = False,
    keybinding: str | None = None,
    queries: list[str] | None = None,
) -> type[HiveScreen[Any]]:
    """Register a screen class for testing.

    Args:
        app: The Hive App instance.
        screen_cls: Screen class to register.
        default: Whether this is the default screen.
        keybinding: Optional keybinding for navigation.
        queries: Query names to bind to screen.

    Returns:
        The registered screen class.
    """
    return screen(app, default=default, keybinding=keybinding, queries=queries)(screen_cls)


def register_test_command(
    app: App,
    cmd_func: Callable[..., Awaitable[Any]],
    *,
    name: str | None = None,
    hidden: bool = False,
) -> Callable[..., Awaitable[Any]]:
    """Register a command function for testing.

    Args:
        app: The Hive App instance.
        cmd_func: Command function to register.
        name: Optional custom command name.
        hidden: Whether to hide from command palette.

    Returns:
        The registered command function.
    """
    return command(app, name=name, hidden=hidden)(cmd_func)


def register_test_query(
    app: App,
    query_func: Callable[..., Awaitable[Any]],
    *,
    name: str | None = None,
    cache_ttl: int | None = None,
) -> Callable[..., Awaitable[Any]]:
    """Register a query function for testing.

    Args:
        app: The Hive App instance.
        query_func: Query function to register.
        name: Optional custom query name.
        cache_ttl: Cache time-to-live in seconds.

    Returns:
        The registered query function.
    """
    return query(app, name=name, cache_ttl=cache_ttl)(query_func)
