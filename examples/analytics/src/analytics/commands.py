"""Commands for Analytics example.

Demonstrates data import and analytics queries with DuckDB.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from hive.contracts import requires
from hive.core.decorators import command
from hive.runtime.context import ExecutionContext

from analytics.app import app
from analytics.database import get_db
from analytics.entities import Report, TableInfo

# --- Database Commands ---


@command(app)
async def init(ctx: ExecutionContext, db_path: str = ":memory:") -> str:  # noqa: ARG001
    """Initialize the analytics database.

    Args:
        ctx: Execution context.
        db_path: Path to database file or ':memory:'.

    Returns:
        Success message.

    Example:
        $ analytics init
        Database initialized at :memory:
    """
    db = get_db(db_path)
    # Ensure connection is established
    _ = db.connection
    return f"Database initialized at {db_path}"


@command(app)
async def list_tables(ctx: ExecutionContext) -> list[TableInfo]:  # noqa: ARG001
    """List all tables in the database.

    Args:
        ctx: Execution context.

    Returns:
        List of TableInfo objects.

    Example:
        $ analytics list-tables
        [TableInfo(name='sales', row_count=1000, ...)]
    """
    db = get_db()
    tables = db.get_tables()

    result = []
    for table_name in tables:
        # Get row count
        row = db.fetchone(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
        row_count = row[0] if row else 0

        # Get column info
        cols = db.fetchall(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?",
            [table_name],
        )

        result.append(
            TableInfo(
                name=table_name,
                row_count=row_count,
                columns=[c[0] for c in cols],
                column_types={c[0]: c[1] for c in cols},
            )
        )

    return result


# --- Data Import Commands ---


@command(app)
@requires(lambda _ctx, file_path, **_kw: Path(file_path).exists(), "File must exist")
async def import_data(
    ctx: ExecutionContext,  # noqa: ARG001
    file_path: str,
    table: str = "data",
    file_format: Literal["csv", "json", "parquet"] = "csv",
) -> int:
    """Import data from a file into the database.

    Args:
        ctx: Execution context.
        file_path: Path to the data file.
        table: Name of the table to create/replace.
        file_format: File format (csv, json, parquet).

    Returns:
        Number of rows imported.

    Example:
        $ analytics import-data sales.csv --table sales
        Imported 1000 rows into 'sales'
    """
    db = get_db()

    # DuckDB can infer format and schema from file
    if file_format == "csv":
        query = f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?)"  # noqa: S608
        db.execute(query, [file_path])
    elif file_format == "json":
        query = f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_json_auto(?)"  # noqa: S608
        db.execute(query, [file_path])
    elif file_format == "parquet":
        query = f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_parquet(?)"  # noqa: S608
        db.execute(query, [file_path])

    # Get row count
    row = db.fetchone(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
    return row[0] if row else 0


# --- Analytics Commands ---


@command(app)
@requires(lambda _ctx, table, **_kw: len(table.strip()) > 0, "Table name required")
async def summary(ctx: ExecutionContext, table: str = "data") -> Report:  # noqa: ARG001
    """Generate summary statistics for a table.

    Args:
        ctx: Execution context.
        table: Name of the table to analyze.

    Returns:
        Report with summary statistics.

    Example:
        $ analytics summary --table sales
        Summary: sales
        ┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
        ┃ Metric       ┃ Value       ┃
        ...
    """
    db = get_db()

    # Get numeric columns for stats
    cols = db.fetchall(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = ? AND data_type IN ('INTEGER', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL')
        """,
        [table],
    )

    # Get basic stats
    row_count_result = db.fetchone(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
    row_count = row_count_result[0] if row_count_result else 0

    data: list[dict[str, str | int | float]] = [{"metric": "Total Rows", "value": row_count}]

    # Add stats for each numeric column
    for col_name, _col_type in cols:
        stat_query = (
            f"SELECT MIN({col_name}), MAX({col_name}), "  # noqa: S608
            f"AVG({col_name}), SUM({col_name}) FROM {table}"
        )
        stats = db.fetchone(stat_query)
        if stats:
            data.extend(
                [
                    {"metric": f"{col_name} (min)", "value": stats[0] or 0},
                    {"metric": f"{col_name} (max)", "value": stats[1] or 0},
                    {"metric": f"{col_name} (avg)", "value": round(stats[2] or 0, 2)},
                    {"metric": f"{col_name} (sum)", "value": stats[3] or 0},
                ]
            )

    return Report(
        title=f"Summary: {table}",
        generated_at=datetime.now(),
        row_count=len(data),
        columns=["metric", "value"],
        data=data,
    )


@command(app)
@requires(lambda _ctx, table, **_kw: len(table.strip()) > 0, "Table name required")
@requires(lambda _ctx, _table, limit=10, **_kw: limit > 0, "Limit must be positive")
async def top_values(
    ctx: ExecutionContext,  # noqa: ARG001
    table: str,
    column: str,
    limit: int = 10,
) -> Report:
    """Get top values by a column.

    Args:
        ctx: Execution context.
        table: Table to query.
        column: Column to sort by (descending).
        limit: Number of results.

    Returns:
        Report with top values.

    Example:
        $ analytics top-values --table sales --column amount --limit 5
    """
    db = get_db()

    # Get all columns for the result
    cols = db.fetchall(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
        [table],
    )
    col_names = [c[0] for c in cols]

    # Query top values
    rows = db.fetchall(
        f"SELECT * FROM {table} ORDER BY {column} DESC LIMIT ?",  # noqa: S608
        [limit],
    )

    data = [dict(zip(col_names, row, strict=True)) for row in rows]

    return Report(
        title=f"Top {limit} by {column}",
        generated_at=datetime.now(),
        row_count=len(data),
        columns=col_names,
        data=data,
    )


@command(app)
@requires(lambda _ctx, table, **_kw: len(table.strip()) > 0, "Table name required")
async def group_by(
    ctx: ExecutionContext,  # noqa: ARG001
    table: str,
    group_column: str,
    agg_column: str,
    agg_func: Literal["sum", "avg", "count", "min", "max"] = "sum",
) -> Report:
    """Group data by a column and aggregate.

    Args:
        ctx: Execution context.
        table: Table to query.
        group_column: Column to group by.
        agg_column: Column to aggregate.
        agg_func: Aggregation function.

    Returns:
        Report with grouped results.

    Example:
        $ analytics group-by --table sales --group-column category
    """
    db = get_db()

    query = f"""
        SELECT {group_column}, {agg_func.upper()}({agg_column}) as {agg_func}_{agg_column}
        FROM {table}
        GROUP BY {group_column}
        ORDER BY {agg_func}_{agg_column} DESC
    """  # noqa: S608

    rows = db.fetchall(query)
    col_names = [group_column, f"{agg_func}_{agg_column}"]
    data = [dict(zip(col_names, row, strict=True)) for row in rows]

    return Report(
        title=f"{agg_func.upper()}({agg_column}) by {group_column}",
        generated_at=datetime.now(),
        row_count=len(data),
        columns=col_names,
        data=data,
    )
