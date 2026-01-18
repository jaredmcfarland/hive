"""Output formatting for CLI commands."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
import json
import sys
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table


class OutputFormat(Enum):
    """Supported output formats."""

    JSON = "json"
    TABLE = "table"
    CSV = "csv"


class OutputFormatter:
    """Format-aware output handler for commands.

    Handles output formatting based on the selected format (JSON, TABLE, CSV).
    In JSON mode, only result() output is shown; info() is suppressed.
    Warnings and errors always appear (to stderr).
    """

    def __init__(
        self,
        format: OutputFormat = OutputFormat.TABLE,
        quiet: bool = False,
        console: Console | None = None,
    ) -> None:
        """Initialize the output formatter.

        Args:
            format: Output format to use.
            quiet: Suppress non-essential output.
            console: Optional Rich console for output.
        """
        self.format = format
        self.quiet = quiet
        self._console = console or Console()
        self._err_console = Console(stderr=True)

    def result(self, data: BaseModel | Sequence[BaseModel] | dict[str, Any] | list[Any]) -> None:
        """Output the main result of a command.

        Args:
            data: The result data to output.
        """
        if self.format == OutputFormat.JSON:
            self._output_json(data)
        elif self.format == OutputFormat.TABLE:
            self._output_table_result(data)
        elif self.format == OutputFormat.CSV:
            self._output_csv(data)

    def table(
        self,
        items: Sequence[BaseModel | dict[str, Any]],
        columns: list[str] | None = None,
    ) -> None:
        """Output items as a table.

        Args:
            items: Items to display.
            columns: Column names to show (defaults to all fields).
        """
        if self.format == OutputFormat.JSON:
            self._output_json(items)
            return

        if not items:
            self.info("No items to display")
            return

        # Determine columns from first item
        first = items[0]
        if columns is None:
            if isinstance(first, BaseModel):
                columns = list(type(first).model_fields.keys())
            elif isinstance(first, dict):
                columns = list(first.keys())
            else:  # pragma: no cover
                columns = ["value"]

        # Create Rich table
        table = Table()
        for col in columns:
            table.add_column(col.replace("_", " ").title())

        for item in items:
            if isinstance(item, BaseModel):
                values = [str(getattr(item, col, "")) for col in columns]
            elif isinstance(item, dict):
                values = [str(item.get(col, "")) for col in columns]
            else:  # pragma: no cover
                values = [str(item)]
            table.add_row(*values)

        self._console.print(table)

    def info(self, message: str) -> None:
        """Output an informational message.

        Suppressed in JSON mode and when quiet is True.

        Args:
            message: The message to display.
        """
        if self.format == OutputFormat.JSON or self.quiet:
            return

        self._console.print(f"[blue]ℹ[/blue] {message}")

    def warning(self, message: str) -> None:
        """Output a warning message.

        Always shown, even in JSON mode (to stderr).

        Args:
            message: The warning message.
        """
        self._err_console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        """Output an error message.

        Always shown to stderr.

        Args:
            message: The error message.
        """
        self._err_console.print(f"[red]✗[/red] {message}")

    def confirm(self, prompt: str, default: bool = False) -> bool:  # pragma: no cover
        """Ask for confirmation.

        In non-interactive mode or when --yes is set, returns the default.

        Args:
            prompt: The confirmation prompt.
            default: Default value if non-interactive.

        Returns:
            True if confirmed, False otherwise.
        """
        if self.format == OutputFormat.JSON or not sys.stdin.isatty():
            return default

        from rich.prompt import Confirm

        return Confirm.ask(prompt, default=default)

    def _output_json(self, data: Any) -> None:
        """Output data as JSON."""
        if isinstance(data, BaseModel):
            output = data.model_dump()
        elif isinstance(data, (list, tuple)):
            output = [item.model_dump() if isinstance(item, BaseModel) else item for item in data]
        elif isinstance(data, dict):
            output = data
        else:  # pragma: no cover
            output = data

        print(json.dumps(output, indent=None, default=str))

    def _output_table_result(self, data: Any) -> None:
        """Output a single result as a table."""
        if isinstance(data, BaseModel):
            table = Table(show_header=True)
            table.add_column("Field")
            table.add_column("Value")

            for field, value in data.model_dump().items():
                table.add_row(field.replace("_", " ").title(), str(value))

            self._console.print(table)
        elif isinstance(data, (list, tuple)):
            self.table(data)
        elif isinstance(data, dict):
            table = Table(show_header=True)
            table.add_column("Key")
            table.add_column("Value")

            for key, value in data.items():
                table.add_row(str(key), str(value))

            self._console.print(table)
        else:  # pragma: no cover
            self._console.print(str(data))

    def _output_csv(self, data: Any) -> None:
        """Output data as CSV."""
        import csv
        import io

        if isinstance(data, BaseModel):
            items = [data]
        elif isinstance(data, (list, tuple)):
            items = list(data)
        else:  # pragma: no cover
            print(str(data))
            return

        if not items:
            return

        # Get field names from first item
        first = items[0]
        if isinstance(first, BaseModel):
            fieldnames = list(type(first).model_fields.keys())
        elif isinstance(first, dict):
            fieldnames = list(first.keys())
        else:  # pragma: no cover
            print("\n".join(str(item) for item in items))
            return

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            if isinstance(item, BaseModel):
                writer.writerow(item.model_dump())
            elif isinstance(item, dict):
                writer.writerow(item)

        print(output.getvalue(), end="")
