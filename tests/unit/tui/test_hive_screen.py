"""Tests for HiveScreen base class and ScreenContext."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hive.tui.screens import DataError, DataLoaded, HiveScreen, ScreenContext


class TestScreenContext:
    """Tests for ScreenContext class."""

    def test_db_property_raises_runtime_error(self) -> None:
        """ScreenContext.db raises RuntimeError with guidance."""
        base = MagicMock()
        app = MagicMock()
        screen = MagicMock()

        ctx = ScreenContext(base, app, screen)
        with pytest.raises(RuntimeError, match="Database access through ScreenContext"):
            _ = ctx.db

    def test_config_property_delegates_to_base(self) -> None:
        """ScreenContext.config returns base context config."""
        base = MagicMock()
        base.config = {"key": "value"}
        app = MagicMock()
        screen = MagicMock()

        ctx = ScreenContext(base, app, screen)
        assert ctx.config is base.config

    def test_output_property_delegates_to_base(self) -> None:
        """ScreenContext.output returns base context output."""
        base = MagicMock()
        base.output = MagicMock()
        app = MagicMock()
        screen = MagicMock()

        ctx = ScreenContext(base, app, screen)
        assert ctx.output is base.output

    @pytest.mark.asyncio
    async def test_navigate_calls_app_navigate_to(self) -> None:
        """ScreenContext.navigate calls app.navigate_to."""
        base = MagicMock()
        app = MagicMock()
        screen = MagicMock()

        ctx = ScreenContext(base, app, screen)
        await ctx.navigate("SettingsScreen")

        app.navigate_to.assert_called_once_with("SettingsScreen")

    @pytest.mark.asyncio
    async def test_go_back_calls_app_pop_screen(self) -> None:
        """ScreenContext.go_back calls app.pop_screen."""
        base = MagicMock()
        app = MagicMock()
        screen = MagicMock()

        ctx = ScreenContext(base, app, screen)
        await ctx.go_back()

        app.pop_screen.assert_called_once()

    def test_notify_calls_app_notify(self) -> None:
        """ScreenContext.notify calls app.notify with correct parameters."""
        base = MagicMock()
        app = MagicMock()
        screen = MagicMock()

        ctx = ScreenContext(base, app, screen)
        ctx.notify("Test message", title="Title", severity="warning", timeout=10.0)

        app.notify.assert_called_once_with(
            "Test message", title="Title", severity="warning", timeout=10.0
        )


class TestHiveScreen:
    """Tests for HiveScreen base class."""

    def test_ctx_property_raises_if_not_initialized(self) -> None:
        """Accessing ctx before initialization raises RuntimeError."""
        screen: HiveScreen[None] = HiveScreen()

        with pytest.raises(RuntimeError, match="context not initialized"):
            _ = screen.ctx

    def test_set_context_sets_ctx(self) -> None:
        """_set_context properly sets the screen context."""
        screen: HiveScreen[None] = HiveScreen()
        base = MagicMock()
        app = MagicMock()

        ctx = ScreenContext(base, app, screen)
        screen._set_context(ctx)

        assert screen.ctx is ctx

    def test_initial_data_is_empty_list(self) -> None:
        """HiveScreen.data defaults to empty list."""
        screen: HiveScreen[None] = HiveScreen()
        # data is a reactive property, defaults to empty list
        assert isinstance(screen.data, list)

    def test_initial_is_loading_is_false(self) -> None:
        """HiveScreen.is_loading defaults to False."""
        screen: HiveScreen[None] = HiveScreen()
        assert screen.is_loading is False

    def test_initial_error_is_none(self) -> None:
        """HiveScreen.error defaults to None."""
        screen: HiveScreen[None] = HiveScreen()
        assert screen.error is None


class TestDataMessages:
    """Tests for DataLoaded and DataError messages."""

    def test_data_loaded_stores_data(self) -> None:
        """DataLoaded message stores data attribute."""
        data = [{"id": 1}, {"id": 2}]
        msg = DataLoaded(data)
        assert msg.data == data

    def test_data_error_stores_error(self) -> None:
        """DataError message stores error string."""
        error = "Connection failed"
        msg = DataError(error)
        assert msg.error == error


class TestHiveScreenWithQueries:
    """Tests for HiveScreen with query bindings."""

    def test_query_names_can_be_set(self) -> None:
        """_query_names can be set on HiveScreen."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        screen = TestScreen()
        screen._query_names = ["list_items", "get_stats"]
        assert screen._query_names == ["list_items", "get_stats"]

    def test_registry_can_be_set(self) -> None:
        """_registry can be set on HiveScreen."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        screen = TestScreen()
        mock_registry = MagicMock()
        screen._registry = mock_registry
        assert screen._registry is mock_registry

    def test_screen_init_with_parameters(self) -> None:
        """HiveScreen accepts name, id, and classes parameters."""

        class TestScreen(HiveScreen[None]):
            """Test screen."""

        screen = TestScreen(name="test", id="test-screen", classes="panel")
        assert screen.name == "test"
        assert screen.id == "test-screen"


class TestHiveScreenEventHandlers:
    """Tests for HiveScreen event handlers."""

    def test_on_data_loaded_default_does_nothing(self) -> None:
        """Default on_data_loaded handler doesn't raise."""
        screen: HiveScreen[None] = HiveScreen()
        event = DataLoaded([{"id": 1}])
        # Should not raise
        screen.on_data_loaded(event)

    def test_on_data_error_default_does_nothing(self) -> None:
        """Default on_data_error handler doesn't raise."""
        screen: HiveScreen[None] = HiveScreen()
        event = DataError("Test error")
        # Should not raise
        screen.on_data_error(event)
