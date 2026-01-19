"""Hive MCP CLI commands.

Provides commands for starting and managing MCP (Model Context Protocol) servers.

Usage:
    hive mcp serve --transport stdio
    hive mcp serve --transport sse --host 127.0.0.1 --port 8080
"""

from __future__ import annotations

from typing import Annotated

from rich.console import Console
import typer

# Create the mcp subcommand group
mcp_app = typer.Typer(
    name="mcp",
    help="MCP (Model Context Protocol) server commands",
    no_args_is_help=True,
)

console = Console()


@mcp_app.command("serve")
def serve_command(
    transport: Annotated[
        str,
        typer.Option(
            "--transport",
            "-t",
            help="Transport protocol (stdio or sse)",
        ),
    ] = "stdio",
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host to bind (SSE transport only)",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="Port to listen on (SSE transport only)",
        ),
    ] = 8080,
    include_queries: Annotated[  # noqa: ARG001  # Reserved for future use
        bool,
        typer.Option(
            "--include-queries",
            help="Include queries as read-only tools",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON on error",
        ),
    ] = False,
) -> None:
    """Start the MCP server to expose commands as tools.

    Examples:
        hive mcp serve                    # stdio transport (default)
        hive mcp serve --transport sse    # SSE transport on 127.0.0.1:8080
        hive mcp serve -t sse -p 3000     # SSE on custom port
    """
    try:
        from hive.generators.mcp import MCP_AVAILABLE, MCPGenerator  # noqa: PLC0415

        if not MCP_AVAILABLE:
            msg = "FastMCP is not installed. Install with: pip install hive-framework[mcp]"
            if json_output:
                console.print_json(data={"status": "error", "error": msg})
            else:
                console.print(f"[red]Error:[/red] {msg}")
            raise typer.Exit(1)  # noqa: TRY301

        # Get the current app
        app = _get_current_app()

        if not json_output:
            console.print("[green]Starting MCP server...[/green]")
            console.print(f"  Transport: {transport}")
            if transport == "sse":
                console.print(f"  Host: {host}")
                console.print(f"  Port: {port}")

        # Generate and serve
        generator = MCPGenerator()
        generator.serve(app, transport=transport, host=host, port=port)

    except typer.Exit:
        raise
    except Exception as e:
        if json_output:
            console.print_json(data={"status": "error", "error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _get_current_app() -> App:  # type: ignore[name-defined]  # noqa: F821
    """Get the current project's App instance.

    For now, creates an empty app. In practice, this would:
    1. Look for a hive.toml or pyproject.toml with [tool.hive]
    2. Import the configured app module
    3. Return the App instance
    """
    from hive import App  # noqa: PLC0415

    # Create a default app - in practice this would load from config
    return App("hive")
