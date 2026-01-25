"""Conformance test generator for Hive applications.

This module generates pytest test cases that verify contract compliance
for commands and queries decorated with @requires, @ensures, and @invariant.

Example:
    from hive.testing.conformance import ConformanceGenerator

    generator = ConformanceGenerator(app)
    test_code = generator.generate()
    print(test_code)  # Outputs pytest-compatible Python code
"""

from __future__ import annotations

from dataclasses import dataclass, field
import inspect
import textwrap
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hive.app import App


@dataclass
class ContractInfo:
    """Information about a single contract (requires/ensures).

    Attributes:
        contract_type: Type of contract ("requires" or "ensures").
        message: Contract message or description.
        source: Source code of condition if available.
    """

    contract_type: str
    message: str
    source: str | None = None


@dataclass
class ConformanceTestCase:
    """A single conformance test case.

    Attributes:
        name: Test function name (e.g., test_get_user_requires_positive_id).
        target_name: Name of the command/query being tested.
        target_type: Type of target ("command", "query", or "entity").
        contract_type: Type of contract being tested.
        contract_message: Contract message for documentation.
        test_body: Python code for the test body.
    """

    name: str
    target_name: str
    target_type: str
    contract_type: str
    contract_message: str
    test_body: str


@dataclass
class ConformanceGeneratorResult:
    """Result from conformance test generation.

    Attributes:
        test_cases: List of generated test cases.
        warnings: Any warnings during generation.
        code: Generated Python code as string.
    """

    test_cases: list[ConformanceTestCase] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    code: str = ""


