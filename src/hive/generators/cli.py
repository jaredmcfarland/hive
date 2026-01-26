"""CLI generator using Typer.

Generates a Typer application from the registered commands and queries.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import inspect
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
import typer

from hive.core.registry import ApplicationRegistry
from hive.core.types import CommandRegistration, ParameterInfo, QueryRegistration
from hive.errors import CommandError
from hive.runtime.config import AppSettings
from hive.runtime.context import ExecutionContext
from hive.runtime.output import OutputFormat


class CLIGenerator:
    """Generates a Typer CLI from an application registry.

    The generator reads command and query registrations and creates
    corresponding Typer commands with proper argument handling,
    help text, and output formatting.
    """

    def __init__(self, app: Any) -> None:
        """Initialize the CLI generator.

        Args:
            app: The Hive application instance.
        """
        self._app = app
        self._registry: ApplicationRegistry = app.registry

    def generate(self) -> typer.Typer:
        """Generate a Typer application from the registry.

        Returns:
            A configured Typer app with all registered commands.
        """
        cli = typer.Typer(
            name=self._app.name,
            help=self._app.description or f"{self._app.name} CLI",
            add_completion=False,
        )

        # Add commands
        for cmd in self._registry.list_commands():
            self._add_command(cli, cmd)

        # Add queries (as commands)
        for qry in self._registry.list_queries():
            self._add_query(cli, qry)

        # Add TUI command if screens are registered
        if self._registry.list_screens():
            self._add_tui_command(cli)

        return cli

    def _add_tui_command(self, cli: typer.Typer) -> None:
        """Add the TUI launch command if screens are registered."""
        app = self._app  # Capture for closure
        generator = self  # Capture for closure

        def tui_command() -> None:
            """Launch the terminal user interface."""
            asyncio.run(generator._run_tui_async(app))

        cli.command(name="tui", help="Launch the terminal user interface")(tui_command)

    async def _run_tui_async(self, app: Any) -> None:
        """Run the TUI with an execution context for database access.

        Args:
            app: The Hive application.
        """
        from hive.generators.tui import generate_tui_app

        settings = AppSettings()

        # Ensure tables exist
        await self._ensure_tables(settings.database_url)

        # Run TUI within execution context for config/registry access
        # session_on_enter=False: Don't create a session - individual operations
        # will create their own ExecutionContexts for database access
        async with ExecutionContext(
            registry=self._registry,
            settings=settings,
            output_format=OutputFormat.TABLE,
            command_name="tui",
            session_on_enter=False,
        ) as ctx:
            tui_app = generate_tui_app(app, execution_context=ctx)
            await tui_app.run_async()

    def _add_command(self, cli: typer.Typer, cmd: CommandRegistration) -> None:
        """Add a command to the Typer app."""
        wrapper = self._create_command_wrapper(cmd.func, cmd.name, cmd.parameters)
        cli.command(
            name=self._to_cli_name(cmd.name),
            help=cmd.docstring,
            hidden=cmd.hidden,
        )(wrapper)

    def _add_query(self, cli: typer.Typer, qry: QueryRegistration) -> None:
        """Add a query to the Typer app as a command."""
        wrapper = self._create_command_wrapper(qry.func, qry.name, qry.parameters)
        cli.command(
            name=self._to_cli_name(qry.name),
            help=qry.docstring,
        )(wrapper)

    def _create_command_wrapper(
        self,
        func: Callable[..., Any],
        name: str,
        parameters: list[ParameterInfo],
    ) -> Callable[..., Any]:
        """Create a Typer-compatible wrapper for a command function.

        This dynamically creates a function with the correct signature
        for Typer to inspect and generate CLI arguments from.
        """
        generator = self  # Capture for closure

        # Build the Typer parameter specifications
        typer_params: list[inspect.Parameter] = []

        for param in parameters:
            cli_name = self._to_cli_name(param.name)
            python_name = param.name

            # Get the base type, handling Optional
            param_type = self._get_base_type(param.type)

            if param.has_default:
                if param_type is bool:
                    default = typer.Option(
                        param.default,
                        f"--{cli_name}/--no-{cli_name}",
                        help=param.help,
                    )
                else:
                    default = typer.Option(
                        param.default,
                        f"--{cli_name}",
                        help=param.help,
                    )
            else:
                # Required positional argument
                default = typer.Argument(help=param.help)

            typer_params.append(
                inspect.Parameter(
                    python_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                    annotation=param_type,
                )
            )

        # Add the --json option
        typer_params.append(
            inspect.Parameter(
                "json_output",
                inspect.Parameter.KEYWORD_ONLY,
                default=typer.Option(False, "--json", help="Output as JSON"),
                annotation=bool,
            )
        )

        # Create the wrapper function
        def wrapper(*args: Any, **kwargs: Any) -> None:
            # Extract json_output from kwargs
            json_output = kwargs.pop("json_output", False)
            output_format = OutputFormat.JSON if json_output else OutputFormat.TABLE

            # Create settings from environment
            settings = AppSettings()

            # Run the async command
            try:
                asyncio.run(generator._execute_command(func, settings, output_format, name, kwargs))
            except CommandError as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(e.exit_code) from None

        # Set the wrapper's signature for Typer to inspect
        wrapper.__signature__ = inspect.Signature(typer_params)  # type: ignore[attr-defined]
        wrapper.__name__ = name
        wrapper.__doc__ = func.__doc__

        # Set annotations
        annotations = {}
        for param in typer_params:
            if param.annotation is not inspect.Parameter.empty:
                annotations[param.name] = param.annotation
        annotations["return"] = None
        wrapper.__annotations__ = annotations

        return wrapper

    def _get_base_type(self, type_hint: Any) -> type:
        """Extract the base type from a type hint, handling Optional and Annotated."""
        import types

        if type_hint is None or type_hint is type(None):
            return str

        origin = get_origin(type_hint)

        # Handle Annotated types (e.g., Annotated[int, Is[...]])
        # This is crucial for refinement types like PositiveInt, Port, etc.
        if origin is Annotated:
            args = get_args(type_hint)
            if args:
                # First arg is the actual type, rest are metadata
                return self._get_base_type(args[0])
            return str

        # Handle Union types (including Optional which is Union[X, None])
        # Python 3.10+ uses types.UnionType for X | Y syntax
        if origin is Union or isinstance(type_hint, types.UnionType):
            args = get_args(type_hint)
            # Filter out NoneType and return the first real type
            for arg in args:
                if arg is not type(None):
                    # Recursively get base type in case of nested generics
                    return self._get_base_type(arg)
            return str

        # Handle Literal types - convert to str for Typer compatibility
        # Typer doesn't support Literal directly; values become string choices
        if origin is Literal:
            return str

        # Handle other generic types (list, dict, etc.)
        if origin is not None:
            return origin

        # Regular type
        if isinstance(type_hint, type):
            return type_hint

        return str

    async def _ensure_tables(self, database_url: str) -> None:
        """Ensure database tables exist.

        Creates all SQLModel tables if they don't exist. For file-based SQLite
        databases, also creates the parent directory if needed.

        Args:
            database_url: Database connection URL.
        """
        from pathlib import Path

        from sqlalchemy.pool import NullPool

        # Ensure we're using the async driver for SQLite
        if database_url.startswith("sqlite") and "aiosqlite" not in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # For file-based SQLite, ensure parent directory exists
        if database_url.startswith("sqlite"):
            # Extract path from sqlite+aiosqlite:///path or sqlite:///path
            # Format: sqlite[+aiosqlite]:///[path] where path can be relative or absolute
            path_part = database_url.split("///", 1)[-1]
            # Skip in-memory databases (empty path or :memory:)
            if path_part and path_part != ":memory:":
                db_path = Path(path_part).expanduser()
                db_path.parent.mkdir(parents=True, exist_ok=True)

        # Use NullPool to avoid connection conflicts with the main session's StaticPool
        if database_url.startswith("sqlite"):
            engine = create_async_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
            )
        else:
            engine = create_async_engine(database_url, poolclass=NullPool)

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()

    async def _execute_command(
        self,
        func: Callable[..., Any],
        settings: AppSettings,
        output_format: OutputFormat,
        command_name: str,
        kwargs: dict[str, Any],
    ) -> Any:
        """Execute an async command with context and beartype validation."""
        # Ensure tables exist before executing
        await self._ensure_tables(settings.database_url)

        async with ExecutionContext(
            settings=settings,
            output_format=output_format,
            command_name=command_name,
        ) as ctx:
            try:
                # Apply beartype validation for refinement types
                validated_func = beartype(func)
                result = await validated_func(ctx, **kwargs)
            except BeartypeCallHintParamViolation as e:
                # Format validation error for CLI
                error_msg = self._format_validation_error(e, kwargs)
                raise CommandError(error_msg, exit_code=1) from None

            # Output the result
            if result is not None:
                ctx.output.result(result)

            return result

    def _format_validation_error(
        self, error: BeartypeCallHintParamViolation, kwargs: dict[str, Any]
    ) -> str:
        """Format beartype validation error for CLI output."""
        msg = str(error)

        # Try to extract parameter name from error message
        # BeartypeCallHintParamViolation typically includes the parameter name
        # Make it more user-friendly
        import re

        # Look for parameter name in error message
        param_match = re.search(r"parameter (['\"]?)(\w+)\1", msg, re.IGNORECASE)
        if param_match:
            param_name = param_match.group(2)
            value = kwargs.get(param_name, "unknown")
            return f"Invalid value for '{param_name}': {value!r} does not satisfy type constraints"

        # Fallback to a simpler message
        return f"Validation error: {msg}"

    def _to_cli_name(self, name: str) -> str:
        """Convert a Python identifier to a CLI-friendly name."""
        return name.replace("_", "-")
