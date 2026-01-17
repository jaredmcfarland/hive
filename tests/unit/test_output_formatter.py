"""Unit tests for OutputFormatter (T044, T045)."""

import json
from io import StringIO
from unittest.mock import patch


class TestOutputFormatterJSON:
    """Tests for OutputFormatter JSON mode (T044)."""

    def test_result_outputs_json(self) -> None:
        """result() outputs JSON when in JSON mode."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class TaskResult(BaseModel):
            id: int
            title: str

        formatter = OutputFormatter(format=OutputFormat.JSON)
        result = TaskResult(id=1, title="Test Task")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(result)
            output = mock_stdout.getvalue()

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["id"] == 1
        assert parsed["title"] == "Test Task"

    def test_info_suppressed_in_json_mode(self) -> None:
        """info() is suppressed in JSON mode."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.JSON)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.info("This should not appear")
            output = mock_stdout.getvalue()

        assert output == ""

    def test_warning_appears_in_json_mode(self) -> None:
        """warning() still appears in JSON mode (to stderr)."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.JSON)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            formatter.warning("Warning message")
            output = mock_stderr.getvalue()

        assert "Warning message" in output

    def test_json_list_output(self) -> None:
        """Lists are output as JSON arrays."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Item(BaseModel):
            name: str

        formatter = OutputFormatter(format=OutputFormat.JSON)
        items = [Item(name="a"), Item(name="b"), Item(name="c")]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(items)
            output = mock_stdout.getvalue()

        parsed = json.loads(output)
        assert len(parsed) == 3
        assert parsed[0]["name"] == "a"


class TestOutputFormatterTable:
    """Tests for OutputFormatter table mode (T045)."""

    def test_result_outputs_table(self) -> None:
        """result() outputs formatted table in TABLE mode."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Task(BaseModel):
            id: int
            title: str
            status: str

        formatter = OutputFormatter(format=OutputFormat.TABLE)
        result = Task(id=1, title="Test Task", status="pending")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(result)
            output = mock_stdout.getvalue()

        # Should contain the field values (Rich table output)
        assert "Test Task" in output or "id" in output.lower()

    def test_table_with_list(self) -> None:
        """table() method outputs items as a table."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Task(BaseModel):
            id: int
            title: str

        formatter = OutputFormatter(format=OutputFormat.TABLE)
        items = [
            Task(id=1, title="First"),
            Task(id=2, title="Second"),
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.table(items, columns=["id", "title"])
            output = mock_stdout.getvalue()

        # Should contain data
        assert "First" in output or "id" in output.lower()

    def test_info_appears_in_table_mode(self) -> None:
        """info() messages appear in TABLE mode."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.TABLE)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.info("Information message")
            output = mock_stdout.getvalue()

        assert "Information" in output or "message" in output.lower()

    def test_error_output(self) -> None:
        """error() outputs to stderr with formatting."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.TABLE)

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            formatter.error("Error message")
            output = mock_stderr.getvalue()

        assert "Error" in output or "message" in output.lower()
