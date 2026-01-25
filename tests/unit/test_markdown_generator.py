"""Unit tests for MarkdownGenerator.

Tests that the MarkdownGenerator correctly generates markdown documentation
from Hive application specifications.
"""

from pathlib import Path
import tempfile


class TestMarkdownGenerator:
    """Unit tests for MarkdownGenerator class."""

    def test_generator_initialization(self) -> None:
        """MarkdownGenerator initializes with app and creates jinja env."""
        from hive.app import App
        from hive.docs import MarkdownGenerator

        app = App("test-app")
        generator = MarkdownGenerator(app)

        assert generator.app is app
        assert generator.env is not None

    def test_generate_returns_documentation_output(self) -> None:
        """generate() returns DocumentationOutput with correct structure."""
        from hive.app import App
        from hive.docs import DocumentationConfig, MarkdownGenerator

        app = App("test-app")
        generator = MarkdownGenerator(app)
        config = DocumentationConfig(format="markdown")

        result = generator.generate(config)

        assert result.commands_documented == 0
        assert result.queries_documented == 0
        assert result.entities_documented == 0
        assert result.content is not None
        assert isinstance(result.content, str)

    def test_generate_documents_commands(self) -> None:
        """generate() includes registered commands in output."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.docs import DocumentationConfig, MarkdownGenerator
        from hive.runtime.context import ExecutionContext

        app = App("test-app")

        @command(app)
        async def hello(ctx: ExecutionContext, name: str) -> str:
            """Say hello to someone."""
            return f"Hello, {name}!"

        generator = MarkdownGenerator(app)
        config = DocumentationConfig(format="markdown")

        result = generator.generate(config)

        assert result.commands_documented == 1
        assert result.content is not None
        assert "hello" in result.content.lower()

    def test_generate_documents_entities(self) -> None:
        """generate() includes registered entities in output."""
        from sqlmodel import Field, SQLModel

        from hive.app import App
        from hive.core.decorators import entity
        from hive.docs import DocumentationConfig, MarkdownGenerator

        app = App("test-app")

        @entity(app)
        class User(SQLModel, table=True):
            """A user in the system."""

            __tablename__ = "users"

            id: int | None = Field(default=None, primary_key=True)
            name: str
            email: str

        generator = MarkdownGenerator(app)
        config = DocumentationConfig(format="markdown")

        result = generator.generate(config)

        assert result.entities_documented == 1
        assert result.content is not None
        assert "user" in result.content.lower()

    def test_generate_outputs_to_directory(self) -> None:
        """generate() creates files when output_dir is specified."""
        from hive.app import App
        from hive.docs import DocumentationConfig, MarkdownGenerator

        app = App("test-app")
        generator = MarkdownGenerator(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = DocumentationConfig(
                format="markdown",
                output_dir=Path(tmpdir),
            )

            result = generator.generate(config)

            assert len(result.files_generated) > 0
            # Check index.md was created
            index_path = Path(tmpdir) / "index.md"
            assert index_path.exists()

    def test_filter_private_commands(self) -> None:
        """Private commands (underscore-prefixed) are filtered by default."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.docs import DocumentationConfig, MarkdownGenerator
        from hive.runtime.context import ExecutionContext

        app = App("test-app")

        @command(app)
        async def public_cmd(ctx: ExecutionContext) -> None:
            """Public command."""

        @command(app)
        async def _private_cmd(ctx: ExecutionContext) -> None:
            """Private command."""

        generator = MarkdownGenerator(app)

        # Without include_private
        config = DocumentationConfig(format="markdown", include_private=False)
        result = generator.generate(config)
        assert result.commands_documented == 1

        # With include_private
        config_private = DocumentationConfig(format="markdown", include_private=True)
        result_private = generator.generate(config_private)
        assert result_private.commands_documented == 2


class TestDocumentationConfig:
    """Unit tests for DocumentationConfig model."""

    def test_default_config(self) -> None:
        """Default config has markdown format and stdout output."""
        from hive.docs import DocumentationConfig

        config = DocumentationConfig()

        assert config.format == "markdown"
        assert config.output_dir is None
        assert config.include_private is False
        assert config.include_examples is True
        assert config.include_contracts is True

    def test_config_with_output_dir(self) -> None:
        """Config with output_dir is immutable."""
        from hive.docs import DocumentationConfig

        config = DocumentationConfig(
            format="markdown",
            output_dir=Path("/tmp/docs"),
        )

        assert config.output_dir == Path("/tmp/docs")


class TestDocumentationOutput:
    """Unit tests for DocumentationOutput model."""

    def test_total_documented(self) -> None:
        """total_documented property sums all documented items."""
        from hive.docs.models import DocumentationOutput

        output = DocumentationOutput(
            commands_documented=5,
            queries_documented=3,
            entities_documented=2,
        )

        assert output.total_documented == 10

    def test_has_warnings(self) -> None:
        """has_warnings property checks warnings list."""
        from hive.docs.models import DocumentationOutput

        output_no_warnings = DocumentationOutput()
        assert output_no_warnings.has_warnings is False

        output_with_warnings = DocumentationOutput(
            warnings=["Missing docstring for command 'foo'"],
        )
        assert output_with_warnings.has_warnings is True


class TestJinjaFilters:
    """Unit tests for Jinja2 filters."""

    def test_format_type(self) -> None:
        """format_type converts JSON Schema types."""
        from hive.docs.filters import format_type

        assert format_type("string") == "string"
        assert format_type("integer") == "integer"
        assert format_type("array") == "list"

    def test_format_constraints(self) -> None:
        """format_constraints formats constraint info."""
        from hive.docs.filters import format_constraints

        # Numeric constraints
        param = {"minimum": 1, "maximum": 100}
        result = format_constraints(param)
        assert "1" in result
        assert "100" in result

        # Length constraints
        param = {"minLength": 1}
        result = format_constraints(param)
        assert "length" in result

    def test_format_default(self) -> None:
        """format_default handles various types."""
        from hive.docs.filters import format_default

        assert format_default(None) == "None"
        assert format_default("hello") == '"hello"'
        assert format_default(42) == "42"
        assert format_default(True) == "True"

    def test_first_line(self) -> None:
        """first_line extracts first line of text."""
        from hive.docs.filters import first_line

        assert first_line("First line.\nSecond line.") == "First line."
        assert first_line("Single line") == "Single line"
        assert first_line(None) == ""
        assert first_line("") == ""

    def test_troff_escape(self) -> None:
        """troff_escape escapes special characters."""
        from hive.docs.filters import troff_escape

        result = troff_escape("use --help")
        assert "\\-" in result
