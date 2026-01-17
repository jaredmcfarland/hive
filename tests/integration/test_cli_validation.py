"""Test CLI validation error formatting with refinement types."""

import pytest
from typer.testing import CliRunner


class TestCLIValidation:
    """Tests for CLI validation with refinement types.

    Note: With single-command Typer apps, the command name becomes the app name
    and arguments are passed directly without a subcommand.
    """

    def test_positive_int_shows_helpful_error(self) -> None:
        """CLI shows helpful error for invalid PositiveInt."""
        from hive import App, command
        from hive.types import PositiveInt
        from hive.generators.cli import CLIGenerator

        app = App(name="test-app")

        @command(app)
        async def set_priority(ctx, priority: PositiveInt) -> dict:
            """Set task priority."""
            return {"priority": priority}

        cli = CLIGenerator(app).generate()
        runner = CliRunner()

        # Single-command CLI: pass argument directly (no subcommand)
        result = runner.invoke(cli, ["0"])

        assert result.exit_code != 0
        # Should have a user-friendly message
        assert "priority" in result.output.lower() or "value" in result.output.lower()

    def test_port_shows_range_error(self) -> None:
        """CLI shows range error for invalid Port."""
        from hive import App, command
        from hive.types import Port
        from hive.generators.cli import CLIGenerator

        app = App(name="test-app")

        @command(app)
        async def start_server(ctx, port: Port) -> dict:
            """Start server."""
            return {"port": port}

        cli = CLIGenerator(app).generate()
        runner = CliRunner()

        # Single-command CLI: pass argument directly (no subcommand)
        result = runner.invoke(cli, ["70000"])

        assert result.exit_code != 0
        # Should mention valid range or port
        assert "port" in result.output.lower() or "value" in result.output.lower()

    def test_valid_value_passes(self) -> None:
        """CLI accepts valid refinement type values."""
        from hive import App, command
        from hive.types import PositiveInt
        from hive.generators.cli import CLIGenerator

        app = App(name="test-app")

        @command(app)
        async def set_priority(ctx, priority: PositiveInt) -> dict:
            """Set task priority."""
            return {"priority": priority}

        cli = CLIGenerator(app).generate()
        runner = CliRunner()

        # Single-command CLI: pass argument directly (no subcommand)
        result = runner.invoke(cli, ["5"])

        assert result.exit_code == 0
