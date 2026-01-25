"""Data entities for Analytics example.

Defines the data models for analytics operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DataPoint:
    """A single data point for analytics.

    Attributes:
        id: Unique identifier.
        timestamp: When the data point was recorded.
        category: Category or grouping label.
        value: Numeric value.
        metadata: Optional additional data.
    """

    id: int
    timestamp: datetime
    category: str
    value: float
    metadata: dict[str, Any] | None = None


@dataclass
class Report:
    """Analytics report with aggregated results.

    Attributes:
        title: Report title.
        generated_at: When the report was generated.
        row_count: Number of rows in the result.
        columns: Column names in the result.
        data: List of row dictionaries.
        summary: Optional summary statistics.
    """

    title: str
    generated_at: datetime
    row_count: int
    columns: list[str]
    data: list[dict[str, Any]]
    summary: dict[str, Any] | None = None


@dataclass
class TableInfo:
    """Information about a database table.

    Attributes:
        name: Table name.
        row_count: Number of rows.
        columns: List of column names.
        column_types: Mapping of column names to types.
    """

    name: str
    row_count: int
    columns: list[str]
    column_types: dict[str, str] = field(default_factory=dict)
