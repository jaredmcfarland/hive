"""Hive serve CLI command.

This module provides the `hive serve` command for starting a REST API
server that exposes Hive commands and queries as HTTP endpoints.

Usage:
    hive serve
    hive serve --port 8000 --reload
    hive serve --auth api_key
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, cast

from rich.console import Console
import typer

if TYPE_CHECKING:
    from hive.generators.rest import AuthType

serve_app = typer.Typer(
    name="serve",
    help="Start REST API server for Hive application",
    no_args_is_help=False,
)

console = Console()


def _get_app() -> Any:
    """Get the Hive App instance.

    Discovers the app by searching common module locations.
    """
    from hive.cli.utils import AppDiscoveryError, discover_app  # noqa: PLC0415

    try:
        return discover_app()
    except AppDiscoveryError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e


@serve_app.callback(invoke_without_command=True)
def serve(  # noqa: C901, PLR0913, PLR0912
    _ctx: typer.Context,
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Host to bind to"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to listen on"),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option("--reload", "-r", help="Enable hot reload on code changes"),
    ] = False,
    workers: Annotated[
        int,
        typer.Option("--workers", "-w", help="Number of worker processes"),
    ] = 1,
    auth: Annotated[
        str,
        typer.Option("--auth", "-a", help="Authentication type: none, api_key, bearer, basic"),
    ] = "none",
    api_key_header: Annotated[
        str,
        typer.Option("--api-key-header", help="Header name for API key auth"),
    ] = "X-API-Key",
    api_key_env: Annotated[
        str,
        typer.Option("--api-key-env", help="Environment variable for API key"),
    ] = "HIVE_API_KEY",
    debug: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Enable debug mode"),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output status as JSON"),
    ] = False,
) -> None:
    """Start REST API server.

    Starts a FastAPI server that exposes Hive commands as POST endpoints
    and queries as GET endpoints. Includes OpenAPI documentation at /docs.

    Examples:
        # Start development server
        hive serve --reload

        # Start production server
        hive serve --host 0.0.0.0 --port 8000 --workers 4

        # With API key authentication
        HIVE_API_KEY=secret123 hive serve --auth api_key
    """
    # Check if REST is available
    try:
        from hive.generators.rest import REST_AVAILABLE, RESTGenerator  # noqa: PLC0415

        if not REST_AVAILABLE:
            if json_output:
                console.print_json(
                    data={
                        "error": "FastAPI not installed",
                        "hint": "pip install hive-framework[rest]",
                    }
                )
            else:
                console.print(
                    "[red]Error:[/red] FastAPI is not installed. "
                    "Install with: pip install hive-framework[rest]"
                )
            raise typer.Exit(code=1)
    except ImportError as e:
        if json_output:
            console.print_json(data={"error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

    # Validate auth type
    valid_auth_types = ["none", "api_key", "bearer", "basic"]
    if auth not in valid_auth_types:
        if json_output:
            console.print_json(
                data={"error": f"Invalid auth type: {auth}", "valid": valid_auth_types}
            )
        else:
            console.print(
                f"[red]Error:[/red] Invalid auth type '{auth}'. Valid: {valid_auth_types}"
            )
        raise typer.Exit(code=1)

    # Get the app
    try:
        app = _get_app()
    except Exception as e:
        if json_output:
            console.print_json(data={"error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

    # Output server info
    generator = RESTGenerator()
    config = generator.generate(app)

    if json_output:
        status = {
            "status": "starting",
            "host": host,
            "port": port,
            "docs_url": f"http://{host}:{port}/docs",
            "endpoints": {
                "commands": len([e for e in config.endpoints if e.method == "POST"]),
                "queries": len([e for e in config.endpoints if e.method == "GET"]),
            },
            "reload_enabled": reload,
            "auth": auth,
        }
        console.print_json(data=status)
    else:
        console.print("\n[bold green]Starting REST API server[/bold green]")
        console.print(f"  Host: {host}")
        console.print(f"  Port: {port}")
        console.print(f"  Docs: http://{host}:{port}/docs")
        console.print(f"  Commands: {len([e for e in config.endpoints if e.method == 'POST'])}")
        console.print(f"  Queries: {len([e for e in config.endpoints if e.method == 'GET'])}")
        if reload:
            console.print("  [yellow]Hot reload enabled[/yellow]")
        if auth != "none":
            console.print(f"  [blue]Auth: {auth}[/blue]")
        console.print()

    # Start the server
    generator.serve(
        app,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        auth_type=cast("AuthType", auth),
        api_key_header=api_key_header,
        api_key_env=api_key_env,
        debug=debug,
    )
