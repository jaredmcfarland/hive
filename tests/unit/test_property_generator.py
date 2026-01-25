"""Unit tests for PropertyGenerator.

Tests for property-based test generation from Hive application types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hive.app import App


class TestPropertyGenerator:
    """Tests for PropertyGenerator class."""

    @pytest.fixture
    def app_with_types(self) -> App:
        """Create a sample app with typed parameters for testing."""
        from hive.app import App
        from hive.core.decorators import command, query
        from hive.types import NonEmptyStr, PositiveInt

        app = App("test-app")

        @command(app)
        async def set_priority(ctx, task_id: PositiveInt, name: NonEmptyStr) -> dict:
            """Set priority for a task."""
            return {"task_id": task_id, "name": name}

        @query(app)
        async def get_items(ctx, limit: PositiveInt = 10) -> list:
            """Get items with limit."""
            return []

        @command(app)
        async def basic_types(ctx, count: int, name: str) -> dict:
            """Command with basic types."""
            return {"count": count, "name": name}

        return app

    @pytest.fixture
    def app_without_types(self) -> App:
        """Create a sample app without typed parameters."""
        from hive.app import App
        from hive.core.decorators import command

        app = App("no-types-app")

        @command(app)
        async def simple_command(ctx) -> str:
            """A simple command without typed params."""
            return "done"

        return app

    def test_generate_extracts_refinement_types(self, app_with_types: App) -> None:
        """PropertyGenerator extracts refinement type parameters."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types)
        result = generator.generate()

        # Should have test cases for commands with typed params
        assert len(result.test_cases) >= 2

    def test_generate_creates_code(self, app_with_types: App) -> None:
        """PropertyGenerator generates valid Python code."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types)
        result = generator.generate()

        assert result.code is not None
        assert len(result.code) > 0

        # Code should be valid Python
        compile(result.code, "<string>", "exec")

    def test_generate_empty_types_warning(self, app_without_types: App) -> None:
        """PropertyGenerator warns when no typed parameters found."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_without_types)
        result = generator.generate()

        assert len(result.warnings) > 0
        assert "No commands/queries" in result.warnings[0]

    def test_generated_code_has_imports(self, app_with_types: App) -> None:
        """Generated code includes necessary imports."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types)
        result = generator.generate()

        assert "import pytest" in result.code
        assert "from hypothesis import given" in result.code
        assert "from hive.testing import" in result.code

    def test_generated_code_uses_strategy_for_type(self, app_with_types: App) -> None:
        """Generated tests use strategy_for_type for refinement types."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types)
        result = generator.generate()

        assert "strategy_for_type" in result.code
        assert "PositiveInt" in result.code
        assert "NonEmptyStr" in result.code

    def test_generated_code_has_given_decorator(self, app_with_types: App) -> None:
        """Generated tests have @given decorator."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types)
        result = generator.generate()

        assert "@given" in result.code

    def test_max_examples_setting(self, app_with_types: App) -> None:
        """PropertyGenerator respects max_examples setting."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types, max_examples=50)
        result = generator.generate()

        assert "max_examples=50" in result.code

    def test_test_case_names_are_unique(self, app_with_types: App) -> None:
        """Generated test case names are unique."""
        from hive.testing.properties import PropertyGenerator

        generator = PropertyGenerator(app_with_types)
        result = generator.generate()

        names = [tc.name for tc in result.test_cases]
        assert len(names) == len(set(names)), "Test names should be unique"


class TestPropertyTestCase:
    """Tests for PropertyTestCase dataclass."""

    def test_test_case_creation(self) -> None:
        """PropertyTestCase can be created with all fields."""
        from hive.testing.properties import PropertyTestCase

        tc = PropertyTestCase(
            name="test_set_priority_accepts_valid_inputs",
            target_name="set_priority",
            target_type="command",
            parameters=[{"name": "task_id", "type_name": "PositiveInt"}],
            test_body="    pass",
        )

        assert tc.name == "test_set_priority_accepts_valid_inputs"
        assert tc.target_name == "set_priority"
        assert tc.target_type == "command"


class TestPropertyGeneratorResult:
    """Tests for PropertyGeneratorResult dataclass."""

    def test_result_defaults(self) -> None:
        """PropertyGeneratorResult has empty defaults."""
        from hive.testing.properties import PropertyGeneratorResult

        result = PropertyGeneratorResult()

        assert result.test_cases == []
        assert result.warnings == []
        assert result.code == ""


class TestSupportedTypes:
    """Tests for supported refinement types."""

    def test_positive_int_supported(self) -> None:
        """PositiveInt is in supported types."""
        from hive.testing.properties import SUPPORTED_REFINEMENT_TYPES

        assert "PositiveInt" in SUPPORTED_REFINEMENT_TYPES

    def test_non_empty_str_supported(self) -> None:
        """NonEmptyStr is in supported types."""
        from hive.testing.properties import SUPPORTED_REFINEMENT_TYPES

        assert "NonEmptyStr" in SUPPORTED_REFINEMENT_TYPES

    def test_percentage_supported(self) -> None:
        """Percentage is in supported types."""
        from hive.testing.properties import SUPPORTED_REFINEMENT_TYPES

        assert "Percentage" in SUPPORTED_REFINEMENT_TYPES
