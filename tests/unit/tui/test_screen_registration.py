"""Contract tests for @screen decorator.

Tests verify that the @screen decorator correctly registers screens
with the application registry, including the queries parameter.
"""

from __future__ import annotations

import pytest

from hive import App
from hive.core.decorators import screen
from hive.errors import RegistrationError


class TestScreenDecoratorRegistration:
    """Tests for @screen decorator registration behavior."""

    def test_screen_decorator_registers_class(self) -> None:
        """Screen decorator registers the class with the registry."""
        app = App("test")

        @screen(app)
        class TestScreen:
            """Test screen."""

        assert "TestScreen" in app.registry.screens
        reg = app.registry.get_screen("TestScreen")
        assert reg is not None
        assert reg.cls is TestScreen
        assert reg.docstring == "Test screen."

    def test_screen_decorator_with_name_override(self) -> None:
        """Screen decorator allows name override."""
        app = App("test")

        @screen(app, name="custom_name")
        class TestScreen:
            """Test screen."""

        assert "custom_name" in app.registry.screens
        assert "TestScreen" not in app.registry.screens

    def test_screen_decorator_default_flag(self) -> None:
        """Screen decorator handles default flag correctly."""
        app = App("test")

        @screen(app, default=True)
        class DefaultScreen:
            """Default screen."""

        reg = app.registry.get_screen("DefaultScreen")
        assert reg is not None
        assert reg.default is True

    def test_screen_decorator_keybinding(self) -> None:
        """Screen decorator registers keybinding."""
        app = App("test")

        @screen(app, keybinding="d")
        class DashboardScreen:
            """Dashboard."""

        reg = app.registry.get_screen("DashboardScreen")
        assert reg is not None
        assert reg.keybinding == "d"

    def test_screen_decorator_queries_parameter(self) -> None:
        """Screen decorator registers query bindings."""
        app = App("test")

        @screen(app, queries=["list_tasks", "get_stats"])
        class TaskScreen:
            """Task screen with query binding."""

        reg = app.registry.get_screen("TaskScreen")
        assert reg is not None
        assert reg.queries == ["list_tasks", "get_stats"]

    def test_screen_decorator_empty_queries(self) -> None:
        """Screen decorator handles empty queries list."""
        app = App("test")

        @screen(app, queries=[])
        class EmptyQueryScreen:
            """Screen with no queries."""

        reg = app.registry.get_screen("EmptyQueryScreen")
        assert reg is not None
        assert reg.queries == []

    def test_screen_decorator_no_queries_defaults_empty(self) -> None:
        """Screen without queries parameter has empty queries list."""
        app = App("test")

        @screen(app)
        class NoQueryScreen:
            """Screen without queries."""

        reg = app.registry.get_screen("NoQueryScreen")
        assert reg is not None
        assert reg.queries == []


class TestScreenDecoratorValidation:
    """Tests for @screen decorator validation and error handling."""

    def test_duplicate_screen_name_raises_error(self) -> None:
        """Registering duplicate screen name raises RegistrationError."""
        app = App("test")

        @screen(app)
        class TestScreen:
            """First screen."""

        with pytest.raises(RegistrationError, match="already registered"):

            @screen(app)
            class TestScreen:
                """Duplicate screen."""

    def test_duplicate_default_screen_raises_error(self) -> None:
        """Only one default screen allowed per app."""
        app = App("test")

        @screen(app, default=True)
        class FirstDefault:
            """First default."""

        with pytest.raises(RegistrationError, match="already the default"):

            @screen(app, default=True)
            class SecondDefault:
                """Second default."""

    def test_duplicate_keybinding_raises_error(self) -> None:
        """Duplicate keybindings raise RegistrationError."""
        app = App("test")

        @screen(app, keybinding="d")
        class FirstScreen:
            """First screen."""

        with pytest.raises(RegistrationError, match="already used"):

            @screen(app, keybinding="d")
            class SecondScreen:
                """Second screen with same keybinding."""


class TestScreenDecoratorReturnValue:
    """Tests for @screen decorator return value behavior."""

    def test_screen_decorator_returns_class_unchanged(self) -> None:
        """Screen decorator returns the original class."""
        app = App("test")

        class OriginalClass:
            """Original class."""

            def method(self) -> str:
                return "test"

        decorated = screen(app)(OriginalClass)
        assert decorated is OriginalClass
        assert decorated().method() == "test"
