"""Contract tests for ApplicationRegistry.

These tests verify the public API contract for the registry
per the contracts/public-api.md specification.
"""

import pytest


class TestRegistryQueryMethods:
    """Tests for registry query methods (T012)."""

    def test_get_command_returns_registration(self) -> None:
        """get_command returns CommandRegistration for registered command."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def my_command(ctx) -> None:
            """A command."""
            pass

        reg = app.registry.get_command("my_command")
        assert reg is not None
        assert reg.name == "my_command"

    def test_get_command_returns_none_for_unknown(self) -> None:
        """get_command returns None for unregistered command."""
        from hive import App

        app = App(name="test-app")
        assert app.registry.get_command("nonexistent") is None

    def test_list_commands_returns_all_commands(self) -> None:
        """list_commands returns all registered commands."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def cmd1(ctx) -> None:
            pass

        @command(app)
        async def cmd2(ctx) -> None:
            pass

        commands = app.registry.list_commands()
        assert len(commands) == 2
        names = [c.name for c in commands]
        assert "cmd1" in names
        assert "cmd2" in names

    def test_list_commands_empty_registry(self) -> None:
        """list_commands returns empty list when no commands registered."""
        from hive import App

        app = App(name="test-app")
        assert app.registry.list_commands() == []

    def test_get_query_returns_registration(self) -> None:
        """get_query returns QueryRegistration for registered query."""
        from hive import App, query

        app = App(name="test-app")

        @query(app)
        async def my_query(ctx) -> list:
            return []

        reg = app.registry.get_query("my_query")
        assert reg is not None
        assert reg.name == "my_query"

    def test_get_query_returns_none_for_unknown(self) -> None:
        """get_query returns None for unregistered query."""
        from hive import App

        app = App(name="test-app")
        assert app.registry.get_query("nonexistent") is None

    def test_list_queries_returns_all_queries(self) -> None:
        """list_queries returns all registered queries."""
        from hive import App, query

        app = App(name="test-app")

        @query(app)
        async def query1(ctx) -> list:
            return []

        @query(app)
        async def query2(ctx) -> list:
            return []

        queries = app.registry.list_queries()
        assert len(queries) == 2

    def test_commands_property_is_mapping(self) -> None:
        """registry.commands is a Mapping[str, CommandRegistration]."""
        from collections.abc import Mapping

        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def cmd(ctx) -> None:
            pass

        assert isinstance(app.registry.commands, Mapping)
        assert "cmd" in app.registry.commands

    def test_queries_property_is_mapping(self) -> None:
        """registry.queries is a Mapping[str, QueryRegistration]."""
        from collections.abc import Mapping

        from hive import App, query

        app = App(name="test-app")

        @query(app)
        async def qry(ctx) -> list:
            return []

        assert isinstance(app.registry.queries, Mapping)
        assert "qry" in app.registry.queries


class TestDuplicateNameRejection:
    """Tests for duplicate name detection (T013)."""

    def test_duplicate_command_name_raises_error(self) -> None:
        """Registering two commands with same name raises RegistrationError."""
        from hive import App, RegistrationError, command

        app = App(name="test-app")

        @command(app)
        async def duplicate(ctx) -> None:
            """First command."""
            pass

        with pytest.raises(RegistrationError):

            @command(app)
            async def duplicate(ctx) -> None:  # noqa: F811
                """Second command with same name."""
                pass

    def test_duplicate_query_name_raises_error(self) -> None:
        """Registering two queries with same name raises RegistrationError."""
        from hive import App, RegistrationError, query

        app = App(name="test-app")

        @query(app)
        async def duplicate(ctx) -> list:
            return []

        with pytest.raises(RegistrationError):

            @query(app)
            async def duplicate(ctx) -> list:  # noqa: F811
                return []

    def test_command_and_query_same_name_raises_error(self) -> None:
        """Command and query cannot share the same name."""
        from hive import App, RegistrationError, command, query

        app = App(name="test-app")

        @command(app)
        async def shared_name(ctx) -> None:
            pass

        with pytest.raises(RegistrationError):

            @query(app)
            async def shared_name(ctx) -> list:  # noqa: F811
                return []

    def test_custom_name_collision_detected(self) -> None:
        """Custom names are checked for collisions."""
        from hive import App, RegistrationError, command

        app = App(name="test-app")

        @command(app, name="create")
        async def add_item(ctx) -> None:
            pass

        with pytest.raises(RegistrationError):

            @command(app, name="create")
            async def new_item(ctx) -> None:
                pass

    def test_alias_collision_with_name_detected(self) -> None:
        """Alias cannot collide with existing command name."""
        from hive import App, RegistrationError, command

        app = App(name="test-app")

        @command(app)
        async def create(ctx) -> None:
            pass

        with pytest.raises(RegistrationError):

            @command(app, aliases=["create"])  # Collides with existing command
            async def add(ctx) -> None:
                pass


