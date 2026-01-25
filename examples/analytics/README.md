# Analytics Example

This example demonstrates Hive's capabilities for building data analytics
CLI applications using DuckDB as the backend.

## Features

- **DuckDB integration** - Fast analytical database for local data processing
- **Rich output** - Beautiful tables and charts in the terminal
- **Data import** - Load CSV/JSON data files
- **Aggregation queries** - SQL-powered analytics through Hive queries

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize the database
analytics init

# Import sample data
analytics data import sales.csv --table sales

# Run analytics queries
analytics report summary --table sales
analytics report top-products --limit 10

# Export results
analytics report summary --table sales --format json > results.json
```

## Project Structure

```
examples/analytics/
├── pyproject.toml           # Project configuration
├── README.md                # This file
├── src/analytics/
│   ├── __init__.py         # App definition and CLI export
│   ├── app.py              # Hive App instance
│   ├── entities.py         # DataPoint, Report entities
│   ├── commands.py         # Import and query commands
│   ├── database.py         # DuckDB configuration
│   └── formatters.py       # Rich output formatting
└── tests/
    ├── __init__.py
    └── test_commands.py    # Analytics tests
```

## Data Models

### DataPoint Entity

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DataPoint:
    \"\"\"A single data point for analytics.\"\"\"
    id: int
    timestamp: datetime
    category: str
    value: float
    metadata: dict | None = None
```

### Report Entity

```python
@dataclass
class Report:
    \"\"\"Analytics report with aggregated results.\"\"\"
    title: str
    generated_at: datetime
    row_count: int
    columns: list[str]
    data: list[dict]
    summary: dict | None = None
```

## Commands

### Data Import

```python
from hive.core.decorators import command
from analytics.app import app

@command(app)
async def import_data(
    ctx,
    file_path: str,
    table: str = "data",
    format: str = "csv",
) -> int:
    \"\"\"Import data from CSV or JSON file.

    Returns the number of rows imported.
    \"\"\"
    conn = ctx.db.connection
    if format == "csv":
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM '{file_path}'")
    row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return row_count
```

### Analytics Queries

```python
@command(app)
async def summary(ctx, table: str = "data") -> Report:
    \"\"\"Generate summary statistics for a table.\"\"\"
    conn = ctx.db.connection

    # Get basic stats
    stats = conn.execute(f\"\"\"
        SELECT
            COUNT(*) as row_count,
            COUNT(DISTINCT category) as categories,
            SUM(value) as total_value,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value
        FROM {table}
    \"\"\").fetchone()

    return Report(
        title=f"Summary: {table}",
        generated_at=datetime.now(),
        row_count=stats[0],
        columns=["metric", "value"],
        data=[
            {"metric": "Total Rows", "value": stats[0]},
            {"metric": "Categories", "value": stats[1]},
            {"metric": "Total Value", "value": f"${stats[2]:,.2f}"},
            {"metric": "Average Value", "value": f"${stats[3]:,.2f}"},
            {"metric": "Min Value", "value": f"${stats[4]:,.2f}"},
            {"metric": "Max Value", "value": f"${stats[5]:,.2f}"},
        ],
    )
```

## Rich Output

Reports are displayed with Rich tables:

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Metric        ┃ Value        ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Total Rows    │ 1,234        │
│ Categories    │ 5            │
│ Total Value   │ $45,678.90   │
│ Average Value │ $37.01       │
│ Min Value     │ $0.99        │
│ Max Value     │ $999.99      │
└───────────────┴──────────────┘
```

## DuckDB Features Used

- **CSV/JSON import** - Direct file reading with schema inference
- **Aggregations** - SUM, AVG, COUNT, MIN, MAX
- **Window functions** - Ranking and partitioning
- **CTEs** - Common table expressions for complex queries
- **In-memory mode** - Fast ephemeral databases for testing

## Testing

```python
import duckdb
from hive.testing import TestClient

async def test_import_and_query():
    # Create in-memory DuckDB for testing
    conn = duckdb.connect(":memory:")

    async with TestClient(app) as client:
        # Import test data
        count = await client.invoke("import_data",
            file_path="tests/fixtures/sample.csv",
            table="sales"
        )
        assert count > 0

        # Run summary
        report = await client.invoke("summary", table="sales")
        assert report.row_count == count
```

## API Reference

### Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize DuckDB database |
| `data import FILE` | Import CSV/JSON data |
| `data list` | List available tables |
| `report summary` | Generate summary statistics |
| `report top-products` | Show top products by value |
| `report by-category` | Breakdown by category |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--db PATH` | Database file path | `:memory:` |
| `--format FORMAT` | Output format (table/json/csv) | `table` |
| `--limit N` | Limit results | 100 |

## Learn More

- [Hive Framework Documentation](https://github.com/jaredmcfarland/hive)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Rich Documentation](https://rich.readthedocs.io/)
