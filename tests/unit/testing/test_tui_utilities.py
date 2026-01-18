"""Tests for TUI testing utilities.

These tests verify the testing helpers work correctly so users
can rely on them for their own tests.
"""

from __future__ import annotations

from typing import Any

import pytest

from hive.app import App
from hive.testing.tui import (
    MockScreenContext,
    TUITestHelper,
    create_test_app,
    register_test_command,
    register_test_query,
    register_test_screen,
)
from hive.tui.screens import HiveScreen


class TestMockScreenContext:
    """Tests for MockScreenContext."""

    def test_mock_context_has_db_property(self) -> None:
        """MockScreenContext provides a mock db property."""
        ctx = MockScreenContext()
        assert ctx.db is not None

    def test_mock_context_has_config_property(self) -> None:
        """MockScreenContext provides a mock config property."""
        ctx = MockScreenContext()
        assert ctx.config is not None

    def test_mock_context_has_output_property(self) -> None:
        """MockScreenContext provides a mock output property."""
        ctx = MockScreenContext()
        assert ctx.output is not None

    @pytest.mark.asyncio
    async def test_navigate_records_screen_name(self) -> None:
        """Navigate records the screen name."""
        ctx = MockScreenContext()
        await ctx.navigate("TestScreen")
        assert "TestScreen" in ctx.navigations

    @pytest.mark.asyncio
    async def test_go_back_increments_counter(self) -> None:
        """Go back increments the back counter."""
        ctx = MockScreenContext()
        assert ctx.back_count == 0
        await ctx.go_back()
        assert ctx.back_count == 1
        await ctx.go_back()
        assert ctx.back_count == 2

    def test_notify_records_message(self) -> None:
        """Notify records the message and severity."""
        ctx = MockScreenContext()
        ctx.notify("Test message", title="Title", severity="warning")
        assert len(ctx.notifications) == 1
        assert ctx.notifications[0] == ("Test message", "Title", "warning")


class TestCreateTestApp:
    """Tests for create_test_app function."""

    def test_creates_app_with_name(self) -> None:
        """Create test app with custom name."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(name="my-test-app", screens=[TestScreen])
        assert app.title == "my-test-app"

    def test_registers_screens(self) -> None:
        """Create test app registers provided screens."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(screens=[TestScreen])
        assert app._hive_registry.get_screen("TestScreen") is not None

    def test_registers_commands(self) -> None:
        """Create test app registers provided commands."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        async def test_cmd(ctx: Any) -> str:
            """Test command."""
            return "done"

        app = create_test_app(screens=[TestScreen], commands=[test_cmd])
        assert app._hive_registry.get_command("test_cmd") is not None

    def test_registers_queries(self) -> None:
        """Create test app registers provided queries."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        async def test_query(ctx: Any) -> list[str]:
            """Test query."""
            return []

        app = create_test_app(screens=[TestScreen], queries=[test_query])
        assert app._hive_registry.get_query("test_query") is not None

    def test_sets_default_screen(self) -> None:
        """Create test app sets the specified default screen."""

        class Screen1(HiveScreen[None]):
            """First screen."""

        class Screen2(HiveScreen[None]):
            """Second screen."""

        app = create_test_app(screens=[Screen1, Screen2], default_screen="Screen2")
        # The first screen registered without default_screen would be default
        # With default_screen="Screen2", Screen2 should be default
        assert app._default_screen == "Screen2"


