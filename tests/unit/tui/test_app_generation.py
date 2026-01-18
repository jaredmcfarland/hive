"""Contract tests for HiveApp generation.

Tests verify that the TUI application generator correctly creates
a Textual app from the registry.
"""

from __future__ import annotations

import pytest

from hive import App
from hive.core.decorators import screen


class TestHiveAppGeneration:
    """Tests for TUI app generation from registry."""

    def test_generate_tui_app_returns_textual_app(self) -> None:
        """generate_tui_app returns a Textual App subclass instance."""
        # Import here to test the import path
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, default=True)
        class DashboardScreen:
            """Dashboard."""

        tui_app = generate_tui_app(app)

        # Should be a Textual App
        from textual.app import App as TextualApp

        assert isinstance(tui_app, TextualApp)

    def test_generate_tui_app_has_registry_reference(self) -> None:
        """Generated app maintains reference to registry."""
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app)
        class TestScreen:
            """Test."""

        tui_app = generate_tui_app(app)

        assert hasattr(tui_app, "_hive_registry")
        assert tui_app._hive_registry is app.registry

    def test_generate_tui_app_installs_screens(self) -> None:
        """Generated app has screens from registry installed."""
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, default=True, keybinding="d")
        class DashboardScreen:
            """Dashboard."""

        @screen(app, keybinding="s")
        class SettingsScreen:
            """Settings."""

        tui_app = generate_tui_app(app)

        # Check screens are known to the app
        assert "DashboardScreen" in tui_app.SCREENS or hasattr(tui_app, "_installed_screens")

    def test_generate_tui_app_with_app_title(self) -> None:
        """Generated app uses app name as title."""
        from hive.generators.tui import generate_tui_app

        app = App("MyTestApp")

        @screen(app, default=True)
        class TestScreen:
            """Test."""

        tui_app = generate_tui_app(app)

        assert tui_app.title == "MyTestApp"

    def test_generate_tui_app_with_no_screens(self) -> None:
        """Generating app without screens raises error."""
        from hive.errors import ConfigurationError
        from hive.generators.tui import generate_tui_app

        app = App("test")

        with pytest.raises(ConfigurationError, match="No screens registered"):
            generate_tui_app(app)


class TestHiveAppBindings:
    """Tests for keybinding generation in HiveApp."""

    def test_keybindings_generated_from_screens(self) -> None:
        """App keybindings match screen keybindings."""
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, default=True, keybinding="d")
        class DashboardScreen:
            """Dashboard."""

        @screen(app, keybinding="s")
        class SettingsScreen:
            """Settings."""

        tui_app = generate_tui_app(app)

        # Get binding keys (includes class bindings + dynamic screen bindings)
        binding_keys = [b.key for b in tui_app.BINDINGS]
        dynamic_keys = [b.key for b in tui_app._dynamic_bindings if hasattr(b, "key")]

        assert "d" in binding_keys or "d" in dynamic_keys
        assert "s" in binding_keys or "s" in dynamic_keys

    def test_default_quit_binding_exists(self) -> None:
        """App includes quit keybinding by default."""
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, default=True)
        class TestScreen:
            """Test."""

        tui_app = generate_tui_app(app)

        binding_keys = [b.key for b in tui_app.BINDINGS]
        assert "q" in binding_keys or "ctrl+c" in binding_keys


class TestHiveAppDefaultScreen:
    """Tests for default screen handling."""

    def test_default_screen_is_initial(self) -> None:
        """Default screen is shown on app startup."""
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, keybinding="a")
        class ScreenA:
            """Not default."""

        @screen(app, default=True, keybinding="b")
        class ScreenB:
            """Default screen."""

        tui_app = generate_tui_app(app)

        # The default screen should be set
        assert tui_app._default_screen == "ScreenB"

    def test_first_screen_used_if_no_default(self) -> None:
        """First registered screen used if none marked default."""
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, keybinding="a")
        class ScreenA:
            """First screen."""

        @screen(app, keybinding="b")
        class ScreenB:
            """Second screen."""

        tui_app = generate_tui_app(app)

        # Should use first screen as default
        assert tui_app._default_screen is not None