class ConformanceGenerator:
    """Generate conformance tests from Hive application contracts.

    Extracts @requires, @ensures, and @invariant contracts from
    registered commands, queries, and entities, then generates
    pytest test cases.

    Example:
        >>> from hive.testing.conformance import ConformanceGenerator
        >>> generator = ConformanceGenerator(app)
        >>> result = generator.generate()
        >>> print(result.code)
    """

    def __init__(self, app: App) -> None:
        """Initialize the conformance generator.

        Args:
            app: Hive application to generate tests for.
        """
        self.app = app

    def generate(self) -> ConformanceGeneratorResult:
        """Generate conformance tests.

        Returns:
            ConformanceGeneratorResult with test cases and generated code.
        """
        result = ConformanceGeneratorResult()

        # Extract contracts from commands
        for reg in self.app.registry.list_commands():
            contracts = self._extract_contracts(reg.func, reg.name)
            for contract in contracts:
                test_case = self._create_test_case(reg.name, "command", contract)
                if test_case:
                    result.test_cases.append(test_case)

        # Extract contracts from queries
        for reg in self.app.registry.list_queries():
            contracts = self._extract_contracts(reg.func, reg.name)
            for contract in contracts:
                test_case = self._create_test_case(reg.name, "query", contract)
                if test_case:
                    result.test_cases.append(test_case)

        # Extract invariants from entities
        for reg in self.app.registry.list_entities():
            invariants = self._extract_invariants(reg.cls, reg.name)
            for inv in invariants:
                test_case = self._create_invariant_test(reg.name, inv)
                if test_case:
                    result.test_cases.append(test_case)

        # Generate code
        if result.test_cases:
            result.code = self._render_test_module(result.test_cases)
        else:
            result.warnings.append("No contracts found to generate tests for")
            result.code = self._render_empty_module()

        return result

    def _extract_contracts(
        self,
        func: Any | None,
        target_name: str,
    ) -> list[ContractInfo]:
        """Extract contract information from a function.

        Only extracts Hive contracts (@requires/@ensures from hive.contracts),
        not raw deal contracts. This ensures generated tests expect CommandError.

        Args:
            func: Function to extract contracts from.
            target_name: Name of the target.

        Returns:
            List of ContractInfo objects.
        """
        if func is None:
            return []

        contracts: list[ContractInfo] = []

        # Check for @requires contracts (stored by our decorator)
        requires_list = getattr(func, "__hive_requires__", [])
        for req in requires_list:
            message = req.get("message", f"{target_name} precondition")
            condition = req.get("condition")
            source = self._get_lambda_source(condition) if condition else None
            contracts.append(ContractInfo(contract_type="requires", message=message, source=source))

        # Check for @ensures contracts
        ensures_list = getattr(func, "__hive_ensures__", [])
        for ens in ensures_list:
            message = ens.get("message", f"{target_name} postcondition")
            condition = ens.get("condition")
            source = self._get_lambda_source(condition) if condition else None
            contracts.append(ContractInfo(contract_type="ensures", message=message, source=source))

        # Note: We intentionally skip raw deal contracts (__deal_pre__/__deal_post__)
        # because they raise deal.PreContractError/PostContractError, not CommandError.
        # Users should use hive.contracts.requires/ensures for Hive applications.

        return contracts

    def _extract_invariants(
        self,
        cls: type | None,
        name: str,
    ) -> list[ContractInfo]:
        """Extract invariant information from an entity class.

        Args:
            cls: Entity class to extract invariants from.
            name: Entity name.

        Returns:
            List of ContractInfo objects.
        """
        if cls is None:
            return []

        invariants: list[ContractInfo] = []

        # Check for deal invariants
        deal_inv = getattr(cls, "__deal_inv__", [])
        for inv in deal_inv:
            message = getattr(inv, "__deal_message__", f"{name} invariant")
            invariants.append(ContractInfo(contract_type="invariant", message=message))

        return invariants

    def _get_lambda_source(self, func: Any) -> str | None:
        """Try to get source code for a lambda.

        Args:
            func: Function to get source for.

        Returns:
            Source code string or None.
        """
        try:
            source = inspect.getsource(func)
            # Try to extract just the lambda portion
            if "lambda" in source:
                return source.strip()
            return None
        except (OSError, TypeError):
            return None

    def _slugify(self, text: str) -> str:
        """Convert text to valid Python identifier slug.

        Args:
            text: Text to slugify.

        Returns:
            Snake_case string safe for Python identifiers.
        """
        import re

        # Convert to lowercase
        slug = text.lower()
        # Replace non-alphanumeric characters with underscores
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        # Remove leading/trailing underscores
        slug = slug.strip("_")
        # Ensure it doesn't start with a number
        if slug and slug[0].isdigit():
            slug = f"n{slug}"
        return slug

    def _create_test_case(
        self,
        name: str,
        target_type: str,
        contract: ContractInfo,
    ) -> ConformanceTestCase | None:
        """Create a test case for a contract.

        Args:
            name: Command/query name.
            target_type: Type of target.
            contract: Contract information.

        Returns:
            ConformanceTestCase or None if cannot generate.
        """
        # Generate test name
        safe_name = name.replace("-", "_")
        contract_slug = self._slugify(contract.message)[:30]
        test_name = f"test_{safe_name}_{contract.contract_type}_{contract_slug}"

        # Generate test body based on contract type
        if contract.contract_type == "requires":
            test_body = self._generate_requires_test_body(name, target_type, contract)
        elif contract.contract_type == "ensures":
            test_body = self._generate_ensures_test_body(name, target_type, contract)
        else:
            return None

        return ConformanceTestCase(
            name=test_name,
            target_name=name,
            target_type=target_type,
            contract_type=contract.contract_type,
            contract_message=contract.message,
            test_body=test_body,
        )

    def _create_invariant_test(
        self,
        name: str,
        contract: ContractInfo,
    ) -> ConformanceTestCase | None:
        """Create a test case for an entity invariant.

        Args:
            name: Entity name.
            contract: Invariant information.

        Returns:
            ConformanceTestCase or None.
        """
        safe_name = name.replace("-", "_")
        contract_slug = contract.message.lower().replace(" ", "_")[:30]
        test_name = f"test_{safe_name}_invariant_{contract_slug}"

        test_body = self._generate_invariant_test_body(name, contract)

        return ConformanceTestCase(
            name=test_name,
            target_name=name,
            target_type="entity",
            contract_type="invariant",
            contract_message=contract.message,
            test_body=test_body,
        )

    def _generate_requires_test_body(
        self,
        name: str,
        target_type: str,
        contract: ContractInfo,
    ) -> str:
        """Generate test body for @requires contract.

        Args:
            name: Command/query name.
            target_type: Type of target.
            contract: Contract information.

        Returns:
            Python code for test body.
        """
        invoke_method = "invoke" if target_type == "command" else "query"

        return f'''\
    """Test that {name} enforces: {contract.message}"""
    # This test verifies that the precondition is enforced.
    # Provide invalid inputs that should violate the @requires condition.
    async with TestClient(app) as client:
        # TODO: Provide inputs that violate: {contract.message}
        # The command should raise CommandError when precondition fails
        with pytest.raises(CommandError):
            await client.{invoke_method}("{name}")  # Add invalid kwargs'''

    def _generate_ensures_test_body(
        self,
        name: str,
        target_type: str,
        contract: ContractInfo,
    ) -> str:
        """Generate test body for @ensures contract.

        Args:
            name: Command/query name.
            target_type: Type of target.
            contract: Contract information.

        Returns:
            Python code for test body.
        """
        invoke_method = "invoke" if target_type == "command" else "query"

        return f'''\
    """Test that {name} satisfies: {contract.message}"""
    # This test verifies that the postcondition holds after execution.
    async with TestClient(app) as client:
        # TODO: Provide valid inputs and verify result satisfies: {contract.message}
        result = await client.{invoke_method}("{name}")  # Add valid kwargs
        # Assert postcondition holds on result
        assert result is not None  # Replace with actual postcondition check'''

    def _generate_invariant_test_body(
        self,
        name: str,
        contract: ContractInfo,
    ) -> str:
        """Generate test body for @invariant contract.

        Args:
            name: Entity name.
            contract: Contract information.

        Returns:
            Python code for test body.
        """
        return f'''\
    """Test that {name} maintains: {contract.message}"""
    # This test verifies that the class invariant is maintained.
    # TODO: Create entity instance and verify invariant holds
    # TODO: Attempt to create instance that violates invariant
    pass  # Replace with invariant verification'''

    def _render_test_module(self, test_cases: list[ConformanceTestCase]) -> str:
        """Render complete test module.

        Args:
            test_cases: List of test cases to include.

        Returns:
            Complete Python test file content.
        """
        # Group by target for better organization
        header = '''\
"""Conformance tests for {app_name}.

Auto-generated by Hive conformance test generator.
These tests verify that contracts (@requires, @ensures, @invariant) are honored.

Run with: pytest {filename}
"""

import pytest

from hive.errors import CommandError
from hive.testing import TestClient

# Import your app - adjust path as needed
from app import app  # noqa: F401


'''.format(app_name=self.app.name, filename="test_conformance.py")

        test_code = ""
        for tc in test_cases:
            test_code += f"@pytest.mark.asyncio\nasync def {tc.name}() -> None:\n"
            test_code += textwrap.indent(tc.test_body.rstrip(), "")
            test_code += "\n\n\n"

        return header + test_code.rstrip() + "\n"

    def _render_empty_module(self) -> str:
        """Render empty test module when no contracts found.

        Returns:
            Python test file with no tests.
        """
        return f'''\
"""Conformance tests for {self.app.name}.

Auto-generated by Hive conformance test generator.

No contracts (@requires, @ensures, @invariant) were found in the application.
Add contracts to your commands, queries, and entities to generate tests.

Example:
    from hive.contracts import requires, ensures

    @command(app)
    @requires(lambda ctx, user_id: user_id > 0, "User ID must be positive")
    async def get_user(ctx, user_id: int) -> User:
        ...
"""

# No tests generated - add contracts to your app to enable conformance testing.
'''
