"""Quickstart validation tests (T086).

These tests validate that the framework works as demonstrated in quickstart.md.
"""

import json

from typer.testing import CliRunner

runner = CliRunner()


class TestQuickstartValidation:
    """Validate the quickstart example works correctly."""

    def test_version_available(self) -> None:
        """Verify hive.__version__ is accessible."""
        import hive

        assert hive.__version__ == "0.1.0"

    def test_decorators_register_correctly(self) -> None:
        """Verify decorators register commands, queries, entities."""
        from sqlmodel import Field, SQLModel

        from hive import App, command, entity, query

        app = App(
            name="todo",
            version="0.1.0",
            description="A simple todo application",
        )

        @entity(app)
        class Task(SQLModel, table=True):
            __tablename__ = "quickstart_task"
            id: int | None = Field(default=None, primary_key=True)
            title: str
            completed: bool = False

        @command(app, entities=[Task])
        async def add(ctx, title: str) -> dict:
            """Add a new task to the list."""
            return {"title": title}

        @command(app, entities=[Task])
        async def complete(ctx, task_id: int) -> dict:
            """Mark a task as completed."""
            return {"task_id": task_id}

        @query(app, entities=[Task])
        async def list_tasks(ctx, show_all: bool = False) -> list:
            """List all tasks."""
            return []

        # Verify registrations
        assert list(app.registry.commands.keys()) == ["add", "complete"]
        assert list(app.registry.queries.keys()) == ["list_tasks"]
        assert list(app.registry.entities.keys()) == ["Task"]

    def test_cli_generation(self) -> None:
        """Verify CLI is generated from decorators."""
        from hive import App, command, query

        app = App(name="todo", description="Todo CLI")

        @command(app)
        async def add(ctx, title: str) -> dict:
            """Add a new task."""
            return {"title": title}

        @query(app)
        async def list_tasks(ctx) -> list:
            """List tasks."""
            return []

        cli = app.cli()

        # Test help output
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "list-tasks" in result.stdout

    def test_json_output_flag(self) -> None:
        """Verify --json flag produces JSON output."""
        from hive import App, command, query

        app = App(name="test")

        @query(app)
        async def get_status(ctx) -> dict:
            """Get status."""
            return {"status": "ok", "version": "1.0.0"}

        # Add a placeholder command to avoid single-command behavior
        @command(app)
        async def noop(ctx) -> None:
            pass

        cli = app.cli()
        result = runner.invoke(cli, ["get-status", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"

    def test_argument_and_option_types(self) -> None:
        """Verify Argument and Option types are available."""
        from hive import Argument, Option

        # These should be importable and usable
        arg = Argument(help="Test argument")
        opt = Option("--test", "-t", help="Test option")

        assert arg.help == "Test argument"
        assert opt.names == ("--test", "-t")
        assert opt.help == "Test option"

    def test_error_types(self) -> None:
        """Verify error types are available."""
        from hive import (
            CommandError,
            ConfigurationError,
            HiveError,
            RegistrationError,
            ValidationError,
        )

        # All error types should be importable
        assert issubclass(CommandError, HiveError)
        assert issubclass(ConfigurationError, HiveError)
        assert issubclass(RegistrationError, HiveError)
        assert issubclass(ValidationError, HiveError)

        # CommandError should have exit_code
        err = CommandError("test")
        assert err.exit_code == 1

    def test_screen_decorator_available(self) -> None:
        """Verify screen decorator is available for TUI."""
        from hive import App, screen

        app = App(name="test")

        @screen(app, default=True, keybinding="d")
        class Dashboard:
            """Main dashboard."""

        # Verify screen is registered
        reg = app.registry.get_screen("Dashboard")
        assert reg is not None
        assert reg.default is True
        assert reg.keybinding == "d"

    def test_validate_method(self) -> None:
        """Verify app.validate() checks registrations."""
        from sqlmodel import Field, SQLModel

        from hive import App, command

        app = App(name="test")

        # Unregistered entity reference
        class UnregisteredTask(SQLModel, table=True):
            __tablename__ = "unregistered_task"
            id: int | None = Field(default=None, primary_key=True)

        @command(app, entities=[UnregisteredTask])
        async def bad_command(ctx) -> None:
            pass

        errors = app.validate()
        assert len(errors) == 1
        assert "UnregisteredTask" in str(errors[0])
