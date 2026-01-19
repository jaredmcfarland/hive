"""Integration tests for full TUI application.

Tests verify screen navigation and end-to-end TUI behavior
using Textual's testing pilot.
"""

from __future__ import annotations

import pytest

from hive import App
from hive.core.decorators import screen


@pytest.fixture
def sample_app() -> App:
    """Create a sample app with multiple screens."""
    from hive.tui.screens import HiveScreen

    app = App("sample")

    @screen(app, default=True, keybinding="d")
    class DashboardScreen(HiveScreen[None]):
        """Dashboard screen."""

    @screen(app, keybinding="s")
    class SettingsScreen(HiveScreen[None]):
        """Settings screen."""

    @screen(app, keybinding="h")
    class HelpScreen(HiveScreen[None]):
        """Help screen."""

    return app


class TestScreenNavigation:
    """Integration tests for screen navigation."""

    @pytest.mark.asyncio
    async def test_navigate_via_keybinding(self, sample_app: App) -> None:
        """Pressing keybinding navigates to corresponding screen."""
        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(sample_app)

        async with tui_app.run_test() as pilot:
            # Should start on dashboard (default)
            assert "Dashboard" in str(type(tui_app.screen).__name__)

            # Navigate to settings
            await pilot.press("s")
            await pilot.pause()

            assert "Settings" in str(type(tui_app.screen).__name__)

    @pytest.mark.asyncio
    async def test_navigate_between_multiple_screens(self, sample_app: App) -> None:
        """Can navigate between all registered screens."""
        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(sample_app)

        async with tui_app.run_test() as pilot:
            # Dashboard -> Settings -> Help -> Dashboard
            await pilot.press("s")
            await pilot.pause()
            assert "Settings" in str(type(tui_app.screen).__name__)

            await pilot.press("h")
            await pilot.pause()
            assert "Help" in str(type(tui_app.screen).__name__)

            await pilot.press("d")
            await pilot.pause()
            assert "Dashboard" in str(type(tui_app.screen).__name__)

    @pytest.mark.asyncio
    async def test_quit_keybinding_exits_app(self, sample_app: App) -> None:
        """Pressing quit keybinding exits the application."""
        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(sample_app)

        async with tui_app.run_test() as pilot:
            await pilot.press("q")
            # App should be exiting
            assert tui_app._exit is True or tui_app.return_code is not None


class TestScreenLifecycle:
    """Tests for screen lifecycle events."""

    @pytest.mark.asyncio
    async def test_screen_mounts_on_navigation(self) -> None:
        """Screen on_mount is called when navigated to."""
        app = App("test")
        mount_called = []

        # We need to create a proper HiveScreen subclass
        # This will work once HiveScreen is implemented
        from hive.tui.screens import HiveScreen

        @screen(app, default=True, keybinding="a")
        class ScreenA(HiveScreen):
            """Screen A."""

            async def on_mount(self) -> None:
                mount_called.append("A")

        @screen(app, keybinding="b")
        class ScreenB(HiveScreen):
            """Screen B."""

            async def on_mount(self) -> None:
                mount_called.append("B")

        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            # Initial mount
            await pilot.pause()
            assert "A" in mount_called

            # Navigate to B
            await pilot.press("b")
            await pilot.pause()
            assert "B" in mount_called


