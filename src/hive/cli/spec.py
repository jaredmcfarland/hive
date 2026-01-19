"""Hive spec CLI commands.

Provides commands for exporting and comparing application specifications.

Usage:
    hive spec export --format json
    hive spec export --format json -o spec.json
    hive spec diff v1.json v2.json
    hive spec diff v1.json v2.json --fail-on-breaking
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from rich.console import Console
import typer

# Create the spec subcommand group
spec_app = typer.Typer(
    name="spec",
    help="Specification export and comparison commands",
    no_args_is_help=True,
)

console = Console()


@spec_app.command("export")
def export_command(
    format: Annotated[  # noqa: A002
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (json or toml)",
        ),
    ] = "json",
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (stdout if not specified)",
        ),
    ] = None,
    include_internal: Annotated[
        bool,
        typer.Option(
            "--include-internal",
            help="Include hidden/internal commands",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON",
        ),
    ] = False,
) -> None:
    """Export application specification as JSON Schema or TOML.

    Examples:
        hive spec export --format json
        hive spec export --format json -o spec.json
        hive spec export --format toml
    """
    try:
        # Import here to avoid circular imports and allow lazy loading
        from hive.spec.export import export_specification  # noqa: PLC0415

        # For now, create an empty app for demonstration
        # In practice, this would load the current project's app
        app = _get_current_app()

        result = export_specification(
            app,
            format=format,  # type: ignore[arg-type]
            output=output,
            include_internal=include_internal,
        )

        if output:
            if json_output:
                console.print_json(data={"status": "success", "output": output})
            else:
                console.print(f"[green]✓[/green] Specification exported to {output}")
        else:
            # Print to stdout - use markup=False to avoid Rich interpreting
            # TOML section headers like [metadata] as markup tags
            console.print(result, markup=False, highlight=False)

    except Exception as e:
        if json_output:
            console.print_json(data={"status": "error", "error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


@spec_app.command("diff")
def diff_command(  # noqa: C901, PLR0912
    v1_path: Annotated[
        Path,
        typer.Argument(
            help="Path to first specification file (older version)",
        ),
    ],
    v2_path: Annotated[
        Path,
        typer.Argument(
            help="Path to second specification file (newer version)",
        ),
    ],
    format: Annotated[  # noqa: A002
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (text or json)",
        ),
    ] = "text",
    fail_on_breaking: Annotated[
        bool,
        typer.Option(
            "--fail-on-breaking",
            help="Exit with error code if breaking changes detected",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON",
        ),
    ] = False,
) -> None:
    """Compare two specification files and identify differences.

    Detects breaking changes that may affect API consumers.

    Examples:
        hive spec diff v1.json v2.json
        hive spec diff v1.json v2.json --format json
        hive spec diff v1.json v2.json --fail-on-breaking
    """
    try:
        from hive.spec.diff import diff_specifications  # noqa: PLC0415

        # Load specification files
        if not v1_path.exists():
            msg = f"File not found: {v1_path}"
            raise typer.BadParameter(msg)  # noqa: TRY301
        if not v2_path.exists():
            msg = f"File not found: {v2_path}"
            raise typer.BadParameter(msg)  # noqa: TRY301

        with v1_path.open() as f:
            spec1 = json.load(f)
        with v2_path.open() as f:
            spec2 = json.load(f)

        # Compute diff
        diff = diff_specifications(spec1, spec2)

        # Output based on format
        if format == "json" or json_output:
            output = {
                "v1_version": diff.v1_version,
                "v2_version": diff.v2_version,
                "compared_at": diff.compared_at.isoformat(),
                "summary": diff.summary,
                "has_breaking_changes": diff.has_breaking_changes,
                "changes": [
                    {
                        "path": c.path,
                        "change_type": c.change_type,
                        "old_value": c.old_value,
                        "new_value": c.new_value,
                        "breaking": c.breaking,
                    }
                    for c in diff.changes
                ],
                "breaking_changes": [
                    {
                        "path": c.path,
                        "change_type": c.change_type,
                        "old_value": c.old_value,
                        "new_value": c.new_value,
                    }
                    for c in diff.breaking_changes
                ],
            }
            console.print_json(data=output)
        else:
            # Text format
            console.print(
                f"\nComparing [cyan]{v1_path}[/cyan] ({diff.v1_version}) → "
                f"[cyan]{v2_path}[/cyan] ({diff.v2_version})\n"
            )

            if diff.breaking_changes:
                console.print(f"[red]BREAKING CHANGES ({len(diff.breaking_changes)}):[/red]")
                for change in diff.breaking_changes:
                    console.print(f"  [red]✗[/red] {change.path}: {change.change_type.upper()}")

            if diff.changes:
                console.print(f"\n[yellow]Changes ({len(diff.changes)}):[/yellow]")
                for change in diff.changes:
                    symbol = (
                        "+"
                        if change.change_type == "added"
                        else "-"
                        if change.change_type == "removed"
                        else "~"
                    )
                    color = (
                        "green"
                        if change.change_type == "added"
                        else "red"
                        if change.change_type == "removed"
                        else "yellow"
                    )
                    console.print(
                        f"  [{color}]{symbol}[/{color}] {change.path}: {change.change_type.upper()}"
                    )

            console.print(f"\n[bold]Summary:[/bold] {diff.summary}")

        # Exit with error if breaking changes and --fail-on-breaking
        if fail_on_breaking and diff.has_breaking_changes:
            raise typer.Exit(1)  # noqa: TRY301

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
