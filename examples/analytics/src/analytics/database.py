"""DuckDB configuration for Analytics example.

Provides database connection management and utilities.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import duckdb

if TYPE_CHECKING:
    from duckdb import DuckDBPyConnection

# Default database path
DEFAULT_DB_PATH = os.environ.get("ANALYTICS_DB_PATH", ":memory:")


class DuckDBConnection:
    """Managed DuckDB connection.

    Provides a context manager for database operations.

    Attributes:
        db_path: Path to the database file or ':memory:'.
        connection: Active DuckDB connection.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to database file or ':memory:' for in-memory.
        """
        self.db_path = db_path
        self._connection: DuckDBPyConnection | None = None

    @property
    def connection(self) -> DuckDBPyConnection:
        """Get the active connection, creating if needed.

        Returns:
            Active DuckDB connection.
        """
        if self._connection is None:
            self._connection = duckdb.connect(self.db_path)
        return self._connection

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def execute(self, query: str, params: list[Any] | None = None) -> Any:
        """Execute a query.

        Args:
            query: SQL query to execute.
            params: Optional query parameters.

        Returns:
            Query result.
        """
        if params:
            return self.connection.execute(query, params)
        return self.connection.execute(query)

    def fetchone(self, query: str, params: list[Any] | None = None) -> tuple[Any, ...] | None:
        """Execute query and fetch one row.

        Args:
            query: SQL query to execute.
            params: Optional query parameters.

        Returns:
            Single row tuple or None.
        """
        result = self.execute(query, params)
        row: tuple[Any, ...] | None = result.fetchone()
        return row

    def fetchall(self, query: str, params: list[Any] | None = None) -> list[tuple[Any, ...]]:
        """Execute query and fetch all rows.

        Args:
            query: SQL query to execute.
            params: Optional query parameters.

        Returns:
            List of row tuples.
        """
        result = self.execute(query, params)
        rows: list[tuple[Any, ...]] = result.fetchall()
        return rows

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if table exists.
        """
        query = """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = ?
        """
        row = self.fetchone(query, [table_name])
        return bool(row and row[0] > 0)

    def get_tables(self) -> list[str]:
        """Get list of all tables.

        Returns:
            List of table names.
        """
        rows = self.fetchall(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        )
        return [row[0] for row in rows]


# Global connection instance
_db: DuckDBConnection | None = None


def get_db(db_path: str = DEFAULT_DB_PATH) -> DuckDBConnection:
    """Get or create the global database connection.

    Args:
        db_path: Path to database file.

    Returns:
        DuckDBConnection instance.
    """
    global _db  # noqa: PLW0603
    if _db is None:
        _db = DuckDBConnection(db_path)
    return _db


@contextmanager
def temp_db() -> Generator[DuckDBConnection, None, None]:
    """Create a temporary in-memory database.

    Yields:
        Temporary DuckDBConnection.
    """
    conn = DuckDBConnection(":memory:")
    try:
        yield conn
    finally:
        conn.close()
