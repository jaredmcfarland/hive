"""Analytics Example - Hive DuckDB Integration.

Demonstrates data analytics with DuckDB backend and rich output formatting.

Example:
    $ analytics init
    $ analytics data import sales.csv --table sales
    $ analytics report summary --table sales
"""

from __future__ import annotations

# Import commands to register them
from analytics import commands as _commands  # noqa: F401
from analytics.app import app

# Generate CLI from app
cli = app.cli()

__all__ = ["app", "cli"]
