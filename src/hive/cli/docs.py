"""Hive CLI documentation commands.

This module provides the `hive docs` subcommand group for generating
documentation from Hive application specifications.

Usage:
    hive docs generate --format markdown
    hive docs generate --format markdown --output docs/
    hive docs generate --format manpage --output man/
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from rich.console import Console
import typer

# Create the docs CLI app
docs_app = typer.Typer(
    name="docs",
    help="Generate documentation from Hive application specification",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


@docs_app.command("generate")
def generate_command(
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: markdown, manpage",
        ),
    ] = "markdown",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output directory (stdout if not specified)",
        ),
    ] = None,
    include_private: Annotated[
        bool,
        typer.Option(
            "--include-private",
            help="Include private commands (underscore-prefixed)",
        ),
    ] = False,
    include_examples: Annotated[
        bool,
        typer.Option(
            "--include-examples/--no-examples",
            help="Include usage examples from docstrings",
        ),
    ] = True,
    include_contracts: Annotated[
        bool,
        typer.Option(
            "--include-contracts/--no-contracts",
            help="Include @requires/@ensures documentation",
        ),
    ] = True,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output result as JSON",
        ),
    ] = False,
) -> None:
    """Generate documentation from the Hive application specification.

    Reads the application specification and generates documentation in the
    specified format. Supports markdown and man page (troff) formats.

    If --output is not specified, documentation is written to stdout.
    If --output is specified, files are created in that directory.

    Examples:
        # Generate markdown to stdout
        hive docs generate --format markdown

        # Generate markdown to docs/ directory
        hive docs generate --format markdown --output docs/

        # Generate man pages
        hive docs generate --format manpage --output man/
    """
    # Import here to avoid circular imports
    from hive.docs.models import DocumentationConfig  # noqa: PLC0415

    if format_ not in ("markdown", "manpage"):
        console.print(f"[red]Error:[/red] Unknown format: {format_}")
        console.print("Supported formats: markdown, manpage")
        raise typer.Exit(code=1)

    # After validation, format_ is narrowed to Literal["markdown", "manpage"]
    config = DocumentationConfig(
        format=format_,
        output_dir=output,
        include_private=include_private,
        include_examples=include_examples,
        include_contracts=include_contracts,
    )

    try:
        # Get the current app
        app = _get_current_app()

        # Generate documentation based on format
        if format_ == "markdown":
            from hive.docs.markdown import MarkdownGenerator  # noqa: PLC0415

            generator = MarkdownGenerator(app)
            result = generator.generate(config)
        else:
            # Man page generation
            from hive.docs.manpage import ManPageGenerator  # noqa: PLC0415

            generator = ManPageGenerator(app)
            result = generator.generate(config)

        # Output result
        if json_output:
            import json  # noqa: PLC0415

            output_data = {
                "status": "success",
                "files_generated": [str(f) for f in result.files_generated],
                "commands_documented": result.commands_documented,
                "queries_documented": result.queries_documented,
                "entities_documented": result.entities_documented,
                "warnings": result.warnings,
            }
            console.print(json.dumps(output_data, indent=2))
        elif result.content:
            # Output to stdout
            console.print(result.content, markup=False)
        else:
            # Output summary for file generation
            console.print(f"[green]✓[/green] Generated {len(result.files_generated)} files")
            for f in result.files_generated:
                console.print(f"  - {f}")
            if result.warnings:
                console.print(f"\n[yellow]Warnings ({len(result.warnings)}):[/yellow]")
                for w in result.warnings:
                    console.print(f"  - {w}")

    except Exception as e:
        if json_output:
            import json  # noqa: PLC0415

            console.print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

    raise typer.Exit(code=0)


def _get_current_app() -> App:  # type: ignore[name-defined]  # noqa: F821
    """Get the current project's App instance.

    Discovers the app by searching common module locations.
    """
    from hive.cli.utils import AppDiscoveryError, discover_app  # noqa: PLC0415

    try:
        return discover_app()
    except AppDiscoveryError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
