"""Tests for Analytics commands.

Demonstrates testing with in-memory DuckDB databases.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from analytics.commands import group_by, import_data, list_tables, summary, top_values
from analytics.database import DuckDBConnection, temp_db
from analytics.entities import DataPoint, Report, TableInfo
from analytics.formatters import _format_value, format_summary


class TestEntities:
    """Tests for data entities."""

    def test_datapoint_creation(self) -> None:
        """DataPoint can be created with required fields."""
        dp = DataPoint(
            id=1,
            timestamp=datetime.now(),
            category="test",
            value=42.5,
        )
        assert dp.id == 1
        assert dp.category == "test"
        assert dp.value == 42.5
        assert dp.metadata is None

    def test_datapoint_with_metadata(self) -> None:
        """DataPoint accepts optional metadata."""
        dp = DataPoint(
            id=1,
            timestamp=datetime.now(),
            category="test",
            value=42.5,
            metadata={"source": "api"},
        )
        assert dp.metadata == {"source": "api"}

    def test_report_creation(self) -> None:
        """Report can be created with required fields."""
        report = Report(
            title="Test Report",
            generated_at=datetime.now(),
            row_count=5,
            columns=["a", "b"],
            data=[{"a": 1, "b": 2}],
        )
        assert report.title == "Test Report"
        assert report.row_count == 5
        assert len(report.columns) == 2

    def test_tableinfo_creation(self) -> None:
        """TableInfo can be created."""
        info = TableInfo(
            name="test_table",
            row_count=100,
            columns=["id", "name", "value"],
        )
        assert info.name == "test_table"
        assert info.row_count == 100
        assert len(info.columns) == 3


class TestDatabase:
    """Tests for DuckDB connection."""

    def test_temp_db_context_manager(self) -> None:
        """temp_db creates and cleans up connection."""
        with temp_db() as db:
            assert db.connection is not None
            db.execute("CREATE TABLE test (id INTEGER)")
            assert db.table_exists("test")

    def test_execute_and_fetch(self) -> None:
        """Execute and fetchall work correctly."""
        with temp_db() as db:
            db.execute("CREATE TABLE nums (n INTEGER)")
            db.execute("INSERT INTO nums VALUES (1), (2), (3)")

            rows = db.fetchall("SELECT n FROM nums ORDER BY n")
            assert rows == [(1,), (2,), (3,)]

    def test_fetchone(self) -> None:
        """Fetchone returns single row."""
        with temp_db() as db:
            db.execute("CREATE TABLE nums (n INTEGER)")
            db.execute("INSERT INTO nums VALUES (42)")

            row = db.fetchone("SELECT n FROM nums")
            assert row == (42,)

    def test_table_exists(self) -> None:
        """table_exists correctly detects tables."""
        with temp_db() as db:
            assert not db.table_exists("nonexistent")

            db.execute("CREATE TABLE exists_test (id INTEGER)")
            assert db.table_exists("exists_test")

    def test_get_tables(self) -> None:
        """get_tables returns all tables."""
        with temp_db() as db:
            db.execute("CREATE TABLE table_a (id INTEGER)")
            db.execute("CREATE TABLE table_b (id INTEGER)")

            tables = db.get_tables()
            assert "table_a" in tables
            assert "table_b" in tables


class TestFormatters:
    """Tests for output formatters."""

    def test_format_value_none(self) -> None:
        """_format_value handles None."""
        assert _format_value(None) == "-"

    def test_format_value_int(self) -> None:
        """_format_value formats integers with commas."""
        assert _format_value(1000) == "1,000"
        assert _format_value(1000000) == "1,000,000"

    def test_format_value_float_large(self) -> None:
        """_format_value formats large floats with commas."""
        assert _format_value(1234.56) == "1,234.56"

    def test_format_value_float_small(self) -> None:
        """_format_value formats small floats with precision."""
        assert _format_value(0.1234) == "0.1234"

    def test_format_value_string(self) -> None:
        """_format_value converts strings."""
        assert _format_value("test") == "test"

    def test_format_summary(self) -> None:
        """format_summary creates Rich table."""
        data: dict[str, Any] = {"Count": 100, "Average": 42.5}
        table = format_summary(data, title="Test")

        assert table.title == "Test"


class TestCommands:
    """Tests for analytics commands."""

    @pytest.fixture
    def mock_db(self) -> DuckDBConnection:
        """Create a mock database with test data."""
        db = DuckDBConnection(":memory:")

        # Create test table
        db.execute("""
            CREATE TABLE sales (
                id INTEGER,
                category VARCHAR,
                amount DOUBLE,
                quantity INTEGER
            )
        """)

        # Insert test data
        db.execute("""
            INSERT INTO sales VALUES
            (1, 'electronics', 999.99, 1),
            (2, 'electronics', 499.99, 2),
            (3, 'clothing', 29.99, 5),
            (4, 'clothing', 49.99, 3),
            (5, 'food', 9.99, 10)
        """)

        return db

    @pytest.mark.asyncio
    async def test_list_tables(self, mock_db: DuckDBConnection) -> None:
        """list_tables returns table information."""
        with patch("analytics.commands.get_db", return_value=mock_db):
            tables = await list_tables(MagicMock())

        assert len(tables) == 1
        assert tables[0].name == "sales"
        assert tables[0].row_count == 5

    @pytest.mark.asyncio
    async def test_summary(self, mock_db: DuckDBConnection) -> None:
        """Summary generates statistics report."""
        with patch("analytics.commands.get_db", return_value=mock_db):
            report = await summary(MagicMock(), table="sales")

        assert report.title == "Summary: sales"
        assert report.row_count > 0

        # Find total rows metric
        total_rows = next((d for d in report.data if d["metric"] == "Total Rows"), None)
        assert total_rows is not None
        assert total_rows["value"] == 5

    @pytest.mark.asyncio
    async def test_top_values(self, mock_db: DuckDBConnection) -> None:
        """top_values returns highest values."""
        with patch("analytics.commands.get_db", return_value=mock_db):
            report = await top_values(MagicMock(), table="sales", column="amount", limit=2)

        assert report.row_count == 2
        # First should be highest amount
        assert report.data[0]["amount"] == 999.99

    @pytest.mark.asyncio
    async def test_group_by(self, mock_db: DuckDBConnection) -> None:
        """group_by aggregates by column."""
        with patch("analytics.commands.get_db", return_value=mock_db):
            report = await group_by(
                MagicMock(),
                table="sales",
                group_column="category",
                agg_column="amount",
                agg_func="sum",
            )

        assert report.row_count == 3  # 3 categories

        # Electronics should have highest sum
        electronics = next((d for d in report.data if d["category"] == "electronics"), None)
        assert electronics is not None
        assert electronics["sum_amount"] == pytest.approx(1499.98, rel=1e-2)

    @pytest.mark.asyncio
    async def test_import_data_csv(self, tmp_path: Path) -> None:
        """import_data loads CSV file."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name,value\n1,a,10\n2,b,20\n3,c,30\n")

        with temp_db() as db, patch("analytics.commands.get_db", return_value=db):
            count = await import_data(
                MagicMock(),
                file_path=str(csv_file),
                table="test",
                file_format="csv",
            )

        assert count == 3
