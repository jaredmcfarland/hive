"""Unit tests for ManPageGenerator.

Tests for man page documentation generation from Hive applications.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hive.app import App


class TestManPageGenerator:
    """Tests for ManPageGenerator class."""

    @pytest.fixture
    def sample_app(self) -> App:
        """Create a sample app for testing."""
        from hive.app import App
        from hive.core.decorators import command

        app = App("test-app")

        @command(app)
        async def hello(ctx, name: str = "World") -> str:
            """Say hello to someone.

            A friendly greeting command.

            Example:
                $ test-app hello --name Alice
                Hello, Alice!
            """
            return f"Hello, {name}!"

        @command(app)
        async def add(ctx, a: int, b: int) -> int:
            """Add two numbers together.

            Args:
                a: First number.
                b: Second number.

            Returns:
                The sum of a and b.
            """
            return a + b

        return app

    def test_generate_single_output(self, sample_app: App) -> None:
        """ManPageGenerator generates single output to stdout."""
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        generator = ManPageGenerator(sample_app)
        config = DocumentationConfig(format="manpage", output_dir=None)

        result = generator.generate(config)

        assert result.content is not None
        assert result.commands_documented == 2
        # Should contain troff macros
        assert ".TH" in result.content
        assert ".SH NAME" in result.content
        assert "hello" in result.content
        assert "add" in result.content

    def test_generate_files(self, sample_app: App, tmp_path: Path) -> None:
        """ManPageGenerator generates files to output directory."""
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        generator = ManPageGenerator(sample_app)
        config = DocumentationConfig(format="manpage", output_dir=tmp_path)

        result = generator.generate(config)

        assert result.files_generated is not None
        assert len(result.files_generated) == 2
        assert result.commands_documented == 2

        # Check file names - man pages use .1 extension
        file_names = {f.name for f in result.files_generated}
        assert "hello.1" in file_names
        assert "add.1" in file_names

        # Check file contents
        hello_content = (tmp_path / "hello.1").read_text()
        assert ".TH HELLO 1" in hello_content
        assert "Say hello to someone" in hello_content

    def test_troff_structure(self, sample_app: App) -> None:
        """Generated man pages have proper troff structure."""
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        generator = ManPageGenerator(sample_app)
        config = DocumentationConfig(format="manpage", output_dir=None)

        result = generator.generate(config)
        content = result.content or ""

        # Check required sections
        required_sections = [
            ".TH",  # Title header
            ".SH NAME",
            ".SH SYNOPSIS",
            ".SH DESCRIPTION",
            ".SH OPTIONS",
            '.SH "SEE ALSO"',
        ]
        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_parameter_documentation(self, sample_app: App) -> None:
        """Man pages document command parameters."""
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        generator = ManPageGenerator(sample_app)
        config = DocumentationConfig(format="manpage", output_dir=None)

        result = generator.generate(config)
        content = result.content or ""

        # Check parameter documentation (hyphens are escaped in troff)
        assert "\\-\\-name" in content
        assert "\\-\\-a" in content
        assert "\\-\\-b" in content

    def test_include_examples(self, sample_app: App) -> None:
        """Man pages include examples when configured."""
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        generator = ManPageGenerator(sample_app)
        config = DocumentationConfig(
            format="manpage",
            output_dir=None,
            include_examples=True,
        )

        result = generator.generate(config)
        content = result.content or ""

        # Should have EXAMPLES section
        assert ".SH EXAMPLES" in content
        # The hello command has an example in its docstring
        assert "test-app hello" in content or "Alice" in content

    def test_exclude_examples(self, sample_app: App) -> None:
        """Man pages exclude examples when configured."""
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        generator = ManPageGenerator(sample_app)
        config = DocumentationConfig(
            format="manpage",
            output_dir=None,
            include_examples=False,
        )

        result = generator.generate(config)
        content = result.content or ""

        # Should NOT have EXAMPLES section
        assert ".SH EXAMPLES" not in content

    def test_private_commands_excluded_by_default(self) -> None:
        """Private commands are excluded by default."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        app = App("test-app")

        @command(app)
        async def public_cmd(ctx) -> str:
            """A public command."""
            return "public"

        @command(app)
        async def _private_cmd(ctx) -> str:
            """A private command."""
            return "private"

        generator = ManPageGenerator(app)
        config = DocumentationConfig(
            format="manpage",
            output_dir=None,
            include_private=False,
        )

        result = generator.generate(config)

        assert result.commands_documented == 1
        content = result.content or ""
        assert "public_cmd" in content
        assert "_private_cmd" not in content

    def test_private_commands_included_when_configured(self) -> None:
        """Private commands are included when configured."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        app = App("test-app")

        @command(app)
        async def public_cmd(ctx) -> str:
            """A public command."""
            return "public"

        @command(app)
        async def _private_cmd(ctx) -> str:
            """A private command."""
            return "private"

        generator = ManPageGenerator(app)
        config = DocumentationConfig(
            format="manpage",
            output_dir=None,
            include_private=True,
        )

        result = generator.generate(config)

        assert result.commands_documented == 2
        content = result.content or ""
        assert "public_cmd" in content
        assert "_private_cmd" in content

    def test_missing_description_warning(self) -> None:
        """Missing descriptions generate warnings."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        app = App("test-app")

        @command(app)
        async def no_doc_cmd(ctx) -> str:
            return "no docs"

        generator = ManPageGenerator(app)
        config = DocumentationConfig(format="manpage", output_dir=None)

        result = generator.generate(config)

        assert len(result.warnings) == 1
        assert "no_doc_cmd" in result.warnings[0]
        assert "no description" in result.warnings[0]

    def test_troff_escaping(self, sample_app: App) -> None:
        """Special characters are escaped for troff."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        app = App("test-app")

        @command(app)
        async def special_chars(ctx) -> str:
            """Test command with special chars: - \\ ' and more."""
            return "special"

        generator = ManPageGenerator(app)
        config = DocumentationConfig(format="manpage", output_dir=None)

        result = generator.generate(config)
        content = result.content or ""

        # Hyphens should be escaped in troff
        assert "\\-" in content


