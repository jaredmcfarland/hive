"""Hive CLI entrypoint.

This module provides the main CLI application for the Hive framework,
exposing subcommands for specification export, MCP server, REST API,
and project management.

Usage:
    hive --help
    hive spec export --format json
    hive spec diff v1.json v2.json
    hive mcp serve
    hive serve
    hive new myproject
    hive dev
"""

from __future__ import annotations

from typing import Annotated

from rich.console import Console
import typer

# Create the main CLI app
app = typer.Typer(
    name="hive",
    help="Hive framework CLI - Build terminal-agent-native applications",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Console for rich output
console = Console()


# Version callback
def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from hive import __version__  # noqa: PLC0415

        console.print(f"Hive Framework v{__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[  # Used by eager callback
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Hive framework CLI.

    Build terminal-agent-native applications with CLI, TUI, MCP, and REST interfaces.
    """
    # version parameter is handled by eager callback - no action needed here
    _ = version  # Explicitly mark as intentionally unused


# Import and register subcommand groups (after app creation to avoid circular imports)
from hive.cli.mcp import mcp_app  # noqa: E402
from hive.cli.project import project_app  # noqa: E402
from hive.cli.serve import serve_app  # noqa: E402
from hive.cli.spec import spec_app  # noqa: E402

app.add_typer(spec_app, name="spec")
app.add_typer(mcp_app, name="mcp")
app.add_typer(serve_app, name="serve")

# Register project commands at root level (hive new, hive dev, etc.)
app.add_typer(project_app, name="project")

# Also expose key project commands at root level for convenience
# Users can use either "hive new" or "hive project new"
from hive.cli.project import (  # noqa: E402
    build_command,
    dev_command,
    new_command,
    publish_command,
)

app.command("new")(new_command)
app.command("dev")(dev_command)
app.command("build")(build_command)
app.command("publish")(publish_command)


def cli() -> None:
    """CLI entry point for the Hive framework."""
    app()


if __name__ == "__main__":
    cli()
