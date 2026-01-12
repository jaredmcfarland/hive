"""CLI generator using Typer.

Generates a Typer application from the registered commands and queries.
"""

import asyncio
import inspect
from collections.abc import Callable
from typing import Any, Union, get_args, get_origin

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

        return cli

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
                asyncio.run(
                    generator._execute_command(
                        func, settings, output_format, name, kwargs
                    )
                )
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
        """Extract the base type from a type hint, handling Optional."""
        import types

        if type_hint is None or type_hint is type(None):
            return str

        origin = get_origin(type_hint)

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

        # Handle other generic types (list, dict, etc.)
        if origin is not None:
            return origin

        # Regular type
        if isinstance(type_hint, type):
            return type_hint

        return str

    async def _execute_command(
        self,
        func: Callable[..., Any],
        settings: AppSettings,
        output_format: OutputFormat,
        command_name: str,
        kwargs: dict[str, Any],
    ) -> Any:
        """Execute an async command with context."""
        async with ExecutionContext(
            settings=settings,
            output_format=output_format,
            command_name=command_name,
        ) as ctx:
            result = await func(ctx, **kwargs)

            # Output the result
            if result is not None:
                ctx.output.result(result)

            return result

    def _to_cli_name(self, name: str) -> str:
        """Convert a Python identifier to a CLI-friendly name."""
        return name.replace("_", "-")
