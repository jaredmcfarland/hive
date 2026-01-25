"""Hive CLI test generation commands.

This module provides the `hive test` subcommand group for generating
tests from Hive application specifications.

Usage:
    hive test generate-conformance --output tests/test_conformance.py
    hive test generate-properties --output tests/test_properties.py
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from rich.console import Console
import typer

if TYPE_CHECKING:
    from hive.app import App

# Create the test CLI app
test_app = typer.Typer(
    name="test",
    help="Generate tests from Hive application specification",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


@test_app.command("generate-conformance")
def generate_conformance_command(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (stdout if not specified)",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output result as JSON",
        ),
    ] = False,
) -> None:
    """Generate conformance tests from @requires/@ensures contracts.

    Analyzes the application's commands and queries for contract decorators
    and generates pytest test cases that verify contract compliance.

    Generated tests include:
    - @requires tests: Verify preconditions are enforced
    - @ensures tests: Verify postconditions hold after execution
    - @invariant tests: Verify class invariants are maintained

    Examples:
        # Generate conformance tests to stdout
        hive test generate-conformance

        # Generate conformance tests to file
        hive test generate-conformance --output tests/test_conformance.py
    """
    try:
        from hive.testing.conformance import ConformanceGenerator  # noqa: PLC0415

        app = _get_current_app()
        generator = ConformanceGenerator(app)
        result = generator.generate()

        # Output result
        if json_output:
            import json  # noqa: PLC0415

            output_data = {
                "status": "success",
                "test_cases": len(result.test_cases),
                "warnings": result.warnings,
                "output": str(output) if output else "stdout",
            }
            console.print(json.dumps(output_data, indent=2))
        elif output:
            # Write to file
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result.code)
            console.print(
                f"[green]✓[/green] Generated {len(result.test_cases)} test(s) to {output}"
            )
            if result.warnings:
                for w in result.warnings:
                    console.print(f"  [yellow]Warning:[/yellow] {w}")
        else:
            # Output to stdout
            console.print(result.code, markup=False)

    except Exception as e:
        if json_output:
            import json  # noqa: PLC0415

            console.print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

    raise typer.Exit(code=0)


@test_app.command("generate-properties")
def generate_properties_command(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (stdout if not specified)",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output result as JSON",
        ),
    ] = False,
) -> None:
    """Generate property-based tests using hypothesis.

    Analyzes the application's commands and queries for refinement type
    parameters and generates hypothesis tests with appropriate strategies.

    Generated tests:
    - Use strategy_for_type() for parameter generation
    - Test that commands accept valid inputs
    - Test that type constraints are enforced

    Examples:
        # Generate property tests to stdout
        hive test generate-properties

        # Generate property tests to file
        hive test generate-properties --output tests/test_properties.py
    """
    try:
        from hive.testing.properties import PropertyGenerator  # noqa: PLC0415

        app = _get_current_app()
        generator = PropertyGenerator(app)
        result = generator.generate()

        # Output result
        if json_output:
            import json  # noqa: PLC0415

            output_data = {
                "status": "success",
                "test_cases": len(result.test_cases),
                "warnings": result.warnings,
                "output": str(output) if output else "stdout",
            }
            console.print(json.dumps(output_data, indent=2))
        elif output:
            # Write to file
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result.code)
            console.print(
                f"[green]✓[/green] Generated {len(result.test_cases)} test(s) to {output}"
            )
            if result.warnings:
                for w in result.warnings:
                    console.print(f"  [yellow]Warning:[/yellow] {w}")
        else:
            # Output to stdout
            console.print(result.code, markup=False)

    except Exception as e:
        if json_output:
            import json  # noqa: PLC0415

            console.print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e

    raise typer.Exit(code=0)


def _get_current_app() -> App:
    """Get the current project's App instance.

    Discovers the app by searching common module locations.
    """
    from hive.cli.utils import AppDiscoveryError, discover_app  # noqa: PLC0415

    try:
        return discover_app()
    except AppDiscoveryError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
