"""Unit tests for OutputFormatter (T044, T045)."""

from io import StringIO
import json
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

    def test_table_with_dict_items(self) -> None:
        """table() method handles dict items."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.TABLE)
        items = [
            {"id": 1, "title": "First"},
            {"id": 2, "title": "Second"},
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.table(items)
            output = mock_stdout.getvalue()

        assert "First" in output or "1" in output

    def test_table_empty_items(self) -> None:
        """table() handles empty item list."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.TABLE)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.table([])
            output = mock_stdout.getvalue()

        # Should print info message about no items
        assert "No items" in output or output == ""

    def test_table_json_mode_outputs_json(self) -> None:
        """table() outputs JSON when in JSON mode."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Task(BaseModel):
            id: int
            title: str

        formatter = OutputFormatter(format=OutputFormat.JSON)
        items = [Task(id=1, title="Test")]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.table(items)
            output = mock_stdout.getvalue()

        parsed = json.loads(output)
        assert parsed[0]["id"] == 1

    def test_result_dict_output(self) -> None:
        """result() handles dict data."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.TABLE)
        data = {"key": "value", "count": 42}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(data)
            output = mock_stdout.getvalue()

        assert "key" in output.lower() or "value" in output

    def test_result_list_output(self) -> None:
        """result() handles list data."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Item(BaseModel):
            name: str

        formatter = OutputFormatter(format=OutputFormat.TABLE)
        items = [Item(name="test")]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(items)
            output = mock_stdout.getvalue()

        assert "test" in output.lower() or "name" in output.lower()


class TestOutputFormatterCSV:
    """Tests for OutputFormatter CSV mode."""

    def test_csv_output_basemodel(self) -> None:
        """CSV output for BaseModel data."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Task(BaseModel):
            id: int
            title: str

        formatter = OutputFormatter(format=OutputFormat.CSV)
        data = Task(id=1, title="Test")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(data)
            output = mock_stdout.getvalue()

        assert "id,title" in output or "id" in output
        assert "Test" in output

    def test_csv_output_list(self) -> None:
        """CSV output for list of BaseModels."""
        from pydantic import BaseModel

        from hive.runtime.output import OutputFormat, OutputFormatter

        class Item(BaseModel):
            name: str
            count: int

        formatter = OutputFormatter(format=OutputFormat.CSV)
        items = [Item(name="a", count=1), Item(name="b", count=2)]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(items)
            output = mock_stdout.getvalue()

        assert "name" in output
        assert "a" in output
        assert "b" in output

    def test_csv_output_dict_list(self) -> None:
        """CSV output for list of dicts."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.CSV)
        items = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result(items)
            output = mock_stdout.getvalue()

        assert "x,y" in output or "x" in output

    def test_csv_output_empty(self) -> None:
        """CSV output for empty list."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.CSV)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.result([])
            output = mock_stdout.getvalue()

        # Empty list should produce no output
        assert output == ""


class TestOutputFormatterQuiet:
    """Tests for OutputFormatter quiet mode."""

    def test_info_suppressed_in_quiet_mode(self) -> None:
        """info() is suppressed when quiet=True."""
        from hive.runtime.output import OutputFormat, OutputFormatter

        formatter = OutputFormatter(format=OutputFormat.TABLE, quiet=True)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            formatter.info("This should not appear")
            output = mock_stdout.getvalue()

        assert output == ""