class TestScreenValidation:
    """Tests for screen validation (T072, T073)."""

    def test_duplicate_screen_name_raises_error(self) -> None:
        """Registering two screens with same name raises RegistrationError."""
        from hive import App, RegistrationError, screen

        app = App(name="test-app")

        @screen(app)
        class Dashboard:
            """First dashboard."""
            pass

        with pytest.raises(RegistrationError):

            @screen(app)
            class Dashboard:  # noqa: F811
                """Second dashboard with same name."""
                pass

    def test_multiple_default_screens_raises_error(self) -> None:
        """Only one screen can be marked as default (T072)."""
        from hive import App, RegistrationError, screen

        app = App(name="test-app")

        @screen(app, default=True)
        class HomeScreen:
            """Home screen (default)."""
            pass

        with pytest.raises(RegistrationError) as exc_info:

            @screen(app, default=True)
            class DashboardScreen:
                """Dashboard (also trying to be default)."""
                pass

        assert "default" in str(exc_info.value).lower()

    def test_non_default_screens_allowed(self) -> None:
        """Multiple non-default screens are allowed."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, default=True)
        class Home:
            pass

        @screen(app)  # Not default
        class Settings:
            pass

        @screen(app)  # Not default
        class Profile:
            pass

        screens = app.registry.list_screens()
        assert len(screens) == 3

    def test_duplicate_keybinding_raises_error(self) -> None:
        """Two screens cannot use the same keybinding (T073)."""
        from hive import App, RegistrationError, screen

        app = App(name="test-app")

        @screen(app, keybinding="d")
        class Dashboard:
            """Dashboard with 'd' keybinding."""
            pass

        with pytest.raises(RegistrationError) as exc_info:

            @screen(app, keybinding="d")
            class DataView:
                """Data view also trying 'd' keybinding."""
                pass

        assert "keybinding" in str(exc_info.value).lower()

    def test_different_keybindings_allowed(self) -> None:
        """Different keybindings are allowed."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app, keybinding="d")
        class Dashboard:
            pass

        @screen(app, keybinding="s")
        class Settings:
            pass

        @screen(app, keybinding="p")
        class Profile:
            pass

        screens = app.registry.list_screens()
        assert len(screens) == 3

    def test_screens_without_keybindings_allowed(self) -> None:
        """Multiple screens without keybindings are allowed."""
        from hive import App, screen

        app = App(name="test-app")

        @screen(app)
        class Screen1:
            pass

        @screen(app)
        class Screen2:
            pass

        screens = app.registry.list_screens()
        assert len(screens) == 2

    def test_screens_property_is_mapping(self) -> None:
        """registry.screens is a Mapping[str, ScreenRegistration]."""
        from collections.abc import Mapping

        from hive import App, screen

        app = App(name="test-app")

        @screen(app)
        class TestScreen:
            pass

        assert isinstance(app.registry.screens, Mapping)
        assert "TestScreen" in app.registry.screens
