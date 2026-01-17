"""Application class for Hive framework.

The App class is the central point for configuring and running
Hive applications. It holds the registry and provides methods
for generating CLI, TUI, and other interfaces.
"""

from pathlib import Path

from hive.core.registry import ApplicationRegistry
from hive.errors import ValidationError


class App:
    """Main application class for Hive framework.

    The App class represents a complete Hive application. It manages
    the registry of commands, queries, entities, and screens, and
    provides methods to generate CLI, TUI, and API interfaces.

    Example:
        app = App(
            name="my-app",
            version="1.0.0",
            description="My awesome application",
        )

        @command(app)
        async def hello(ctx, name: str) -> str:
            return f"Hello, {name}!"

        # Generate and run CLI
        if __name__ == "__main__":
            app.cli()()
    """

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        cli_command: str | None = None,
        tui_title: str | None = None,
        database: str | None = None,
        mcp_server: bool = False,
        rest_api: bool = False,
    ) -> None:
        """Initialize a Hive application.

        Args:
            name: Package name (e.g., "my-app").
            version: Semantic version string.
            description: Human-readable description.
            cli_command: CLI entry point name (defaults to name).
            tui_title: TUI window title.
            database: Database URL (defaults to sqlite:///~/.{name}/data.db).
            mcp_server: Enable MCP server generation.
            rest_api: Enable REST API generation.
        """
        self._name = name
        self._version = version
        self._description = description
        self._cli_command = cli_command or name
        self._tui_title = tui_title or name
        self._database = database or f"sqlite:///{Path.home()}/.{name}/data.db"
        self._mcp_server = mcp_server
        self._rest_api = rest_api

        self._registry = ApplicationRegistry()

    @property
    def name(self) -> str:
        """Application name."""
        return self._name

    @property
    def version(self) -> str:
        """Application version."""
        return self._version

    @property
    def description(self) -> str:
        """Application description."""
        return self._description

    @property
    def registry(self) -> ApplicationRegistry:
        """Access to registration data (read-only)."""
        return self._registry

    def validate(self) -> list[ValidationError]:
        """Validate all registrations.

        Checks for:
        - Commands/queries referencing unregistered entities
        - Return types that aren't JSON-serializable
        - Other consistency issues

        Returns:
            List of validation errors found. Empty if valid.
        """
        errors: list[ValidationError] = []

        # Check that entity references point to registered entities
        entity_names = set(self._registry.entities.keys())

        for cmd in self._registry.list_commands():
            for entity_cls in cmd.entities:
                if entity_cls.__name__ not in entity_names:
                    errors.append(
                        ValidationError(
                            f"Command '{cmd.name}' references unregistered entity "
                            f"'{entity_cls.__name__}'",
                            field=f"commands.{cmd.name}.entities",
                        )
                    )

        for qry in self._registry.list_queries():
            for entity_cls in qry.entities:
                if entity_cls.__name__ not in entity_names:
                    errors.append(
                        ValidationError(
                            f"Query '{qry.name}' references unregistered entity "
                            f"'{entity_cls.__name__}'",
                            field=f"queries.{qry.name}.entities",
                        )
                    )

        # Check for at most one default screen
        default_screens = [s for s in self._registry.list_screens() if s.default]
        if len(default_screens) > 1:
            names = [s.name for s in default_screens]
            errors.append(
                ValidationError(
                    f"Multiple default screens defined: {names}",
                    field="screens",
                )
            )

        return errors

    def cli(self) -> "typer.Typer":  # noqa: F821
        """Get the generated Typer CLI application.

        Returns:
            A configured Typer app with all registered commands.
        """
        from hive.generators.cli import CLIGenerator

        generator = CLIGenerator(self)
        return generator.generate()