class TestTUIAppConfiguration:
    """Tests for TUI app configuration."""

    @pytest.mark.asyncio
    async def test_app_has_header_and_footer(self) -> None:
        """Generated app includes HiveHeader and HiveFooter."""
        app = App("test")

        from textual.app import ComposeResult

        from hive.tui.screens import HiveScreen
        from hive.tui.widgets import HiveFooter, HiveHeader

        @screen(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen with standard layout."""

            def compose(self) -> ComposeResult:
                yield HiveHeader()
                yield HiveFooter()

        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Query for widgets on the current screen
            current_screen = tui_app.screen
            header = current_screen.query_one(HiveHeader)
            footer = current_screen.query_one(HiveFooter)

            assert header is not None
            assert footer is not None


class TestDataLoadingFlow:
    """Integration tests for query data loading flow (US2)."""

    @pytest.mark.asyncio
    async def test_screen_loads_data_on_mount(self) -> None:
        """Screen with bound query loads data automatically on mount."""
        from typing import Any

        from hive.core.decorators import query
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @query(app)
        async def get_items(ctx: Any) -> list[dict[str, str]]:
            """Get all items."""
            return [{"id": "1", "name": "Item A"}, {"id": "2", "name": "Item B"}]

        @screen(app, default=True, queries=["get_items"])
        class DataScreen(HiveScreen[None]):
            """Screen that loads data."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            current_screen = tui_app.screen
            # Data should be loaded
            assert current_screen.data is not None
            assert len(current_screen.data) == 2
            assert current_screen.data[0]["name"] == "Item A"

    @pytest.mark.asyncio
    async def test_screen_shows_loading_then_data(self) -> None:
        """Screen transitions from loading to data display."""
        import asyncio
        from typing import Any

        from hive.core.decorators import query
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")
        states_observed: list[str] = []

        @query(app)
        async def slow_query(ctx: Any) -> list[dict[str, str]]:
            """Slow query for testing loading state."""
            await asyncio.sleep(0.05)  # Small delay
            return [{"id": "1", "name": "Loaded"}]

        @screen(app, default=True, queries=["slow_query"])
        class LoadingStateScreen(HiveScreen[None]):
            """Screen tracking loading states."""

            def watch_is_loading(self, loading: bool) -> None:
                """Track loading state changes."""
                if loading:
                    states_observed.append("loading")
                else:
                    states_observed.append("loaded")

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            # Wait for loading cycle
            await pilot.pause()
            await asyncio.sleep(0.1)
            await pilot.pause()

            # Should have observed loading then loaded states
            assert "loading" in states_observed
            assert "loaded" in states_observed

    @pytest.mark.asyncio
    async def test_empty_query_results_display_empty_state(self) -> None:
        """Screen handles empty query results appropriately."""
        from typing import Any

        from hive.core.decorators import query
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @query(app)
        async def empty_query(ctx: Any) -> list[dict[str, str]]:
            """Query returning empty results."""
            return []

        @screen(app, default=True, queries=["empty_query"])
        class EmptyScreen(HiveScreen[None]):
            """Screen with empty data."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            current_screen = tui_app.screen
            assert current_screen.data == []
            assert current_screen.error is None

    @pytest.mark.asyncio
    async def test_query_error_sets_error_state(self) -> None:
        """Screen shows error when query fails."""
        from typing import Any

        from hive.core.decorators import query
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @query(app)
        async def failing_query(ctx: Any) -> list[dict[str, str]]:
            """Query that fails."""
            raise RuntimeError("Database connection failed")

        @screen(app, default=True, queries=["failing_query"])
        class ErrorScreen(HiveScreen[None]):
            """Screen with failing query."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            current_screen = tui_app.screen
            assert current_screen.error is not None
            assert "Database connection failed" in current_screen.error

    @pytest.mark.asyncio
    async def test_refresh_data_reloads_query(self) -> None:
        """Calling refresh_data triggers query reload."""
        from typing import Any

        from hive.core.decorators import query
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")
        call_count = 0

        @query(app)
        async def counting_query(ctx: Any) -> list[dict[str, int]]:
            """Query that counts invocations."""
            nonlocal call_count
            call_count += 1
            return [{"count": call_count}]

        @screen(app, default=True, queries=["counting_query"])
        class RefreshScreen(HiveScreen[None]):
            """Screen for testing refresh."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            initial_count = call_count

            current_screen = tui_app.screen
            await current_screen.refresh_data()
            await pilot.pause()

            # Query should have been called again
            assert call_count > initial_count

    @pytest.mark.asyncio
    async def test_data_loaded_event_fires(self) -> None:
        """DataLoaded event fires when query completes."""
        from typing import Any

        from hive.core.decorators import query
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import DataLoaded, HiveScreen

        app = App("test")
        data_loaded_events: list[DataLoaded] = []

        @query(app)
        async def simple_query(ctx: Any) -> list[dict[str, str]]:
            """Simple query."""
            return [{"id": "1"}]

        @screen(app, default=True, queries=["simple_query"])
        class EventScreen(HiveScreen[None]):
            """Screen tracking events."""

            def on_data_loaded(self, event: DataLoaded) -> None:
                """Capture data loaded events."""
                data_loaded_events.append(event)

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # DataLoaded should have been posted
            assert len(data_loaded_events) >= 1


class TestCommandPaletteExecution:
    """Integration tests for command palette execution flow (US4, T051)."""

    @pytest.mark.asyncio
    async def test_command_palette_opens_with_ctrl_p(self) -> None:
        """Pressing Ctrl+P opens the command palette."""
        from textual.command import CommandPalette as TextualCommandPalette

        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        from hive.core.decorators import command

        @command(app)
        async def test_command(ctx: object) -> str:
            return "executed"

        @screen(app, default=True)
        class MainScreen(HiveScreen[None]):
            """Main screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Press Ctrl+P to open palette (Textual's default binding)
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Textual's CommandPalette is a modal screen, check screen type
            assert isinstance(tui_app.screen, TextualCommandPalette)

    @pytest.mark.asyncio
    async def test_command_execution_via_palette(self) -> None:
        """Selecting a command and submitting parameters executes it."""
        from typing import Any

        from hive.core.decorators import command
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")
        execution_results: list[str] = []

        @command(app)
        async def greet(ctx: Any, name: str = "World") -> str:
            result = f"Hello, {name}!"
            execution_results.append(result)
            return result

        @screen(app, default=True)
        class MainScreen(HiveScreen[None]):
            """Main screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open palette (Textual's built-in command palette)
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Type to filter to our command
            await pilot.press("g", "r", "e", "e", "t")
            await pilot.pause()

            # Select the command (Enter on highlighted command)
            await pilot.press("enter")
            await pilot.pause()

            # Tab to the submit button and press Enter
            await pilot.press("tab")  # Move to submit button
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Command should have been executed
            assert len(execution_results) >= 1
            assert "Hello" in execution_results[0]

    @pytest.mark.asyncio
    async def test_command_result_shows_notification(self) -> None:
        """Command execution result displays as notification."""
        from typing import Any

        from hive.core.decorators import command
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @command(app)
        async def notify_test(ctx: Any) -> str:
            return "Success message"

        @screen(app, default=True)
        class MainScreen(HiveScreen[None]):
            """Main screen."""

        tui_app = generate_tui_app(app)
        notifications_shown: list[str] = []

        # Patch notify to capture notifications
        original_notify = tui_app.notify

        def capture_notify(message: str, *args: object, **kwargs: object) -> object:
            notifications_shown.append(message)
            return original_notify(message, *args, **kwargs)

        tui_app.notify = capture_notify  # type: ignore[method-assign]

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Execute command via palette
            await pilot.press("ctrl+p")
            await pilot.pause()
            await pilot.press("enter")  # Select command
            await pilot.pause()
            await pilot.press("enter")  # Submit (no params)
            await pilot.pause()

            # Should have shown a notification
            assert len(notifications_shown) >= 1

    @pytest.mark.asyncio
    async def test_command_error_shows_error_notification(self) -> None:
        """Command execution error displays as error notification."""
        from typing import Any

        from hive.core.decorators import command
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @command(app)
        async def failing_command(ctx: Any) -> str:
            raise ValueError("Something went wrong")

        @screen(app, default=True)
        class MainScreen(HiveScreen[None]):
            """Main screen."""

        tui_app = generate_tui_app(app)
        error_notifications: list[str] = []

        # Patch notify to capture error notifications
        original_notify = tui_app.notify

        def capture_notify(
            message: str, *args: object, severity: str = "information", **kwargs: object
        ) -> object:
            if severity == "error":
                error_notifications.append(message)
            return original_notify(message, *args, severity=severity, **kwargs)

        tui_app.notify = capture_notify  # type: ignore[method-assign]

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Execute failing command via palette
            await pilot.press("ctrl+p")
            await pilot.pause()
            await pilot.press("enter")  # Select command
            await pilot.pause()
            await pilot.press("enter")  # Submit
            await pilot.pause()

            # Should have shown an error notification
            assert len(error_notifications) >= 1
            assert "went wrong" in error_notifications[0]

    @pytest.mark.asyncio
    async def test_palette_search_filters_commands(self) -> None:
        """Typing in palette search filters the command list."""
        from typing import Any

        from textual.command import CommandPalette as TextualCommandPalette

        from hive.core.decorators import command
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")
        executed_commands: list[str] = []

        @command(app)
        async def create_user(ctx: Any, name: str = "test") -> dict[str, str]:
            executed_commands.append("create_user")
            return {"name": name}

        @command(app)
        async def delete_user(ctx: Any, user_id: int = 1) -> None:
            executed_commands.append("delete_user")

        @command(app)
        async def list_items(ctx: Any) -> list[str]:
            executed_commands.append("list_items")
            return []

        @screen(app, default=True)
        class MainScreen(HiveScreen[None]):
            """Main screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open Textual's built-in command palette
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Verify palette is open (it's a modal screen)
            assert isinstance(tui_app.screen, TextualCommandPalette)

            # Type to filter commands - "delete" should filter to delete_user
            await pilot.press("d", "e", "l", "e", "t", "e")
            await pilot.pause()

            # Select and execute the filtered command
            await pilot.press("enter")
            await pilot.pause()

            # Tab to submit button and submit the modal form
            await pilot.press("tab")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Only delete_user should have been executed (the filtered result)
            assert "delete_user" in executed_commands
            assert "list_items" not in executed_commands

    @pytest.mark.asyncio
    async def test_command_uses_same_execution_path_as_cli(self) -> None:
        """Command executed via palette uses same path as CLI execution."""
        from typing import Any

        from hive.core.decorators import command
        from hive.generators.tui import generate_tui_app
        from hive.runtime.context import ExecutionContext
        from hive.tui.screens import HiveScreen

        app = App("test")
        context_received: list[object] = []

        @command(app)
        async def context_aware_cmd(ctx: Any) -> str:
            context_received.append(ctx)
            return "done"

        @screen(app, default=True)
        class MainScreen(HiveScreen[None]):
            """Main screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Execute via palette
            await pilot.press("ctrl+p")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Command should have received an ExecutionContext
            assert len(context_received) >= 1
            # Verify it's a proper context (has expected attributes)
            ctx = context_received[0]
            assert hasattr(ctx, "output") or isinstance(ctx, ExecutionContext)
