"""Unit tests for ConformanceGenerator.

Tests for conformance test generation from Hive application contracts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hive.app import App


class TestConformanceGenerator:
    """Tests for ConformanceGenerator class."""

    @pytest.fixture
    def app_with_contracts(self) -> App:
        """Create a sample app with contracts for testing."""
        from hive.app import App
        from hive.contracts import ensures, requires
        from hive.core.decorators import command, query

        app = App("test-app")

        @command(app)
        @requires(lambda ctx, user_id: user_id > 0, "User ID must be positive")
        async def get_user(ctx, user_id: int) -> dict:
            """Get a user by ID."""
            return {"id": user_id, "name": "Test User"}

        @command(app)
        @ensures(lambda ctx, a, b, result: result == a + b, "Result must equal a + b")
        async def add_numbers(ctx, a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        @query(app)
        @requires(lambda ctx, name: len(name) > 0, "Name cannot be empty")
        @ensures(lambda ctx, name, result: name in result, "Greeting must contain name")
        async def greet(ctx, name: str) -> str:
            """Greet someone by name."""
            return f"Hello, {name}!"

        return app

    @pytest.fixture
    def app_without_contracts(self) -> App:
        """Create a sample app without contracts."""
        from hive.app import App
        from hive.core.decorators import command

        app = App("no-contracts-app")

        @command(app)
        async def simple_command(ctx) -> str:
            """A simple command without contracts."""
            return "done"

        return app

    def test_generate_extracts_requires(self, app_with_contracts: App) -> None:
        """ConformanceGenerator extracts @requires contracts."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        # Should have test cases for requires
        requires_tests = [tc for tc in result.test_cases if tc.contract_type == "requires"]
        assert len(requires_tests) >= 2  # get_user and greet

    def test_generate_extracts_ensures(self, app_with_contracts: App) -> None:
        """ConformanceGenerator extracts @ensures contracts."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        # Should have test cases for ensures
        ensures_tests = [tc for tc in result.test_cases if tc.contract_type == "ensures"]
        assert len(ensures_tests) >= 2  # add_numbers and greet

    def test_generate_creates_code(self, app_with_contracts: App) -> None:
        """ConformanceGenerator generates valid Python code."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        assert result.code is not None
        assert len(result.code) > 0

        # Code should be valid Python - try to compile it
        compile(result.code, "<string>", "exec")

    def test_generate_empty_contracts_warning(self, app_without_contracts: App) -> None:
        """ConformanceGenerator warns when no contracts found."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_without_contracts)
        result = generator.generate()

        assert len(result.warnings) > 0
        assert "No contracts found" in result.warnings[0]

    def test_generated_code_has_imports(self, app_with_contracts: App) -> None:
        """Generated code includes necessary imports."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        assert "import pytest" in result.code
        assert "from hive.errors import CommandError" in result.code
        assert "from hive.testing import TestClient" in result.code

    def test_generated_code_has_pytest_markers(self, app_with_contracts: App) -> None:
        """Generated tests have @pytest.mark.asyncio decorator."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        assert "@pytest.mark.asyncio" in result.code

    def test_test_case_names_are_unique(self, app_with_contracts: App) -> None:
        """Generated test case names are unique."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        names = [tc.name for tc in result.test_cases]
        assert len(names) == len(set(names)), "Test names should be unique"

    def test_test_case_body_references_command(self, app_with_contracts: App) -> None:
        """Test body references the correct command/query name."""
        from hive.testing.conformance import ConformanceGenerator

        generator = ConformanceGenerator(app_with_contracts)
        result = generator.generate()

        for tc in result.test_cases:
            assert tc.target_name in tc.test_body


class TestContractInfo:
    """Tests for ContractInfo dataclass."""

    def test_contract_info_creation(self) -> None:
        """ContractInfo can be created with all fields."""
        from hive.testing.conformance import ContractInfo

        info = ContractInfo(
            contract_type="requires",
            message="value must be positive",
            source="lambda x: x > 0",
        )

        assert info.contract_type == "requires"
        assert info.message == "value must be positive"
        assert info.source == "lambda x: x > 0"

    def test_contract_info_defaults(self) -> None:
        """ContractInfo has sensible defaults."""
        from hive.testing.conformance import ContractInfo

        info = ContractInfo(
            contract_type="ensures",
            message="result is valid",
        )

        assert info.source is None


class TestConformanceTestCase:
    """Tests for ConformanceTestCase dataclass."""

    def test_test_case_creation(self) -> None:
        """ConformanceTestCase can be created with all fields."""
        from hive.testing.conformance import ConformanceTestCase

        tc = ConformanceTestCase(
            name="test_get_user_requires_positive",
            target_name="get_user",
            target_type="command",
            contract_type="requires",
            contract_message="User ID must be positive",
            test_body="    pass",
        )

        assert tc.name == "test_get_user_requires_positive"
        assert tc.target_name == "get_user"
        assert tc.target_type == "command"


class TestConformanceGeneratorResult:
    """Tests for ConformanceGeneratorResult dataclass."""

    def test_result_defaults(self) -> None:
        """ConformanceGeneratorResult has empty defaults."""
        from hive.testing.conformance import ConformanceGeneratorResult

        result = ConformanceGeneratorResult()

        assert result.test_cases == []
        assert result.warnings == []
        assert result.code == ""


class TestContractMetadataStorage:
    """Tests that contract decorators store metadata correctly."""

    def test_requires_stores_metadata(self) -> None:
        """@requires decorator stores contract metadata."""
        from hive.contracts import requires

        @requires(lambda x: x > 0, "value must be positive")
        async def test_func(x: int) -> int:
            return x

        assert hasattr(test_func, "__hive_requires__")
        reqs = test_func.__hive_requires__
        assert len(reqs) == 1
        assert reqs[0]["message"] == "value must be positive"

    def test_ensures_stores_metadata(self) -> None:
        """@ensures decorator stores contract metadata."""
        from hive.contracts import ensures

        @ensures(lambda x, result: result > 0, "result must be positive")
        async def test_func(x: int) -> int:
            return x

        assert hasattr(test_func, "__hive_ensures__")
        ens = test_func.__hive_ensures__
        assert len(ens) == 1
        assert ens[0]["message"] == "result must be positive"

    def test_multiple_requires_accumulate(self) -> None:
        """Multiple @requires decorators accumulate."""
        from hive.contracts import requires

        @requires(lambda x: x > 0, "must be positive")
        @requires(lambda x: x < 100, "must be less than 100")
        async def test_func(x: int) -> int:
            return x

        assert hasattr(test_func, "__hive_requires__")
        reqs = test_func.__hive_requires__
        assert len(reqs) == 2