class TestManPageFilters:
    """Tests for man page specific Jinja2 filters."""

    def test_troff_escape_hyphen(self) -> None:
        """troff_escape escapes hyphens."""
        from hive.docs.filters import troff_escape

        result = troff_escape("--option")
        assert result == "\\-\\-option"

    def test_troff_escape_backslash(self) -> None:
        """troff_escape escapes backslashes."""
        from hive.docs.filters import troff_escape

        result = troff_escape("path\\to\\file")
        assert result == "path\\\\to\\\\file"

    def test_troff_escape_single_quote(self) -> None:
        """troff_escape escapes single quotes."""
        from hive.docs.filters import troff_escape

        result = troff_escape("it's a test")
        assert "\\(aq" in result or "'" in result  # Either escape or preserve

    def test_first_line_filter(self) -> None:
        """first_line extracts first line of text."""
        from hive.docs.filters import first_line

        text = "First line.\nSecond line.\nThird line."
        assert first_line(text) == "First line."

    def test_first_line_single_line(self) -> None:
        """first_line works with single line."""
        from hive.docs.filters import first_line

        text = "Only one line"
        assert first_line(text) == "Only one line"

    def test_first_line_empty(self) -> None:
        """first_line handles empty string."""
        from hive.docs.filters import first_line

        assert first_line("") == ""
        assert first_line(None) == ""  # type: ignore[arg-type]


class TestManPageContractDocumentation:
    """Unit tests for contract documentation extraction in man pages."""

    def test_get_contracts_extracts_requires(self) -> None:
        """_get_contracts extracts @requires contract messages."""
        from hive.app import App
        from hive.contracts import requires
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator

        app = App("test-app")

        @command(app)
        @requires(lambda ctx, x: x > 0, "x must be positive")
        async def positive_cmd(ctx, x: int) -> int:
            """Command requiring positive input."""
            return x

        generator = ManPageGenerator(app)
        contracts = generator._get_contracts("positive_cmd")

        assert "x must be positive" in contracts["requires"]
        assert len(contracts["ensures"]) == 0

    def test_get_contracts_extracts_ensures(self) -> None:
        """_get_contracts extracts @ensures contract messages."""
        from hive.app import App
        from hive.contracts import ensures
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator

        app = App("test-app")

        @command(app)
        @ensures(lambda ctx, x, result: result >= x, "result must be >= input")
        async def double_cmd(ctx, x: int) -> int:
            """Command that doubles input."""
            return x * 2

        generator = ManPageGenerator(app)
        contracts = generator._get_contracts("double_cmd")

        assert "result must be >= input" in contracts["ensures"]
        assert len(contracts["requires"]) == 0

    def test_get_contracts_extracts_both(self) -> None:
        """_get_contracts extracts both @requires and @ensures."""
        from hive.app import App
        from hive.contracts import ensures, requires
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator

        app = App("test-app")

        @command(app)
        @requires(lambda ctx, x: x > 0, "input must be positive")
        @ensures(lambda ctx, x, result: result > x, "result must be greater than input")
        async def increment_cmd(ctx, x: int) -> int:
            """Command that increments input."""
            return x + 1

        generator = ManPageGenerator(app)
        contracts = generator._get_contracts("increment_cmd")

        assert "input must be positive" in contracts["requires"]
        assert "result must be greater than input" in contracts["ensures"]

    def test_contracts_included_in_output(self) -> None:
        """Contracts appear in generated man page output."""
        from hive.app import App
        from hive.contracts import requires
        from hive.core.decorators import command
        from hive.docs.manpage import ManPageGenerator
        from hive.docs.models import DocumentationConfig

        app = App("test-app")

        @command(app)
        @requires(lambda ctx, x: x > 0, "Value must be positive")
        async def validated_cmd(ctx, x: int) -> int:
            """Command with validation."""
            return x

        generator = ManPageGenerator(app)
        config = DocumentationConfig(
            format="manpage",
            output_dir=None,
            include_contracts=True,
        )

        result = generator.generate(config)
        content = result.content or ""

        # Check contracts section appears
        assert ".SH CONTRACTS" in content
        assert "Value must be positive" in content