class TestRegisterHelpers:
    """Tests for registration helper functions."""

    def test_register_test_screen(self) -> None:
        """Register test screen adds screen to registry."""
        app = App("test")

        class MyScreen(HiveScreen[None]):
            """Test screen."""

        result = register_test_screen(app, MyScreen, default=True)
        assert result is MyScreen
        reg = app.registry.get_screen("MyScreen")
        assert reg is not None
        assert reg.default is True

    def test_register_test_screen_with_keybinding(self) -> None:
        """Register test screen with keybinding."""
        app = App("test")

        class MyScreen(HiveScreen[None]):
            """Test screen."""

        register_test_screen(app, MyScreen, keybinding="m")
        reg = app.registry.get_screen("MyScreen")
        assert reg is not None
        assert reg.keybinding == "m"

    def test_register_test_screen_with_queries(self) -> None:
        """Register test screen with query bindings."""
        app = App("test")

        class MyScreen(HiveScreen[None]):
            """Test screen."""

        register_test_screen(app, MyScreen, queries=["list_items"])
        reg = app.registry.get_screen("MyScreen")
        assert reg is not None
        assert "list_items" in reg.queries

    def test_register_test_command(self) -> None:
        """Register test command adds command to registry."""
        app = App("test")

        async def my_command(ctx: Any) -> str:
            """Test command."""
            return "ok"

        result = register_test_command(app, my_command)
        assert result is my_command
        reg = app.registry.get_command("my_command")
        assert reg is not None

    def test_register_test_command_with_custom_name(self) -> None:
        """Register test command with custom name."""
        app = App("test")

        async def my_command(ctx: Any) -> str:
            """Test command."""
            return "ok"

        register_test_command(app, my_command, name="custom_name")
        reg = app.registry.get_command("custom_name")
        assert reg is not None

    def test_register_test_command_hidden(self) -> None:
        """Register test command as hidden."""
        app = App("test")

        async def my_command(ctx: Any) -> str:
            """Test command."""
            return "ok"

        register_test_command(app, my_command, hidden=True)
        reg = app.registry.get_command("my_command")
        assert reg is not None
        assert reg.hidden is True

    def test_register_test_query(self) -> None:
        """Register test query adds query to registry."""
        app = App("test")

        async def my_query(ctx: Any) -> list[str]:
            """Test query."""
            return []

        result = register_test_query(app, my_query)
        assert result is my_query
        reg = app.registry.get_query("my_query")
        assert reg is not None

    def test_register_test_query_with_custom_name(self) -> None:
        """Register test query with custom name."""
        app = App("test")

        async def my_query(ctx: Any) -> list[str]:
            """Test query."""
            return []

        register_test_query(app, my_query, name="custom_query")
        reg = app.registry.get_query("custom_query")
        assert reg is not None

    def test_register_test_query_with_cache_ttl(self) -> None:
        """Register test query with cache TTL."""
        app = App("test")

        async def my_query(ctx: Any) -> list[str]:
            """Test query."""
            return []

        register_test_query(app, my_query, cache_ttl=300)
        reg = app.registry.get_query("my_query")
        assert reg is not None
        assert reg.cache_ttl == 300


class TestTUITestHelper:
    """Tests for TUITestHelper async context manager."""

    @pytest.mark.asyncio
    async def test_helper_provides_pilot(self) -> None:
        """TUITestHelper provides access to Pilot."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(screens=[TestScreen])
        async with TUITestHelper(app) as helper:
            assert helper.pilot is not None

    @pytest.mark.asyncio
    async def test_helper_provides_app(self) -> None:
        """TUITestHelper provides access to app."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(screens=[TestScreen])
        async with TUITestHelper(app) as helper:
            assert helper.app is app

    @pytest.mark.asyncio
    async def test_helper_current_screen_name(self) -> None:
        """TUITestHelper reports current screen name."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(screens=[TestScreen])
        async with TUITestHelper(app) as helper:
            # Default screen should be mounted
            assert helper.current_screen_name == "TestScreen"

    @pytest.mark.asyncio
    async def test_helper_press_key(self) -> None:
        """TUITestHelper can press keys."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(screens=[TestScreen])
        async with TUITestHelper(app) as helper:
            # Should not raise
            await helper.press("q")

    @pytest.mark.asyncio
    async def test_helper_requires_context_for_pilot(self) -> None:
        """TUITestHelper raises if pilot accessed outside context."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        app = create_test_app(screens=[TestScreen])
        helper = TUITestHelper(app)
        with pytest.raises(RuntimeError, match="async context manager"):
            _ = helper.pilot
