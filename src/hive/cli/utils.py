"""Shared CLI utilities.

Common utilities used across CLI command modules including app discovery,
output formatting, and error handling.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

from rich.console import Console

if TYPE_CHECKING:
    from hive.app import App

console = Console()


class AppDiscoveryError(Exception):
    """Raised when app discovery fails."""


def discover_app(
    module_names: list[str] | None = None,
    app_attr: str = "app",
    cwd: Path | None = None,
) -> App:
    """Discover and load the Hive App instance from the current project.

    Searches for a Hive App instance by importing common module locations
    and looking for an 'app' attribute.

    Args:
        module_names: List of module names to search for the app.
            Defaults to ["app", "main", "src.app", "src.main"].
        app_attr: Attribute name to look for in each module.
            Defaults to "app".
        cwd: Working directory to add to sys.path.
            Defaults to Path.cwd().

    Returns:
        The discovered Hive App instance.

    Raises:
        AppDiscoveryError: If no Hive app could be found.

    Example:
        >>> app = discover_app()
        >>> print(app.name)
        myapp
    """
    if module_names is None:
        module_names = ["app", "main", "src.app", "src.main"]

    if cwd is None:
        cwd = Path.cwd()

    # Add current directory to path for imports
    cwd_str = str(cwd)
    if cwd_str not in sys.path:
        sys.path.insert(0, cwd_str)

    errors: list[str] = []

    for module_name in module_names:
        try:
            module = __import__(module_name, fromlist=[app_attr])
            if hasattr(module, app_attr):
                app = getattr(module, app_attr)
                # Validate it's actually an App instance
                from hive.app import App  # noqa: PLC0415

                if isinstance(app, App):
                    return app
                errors.append(f"{module_name}.{app_attr} is not a Hive App instance")
            else:
                errors.append(f"{module_name} has no '{app_attr}' attribute")
        except ImportError as e:
            errors.append(f"Could not import {module_name}: {e}")

    # Build helpful error message
    searched = "\n".join(f"  - {name}.{app_attr}" for name in module_names)
    msg = (
        f"No Hive app found. Searched for:\n{searched}\n\n"
        "Create an app.py with:\n"
        "  from hive import App\n"
        "  app = App('myapp')"
    )
    raise AppDiscoveryError(msg)


def print_error(message: str, json_output: bool = False) -> None:
    """Print an error message in the appropriate format.

    Args:
        message: The error message.
        json_output: If True, output as JSON.
    """
    if json_output:
        console.print_json(data={"status": "error", "error": message})
    else:
        console.print(f"[red]Error:[/red] {message}")


def print_success(message: str, json_output: bool = False, **data: Any) -> None:
    """Print a success message in the appropriate format.

    Args:
        message: The success message.
        json_output: If True, output as JSON.
        **data: Additional data to include in JSON output.
    """
    if json_output:
        output = {"status": "success", "message": message, **data}
        console.print_json(data=output)
    else:
        console.print(f"[green]✓[/green] {message}")
