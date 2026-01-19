"""Hive project management CLI commands.

This module provides commands for project scaffolding and lifecycle
management including hive new, hive dev, hive build, and hive publish.

Usage:
    hive new myproject
    hive new myproject --features tui,mcp
    hive dev
    hive build
    hive publish
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess  # nosec B404
from typing import Annotated, Any

from rich.console import Console
import typer

project_app = typer.Typer(
    name="project",
    help="Project scaffolding and management commands",
    no_args_is_help=True,
)

console = Console()


# =============================================================================
# Template Content
# =============================================================================


def _get_pyproject_template() -> str:
    """Get pyproject.toml template content."""
    return """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{name}}"
version = "0.1.0"
description = "{{description}}"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    { name = "{{author}}" }
]
dependencies = [
    "hive-framework>=0.1.0",
]

[project.optional-dependencies]
{{optional_deps}}
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.8.0",
]

[project.scripts]
{{name}} = "{{name}}.app:cli"

[tool.hatch.build.targets.wheel]
packages = ["src/{{name}}"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
"""


def _get_app_template() -> str:
    """Get app.py template content."""
    return '''"""{{name}} - A Hive application.

{{description}}
"""

from __future__ import annotations

from hive import App, command, query

app = App("{{name}}")


@command(app)
async def hello(ctx, name: str = "World") -> str:
    """Say hello to someone.

    Args:
        ctx: Execution context.
        name: Name to greet.

    Returns:
        Greeting message.
    """
    return f"Hello, {name}!"


@query(app)
async def status(ctx) -> dict:
    """Get application status.

    Args:
        ctx: Execution context.

    Returns:
        Status dictionary.
    """
    return {"status": "ok", "app": "{{name}}"}


def cli() -> None:
    """CLI entry point."""
    from hive.generators.cli import generate_cli

    typer_app = generate_cli(app)
    typer_app()


if __name__ == "__main__":
    cli()
'''


def _get_init_template() -> str:
    """Get __init__.py template content."""
    return '''"""{{name}} - {{description}}"""

__version__ = "0.1.0"
'''


def _get_readme_template() -> str:
    """Get README.md template content."""
    return """# {{name}}

{{description}}

## Installation

```bash
pip install {{name}}
```

## Usage

```bash
# Run CLI
{{name}} hello --name World

# Start development server
hive dev
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run ruff format .
```
"""


def _get_test_template() -> str:
    """Get test file template content."""
    return '''"""Tests for {{name}}."""

import pytest


def test_hello():
    """Test hello command."""
    from {{name}}.app import hello
    # Test would go here
    assert True


def test_status():
    """Test status query."""
    from {{name}}.app import status
    # Test would go here
    assert True
'''


# =============================================================================
# Project Creation
# =============================================================================


def create_project(
    name: str,
    path: str | Path | None = None,
    description: str = "A Hive application",
    author: str = "",
    features: list[str] | None = None,
    force: bool = False,
) -> str:
    """Create a new Hive project.

    Args:
        name: Project name (valid Python package name).
        path: Directory to create project in (default: current).
        description: Project description.
        author: Author name.
        features: Optional features to enable (tui, mcp, rest, all).
        force: Overwrite existing directory.

    Returns:
        Absolute path to created project.

    Raises:
        FileExistsError: If directory exists and force=False.
    """
    # Determine project directory
    base_path = Path(path) if path else Path.cwd()
    project_path = base_path / name

    # Check if exists
    if project_path.exists() and not force:
        msg = f"Directory already exists: {project_path}"
        raise FileExistsError(msg)

    # Remove if force
    if project_path.exists() and force:
        shutil.rmtree(project_path)

    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    src_dir = project_path / "src" / name
    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = project_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Build optional dependencies
    optional_deps = []
    features = features or []
    if "all" in features:
        features = ["tui", "mcp", "rest"]

    if "tui" in features:
        optional_deps.append('tui = ["textual>=0.50.0"]')
    if "mcp" in features:
        optional_deps.append('mcp = ["fastmcp>=2.0,<3"]')
    if "rest" in features:
        optional_deps.append('rest = ["fastapi>=0.100.0", "uvicorn>=0.23.0"]')

    optional_deps_str = "\n".join(optional_deps) if optional_deps else ""

    # Template variables
    variables = {
        "{{name}}": name,
        "{{description}}": description,
        "{{author}}": author or "Unknown",
        "{{optional_deps}}": optional_deps_str,
    }

    def substitute(content: str) -> str:
        """Substitute template variables."""
        for key, value in variables.items():
            content = content.replace(key, value)
        return content

    # Write files
    files = [
        (project_path / "pyproject.toml", _get_pyproject_template()),
        (project_path / "README.md", _get_readme_template()),
        (src_dir / "__init__.py", _get_init_template()),
        (src_dir / "app.py", _get_app_template()),
        (tests_dir / "__init__.py", ""),
        (tests_dir / f"test_{name}.py", _get_test_template()),
    ]

    for file_path, template in files:
        content = substitute(template)
        file_path.write_text(content)

    return str(project_path.absolute())


# =============================================================================
# Build and Publish
# =============================================================================


def build_project(
    project_path: str | Path,
    formats: list[str] | None = None,
    clean: bool = False,
) -> dict[str, Any]:
    """Build project artifacts.

    Args:
        project_path: Path to project directory.
        formats: Build formats (wheel, sdist).
        clean: Clean dist/ before building.

    Returns:
        Dict with 'artifacts' list.
    """
    project_path = Path(project_path)
    formats = formats or ["wheel"]
    dist_dir = project_path / "dist"

    # Clean if requested
    if clean and dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Build using uv build
    cmd = ["uv", "build"]
    if "wheel" in formats and "sdist" not in formats:
        cmd.append("--wheel")
    elif "sdist" in formats and "wheel" not in formats:
        cmd.append("--sdist")

    result = subprocess.run(  # noqa: S603  # nosec B603
        cmd,
        cwd=project_path,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {
            "artifacts": [],
            "error": result.stderr,
        }

    # List created artifacts
    artifacts = []
    if dist_dir.exists():
        for f in dist_dir.iterdir():
            artifact_type = "wheel" if f.suffix == ".whl" else "sdist"
            artifacts.append(
                {
                    "path": str(f),
                    "format": artifact_type,
                    "size": f.stat().st_size,
                }
            )

    return {"artifacts": artifacts}


def publish_project(
    project_path: str | Path,
    repository: str = "pypi",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Publish project to package repository.

    Args:
        project_path: Path to project directory.
        repository: Target repository (pypi, testpypi).
        dry_run: Simulate without uploading.

    Returns:
        Dict with publish result.
    """
    project_path = Path(project_path)

    if dry_run:
        return {
            "repository": repository,
            "package": project_path.name,
            "version": "0.1.0",
            "dry_run": True,
        }

    # Build first
    build_result = build_project(project_path)
    if not build_result["artifacts"]:
        return {"error": "No artifacts to publish"}

    # Publish using uv publish
    cmd = ["uv", "publish"]
    if repository == "testpypi":
        cmd.extend(["--publish-url", "https://test.pypi.org/legacy/"])

    result = subprocess.run(  # noqa: S603  # nosec B603
        cmd,
        cwd=project_path,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {"error": result.stderr}

    return {
        "repository": repository,
        "package": project_path.name,
        "version": "0.1.0",
    }


# =============================================================================
# Hot Reload / File Watching
# =============================================================================


def _get_python_file_filter() -> Any:
    """Get a filter function for Python files.

    Returns:
        A filter function that accepts Python files and excludes cache directories.
    """

    def filter_func(_: Any, path: str) -> bool:
        """Filter for Python files, excluding cache directories."""
        return path.endswith(".py") and "__pycache__" not in path and ".venv" not in path

    return filter_func


def create_file_watcher(path: str | Path) -> Any:
    """Create a file watcher for hot reload.

    Args:
        path: Directory to watch.

    Returns:
        Watchfiles watcher configuration.
    """
    from watchfiles import watch  # noqa: PLC0415

    # Return a configured watch generator
    # Filter to only Python files, ignore __pycache__
    return watch(
        path,
        watch_filter=_get_python_file_filter(),
    )


def _build_server_command(
    interface: str,
    project_path: Path,
    rest_port: int = 8000,
    mcp_port: int = 8080,
) -> list[str]:
    """Build command to start a server for the given interface.

    Args:
        interface: Interface type (rest, mcp).
        project_path: Path to the project directory.
        rest_port: Port for REST API server.
        mcp_port: Port for MCP server.

    Returns:
        Command list to start the server.
    """
    if interface == "rest":
        # Use uvicorn with the app discovery pattern
        # Assumes app.py with `app` variable exists
        return [
            "uvicorn",
            "app:app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(rest_port),
            "--app-dir",
            str(project_path / "src"),
        ]
    if interface == "mcp":
        # Use hive CLI to serve MCP
        return [
            "hive",
            "mcp",
            "serve",
            "--transport",
            "sse",
            "--port",
            str(mcp_port),
        ]
    return []


def start_dev_server(
    project_path: str | Path,
    interfaces: list[str] | None = None,
    rest_port: int = 8000,
    mcp_port: int = 8080,
) -> None:
    """Start development server with hot reload.

    Uses watchfiles.run_process to manage server subprocesses with automatic
    restart when files change.

    Args:
        project_path: Path to project.
        interfaces: Interfaces to enable (cli, tui, rest, mcp).
        rest_port: Port for REST API.
        mcp_port: Port for MCP server.
    """
    interfaces = interfaces or ["cli"]
    project_path = Path(project_path)

    console.print("[bold green]Starting development server[/bold green]")
    console.print(f"  Interfaces: {', '.join(interfaces)}")
    console.print("  Hot reload: enabled")

    # Determine which server to run
    # Priority: rest > mcp > cli (only run one at a time with hot reload)
    server_interface = None
    if "rest" in interfaces:
        server_interface = "rest"
        console.print(f"  REST API: http://127.0.0.1:{rest_port}")
        console.print(f"  OpenAPI docs: http://127.0.0.1:{rest_port}/docs")
    elif "mcp" in interfaces:
        server_interface = "mcp"
        console.print(f"  MCP Server: http://127.0.0.1:{mcp_port}")

    console.print("\n[yellow]Watching for changes...[/yellow]")

    if server_interface:
        # Use watchfiles.run_process for actual server reload
        try:
            from watchfiles import run_process  # noqa: PLC0415

            cmd = _build_server_command(
                server_interface,
                project_path,
                rest_port=rest_port,
                mcp_port=mcp_port,
            )

            if cmd:
                console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")
                run_process(
                    project_path,
                    target=cmd[0],
                    args=tuple(cmd[1:]),
                    watch_filter=_get_python_file_filter(),
                    callback=lambda changes: console.print(
                        f"\n[cyan]Detected {len(changes)} change(s), restarting...[/cyan]\n"
                    ),
                )
            else:
                console.print(f"[red]No command configured for interface: {server_interface}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping development server[/yellow]")
    else:
        # For CLI-only mode, just watch and report changes (no server to restart)
        try:
            for changes in create_file_watcher(project_path):
                console.print(f"[cyan]Detected changes:[/cyan] {len(changes)} files")
                for change_type, path in changes:
                    console.print(f"  {change_type}: {path}")
                console.print("[dim]Note: CLI mode - no server to restart[/dim]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping file watcher[/yellow]")


# =============================================================================
# CLI Commands
# =============================================================================


@project_app.command("new")
def new_command(  # noqa: PLR0913
    name: Annotated[str, typer.Argument(help="Project name")],
    path: Annotated[
        str | None,
        typer.Option("--path", "-p", help="Directory to create project in"),
    ] = None,
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Project description"),
    ] = "A Hive application",
    author: Annotated[
        str,
        typer.Option("--author", "-a", help="Author name"),
    ] = "",
    features: Annotated[
        str | None,
        typer.Option(
            "--features", "-f", help="Features to enable (comma-separated: tui,mcp,rest,all)"
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing directory"),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON"),
    ] = False,
) -> None:
    """Create a new Hive project.

    Examples:
        hive new myapp
        hive new myapp --features tui,mcp
        hive new myapp --author "John Doe" --description "My app"
    """
    feature_list = features.split(",") if features else None

    try:
        project_path = create_project(
            name=name,
            path=path,
            description=description,
            author=author,
            features=feature_list,
            force=force,
        )

        if json_output:
            console.print_json(
                data={
                    "path": project_path,
                    "name": name,
                    "next_steps": [
                        f"cd {name}",
                        "uv sync",
                        f"{name} hello",
                    ],
                }
            )
        else:
            console.print(f"\n[bold green]Created project:[/bold green] {project_path}")
            console.print("\n[bold]Next steps:[/bold]")
            console.print(f"  cd {name}")
            console.print("  uv sync")
            console.print(f"  {name} hello")
    except FileExistsError as e:
        if json_output:
            console.print_json(data={"error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e


@project_app.command("dev")
def dev_command(
    interfaces: Annotated[
        str,
        typer.Option(
            "--interfaces", "-i", help="Interfaces to enable (comma-separated: cli,tui,rest,mcp)"
        ),
    ] = "cli",
    rest_port: Annotated[
        int,
        typer.Option("--rest-port", help="REST API port"),
    ] = 8000,
    mcp_port: Annotated[
        int,
        typer.Option("--mcp-port", help="MCP server port"),
    ] = 8080,
) -> None:
    """Start development server with hot reload.

    Examples:
        hive dev
        hive dev --interfaces cli,rest
        hive dev --rest-port 8080
    """
    interface_list = interfaces.split(",")
    start_dev_server(
        project_path=Path.cwd(),
        interfaces=interface_list,
        rest_port=rest_port,
        mcp_port=mcp_port,
    )


@project_app.command("build")
def build_command(
    formats: Annotated[
        str,
        typer.Option("--format", "-f", help="Build formats (comma-separated: wheel,sdist)"),
    ] = "wheel",
    clean: Annotated[
        bool,
        typer.Option("--clean", "-c", help="Clean dist/ before building"),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON"),
    ] = False,
) -> None:
    """Build project artifacts.

    Examples:
        hive build
        hive build --format wheel,sdist
        hive build --clean
    """
    format_list = formats.split(",")
    result = build_project(
        project_path=Path.cwd(),
        formats=format_list,
        clean=clean,
    )

    if json_output:
        console.print_json(data=result)
    elif "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)
    else:
        console.print("[bold green]Build complete![/bold green]")
        for artifact in result["artifacts"]:
            console.print(f"  {artifact['path']} ({artifact['size']} bytes)")


@project_app.command("publish")
def publish_command(
    repository: Annotated[
        str,
        typer.Option("--repository", "-r", help="Target repository (pypi, testpypi)"),
    ] = "pypi",
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Simulate without uploading"),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON"),
    ] = False,
) -> None:
    """Publish package to repository.

    Examples:
        hive publish
        hive publish --repository testpypi
        hive publish --dry-run
    """
    result = publish_project(
        project_path=Path.cwd(),
        repository=repository,
        dry_run=dry_run,
    )

    if json_output:
        console.print_json(data=result)
    elif "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        raise typer.Exit(code=1)
    else:
        console.print("[bold green]Published successfully![/bold green]")
        console.print(f"  Repository: {result['repository']}")
        console.print(f"  Package: {result['package']}")
        console.print(f"  Version: {result['version']}")
