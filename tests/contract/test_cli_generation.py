"""Contract tests for CLI generation (T057-T060)."""

import json

from typer.testing import CliRunner

runner = CliRunner()


class TestCLIGeneration:
    """Tests for CLI generation from registry (T057)."""

    def test_cli_generates_commands(self) -> None:
        """CLI generator creates Typer commands from registered commands."""
        from hive import App, command

        app = App(name="test-cli")

        @command(app)
        async def hello(ctx, name: str = "World") -> dict:
            """Say hello."""
            return {"message": f"Hello, {name}!"}

        cli = app.cli()
        result = runner.invoke(cli, ["hello", "--help"])

        assert result.exit_code == 0
        assert "Say hello" in result.stdout
        assert "name" in result.stdout.lower()

    def test_cli_generates_queries(self) -> None:
        """CLI generator creates Typer commands from registered queries."""
        from hive import App, query

        app = App(name="test-cli")

        @query(app)
        async def list_items(ctx) -> list:
            """List all items."""
            return []

        cli = app.cli()
        result = runner.invoke(cli, ["list-items", "--help"])

        assert result.exit_code == 0
        assert "List all items" in result.stdout

    def test_cli_handles_parameters(self) -> None:
        """CLI correctly maps function parameters to CLI arguments/options."""
        from hive import App, command

        app = App(name="test-cli")

        @command(app)
        async def create(
            ctx,
            name: str,
            count: int = 1,
            verbose: bool = False,
        ) -> dict:
            """Create something."""
            return {"name": name, "count": count, "verbose": verbose}

        cli = app.cli()
        result = runner.invoke(cli, ["create", "--help"])

        assert result.exit_code == 0
        assert "name" in result.stdout.lower()
        assert "count" in result.stdout.lower()
        assert "verbose" in result.stdout.lower()


class TestJSONFlag:
    """Tests for --json flag output (T058)."""

    def test_json_flag_produces_json_output(self) -> None:
        """--json flag produces valid JSON output."""
        from hive import App, command, query

        app = App(name="test-cli")

        @query(app)
        async def get_status(ctx) -> dict:
            """Get system status."""
            return {"status": "ok", "version": "1.0.0"}

        @command(app)
        async def noop(ctx) -> None:
            """Placeholder command."""

        cli = app.cli()
        result = runner.invoke(cli, ["get-status", "--json"])

        assert result.exit_code == 0
        # Output should be valid JSON
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"

    def test_json_flag_suppresses_info_messages(self) -> None:
        """--json flag suppresses informational messages."""
        from hive import App, command, query

        app = App(name="test-cli")

        @command(app)
        async def create(ctx, name: str) -> dict:
            """Create something."""
            ctx.output.info("Creating item...")  # Should be suppressed
            return {"name": name}

        @query(app)
        async def noop(ctx) -> list:
            """Placeholder query."""
            return []

        cli = app.cli()
        result = runner.invoke(cli, ["create", "test", "--json"])

        assert result.exit_code == 0
        # Should be pure JSON without info messages
        data = json.loads(result.stdout)
        assert data["name"] == "test"


class TestHelpOutput:
    """Tests for --help output (T059)."""

    def test_help_shows_all_commands(self) -> None:
        """--help shows all registered commands."""
        from hive import App, command, query

        app = App(name="test-cli")

        @command(app)
        async def create(ctx) -> None:
            """Create a resource."""

        @command(app)
        async def delete(ctx) -> None:
            """Delete a resource."""

        @query(app)
        async def list_resources(ctx) -> list:
            """List all resources."""
            return []

        cli = app.cli()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "delete" in result.stdout
        assert "list-resources" in result.stdout

    def test_help_shows_description_from_docstring(self) -> None:
        """--help shows command description from docstring."""
        from hive import App, command

        app = App(name="test-cli")

        @command(app)
        async def my_command(ctx) -> None:
            """This is the command description."""

        cli = app.cli()
        result = runner.invoke(cli, ["my-command", "--help"])

        assert result.exit_code == 0
        assert "This is the command description" in result.stdout

    def test_help_shows_parameter_descriptions(self) -> None:
        """--help shows parameter help text when available."""
        from hive import App, command

        app = App(name="test-cli")

        @command(app)
        async def with_params(ctx, name: str, count: int = 10) -> None:
            """Command with parameters."""

        cli = app.cli()
        result = runner.invoke(cli, ["with-params", "--help"])

        assert result.exit_code == 0
        # Parameters should be documented
        assert "name" in result.stdout.lower()
        assert "count" in result.stdout.lower()
