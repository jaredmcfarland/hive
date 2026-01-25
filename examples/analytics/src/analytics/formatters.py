"""Rich output formatters for Analytics example.

Provides beautiful terminal output for reports and data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from analytics.entities import Report, TableInfo


def format_report(report: Report, console: Console | None = None) -> Table:
    """Format a report as a Rich table.

    Args:
        report: Report to format.
        console: Optional console for output.

    Returns:
        Rich Table object.
    """
    table = Table(title=report.title, show_header=True, header_style="bold cyan")

    # Add columns
    for col in report.columns:
        table.add_column(col, style="dim" if col == "id" else None)

    # Add rows
    for row in report.data:
        table.add_row(*[str(row.get(col, "")) for col in report.columns])

    if console:
        console.print(table)

    return table


def format_table_info(info: TableInfo, console: Console | None = None) -> Table:
    """Format table information as a Rich table.

    Args:
        info: TableInfo to format.
        console: Optional console for output.

    Returns:
        Rich Table object.
    """
    table = Table(title=f"Table: {info.name}", show_header=True, header_style="bold green")

    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Name", info.name)
    table.add_row("Row Count", f"{info.row_count:,}")
    table.add_row("Columns", str(len(info.columns)))

    if console:
        console.print(table)

    return table


def format_summary(
    data: dict[str, Any],
    title: str = "Summary",
    console: Console | None = None,
) -> Table:
    """Format summary statistics as a Rich table.

    Args:
        data: Dictionary of metric name to value.
        title: Table title.
        console: Optional console for output.

    Returns:
        Rich Table object.
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    for key, value in data.items():
        formatted_value = _format_value(value)
        table.add_row(key, formatted_value)

    if console:
        console.print(table)

    return table


def _format_value(value: Any) -> str:
    """Format a value for display.

    Args:
        value: Value to format.

    Returns:
        Formatted string.
    """
    if value is None:
        return "-"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.2f}"
        return f"{value:.4f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
