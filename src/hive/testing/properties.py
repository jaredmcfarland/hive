"""Property-based test generator for Hive applications.

This module generates hypothesis tests that use strategy_for_type
to automatically generate test inputs for commands and queries.

Example:
    from hive.testing.properties import PropertyGenerator

    generator = PropertyGenerator(app)
    test_code = generator.generate()
    print(test_code)  # Outputs hypothesis-compatible test code
"""

from __future__ import annotations

from dataclasses import dataclass, field
import inspect
import textwrap
from typing import TYPE_CHECKING, Any, get_type_hints

from hive.types import (
    Day,
    Email,
    FilePath,
    Hour,
    HttpStatusCode,
    Identifier,
    Minute,
    Month,
    NegativeInt,
    NonEmptyStr,
    NonNegativeFloat,
    NonNegativeInt,
    Percentage,
    Port,
    PositiveFloat,
    PositiveInt,
    Probability,
    Second,
    Slug,
    TrimmedStr,
    UnitInterval,
    Url,
    Year,
)

if TYPE_CHECKING:
    from hive.app import App


@dataclass
class PropertyTestCase:
    """A single property test case.

    Attributes:
        name: Test function name.
        target_name: Name of the command/query being tested.
        target_type: Type of target ("command" or "query").
        parameters: Parameter info for strategy generation.
        test_body: Python code for the test body.
    """

    name: str
    target_name: str
    target_type: str
    parameters: list[dict[str, Any]]
    test_body: str


@dataclass
class PropertyGeneratorResult:
    """Result from property test generation.

    Attributes:
        test_cases: List of generated test cases.
        warnings: Any warnings during generation.
        code: Generated Python code as string.
    """

    test_cases: list[PropertyTestCase] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    code: str = ""


# Types that have strategies available (string names)
SUPPORTED_REFINEMENT_TYPES = {
    "PositiveInt",
    "NonNegativeInt",
    "NegativeInt",
    "PositiveFloat",
    "NonNegativeFloat",
    "NegativeFloat",
    "UnitInterval",
    "Percentage",
    "Probability",
    "Port",
    "HttpStatusCode",
    "Year",
    "Month",
    "Day",
    "Hour",
    "Minute",
    "Second",
    "NonEmptyStr",
    "TrimmedStr",
    "Identifier",
    "Slug",
    "Email",
    "Url",
    "FilePath",
}

# Mapping from actual type objects to their names
# This is needed because Annotated types don't have __name__
REFINEMENT_TYPE_MAP: dict[Any, str] = {
    PositiveInt: "PositiveInt",
    NonNegativeInt: "NonNegativeInt",
    NegativeInt: "NegativeInt",
    PositiveFloat: "PositiveFloat",
    NonNegativeFloat: "NonNegativeFloat",
    UnitInterval: "UnitInterval",
    Percentage: "Percentage",
    Probability: "Probability",
    Port: "Port",
    HttpStatusCode: "HttpStatusCode",
    Year: "Year",
    Month: "Month",
    Day: "Day",
    Hour: "Hour",
    Minute: "Minute",
    Second: "Second",
    NonEmptyStr: "NonEmptyStr",
    TrimmedStr: "TrimmedStr",
    Identifier: "Identifier",
    Slug: "Slug",
    Email: "Email",
    Url: "Url",
    FilePath: "FilePath",
}


class PropertyGenerator:
    """Generate property tests from Hive application type annotations.

    Extracts type information from command and query parameters,
    then generates hypothesis tests using strategy_for_type.

    Example:
        >>> from hive.testing.properties import PropertyGenerator
        >>> generator = PropertyGenerator(app)
        >>> result = generator.generate()
        >>> print(result.code)
    """

    def __init__(
        self,
        app: App,
        *,
        max_examples: int = 100,
        suppress_health_check: bool = False,
    ) -> None:
        """Initialize the property generator.

        Args:
            app: Hive application to generate tests for.
            max_examples: Maximum hypothesis examples per test.
            suppress_health_check: Whether to suppress hypothesis health checks.
        """
        self.app = app
        self.max_examples = max_examples
        self.suppress_health_check = suppress_health_check

    def generate(self) -> PropertyGeneratorResult:
        """Generate property tests.

        Returns:
            PropertyGeneratorResult with test cases and generated code.
        """
        result = PropertyGeneratorResult()

        # Generate tests for commands
        for reg in self.app.registry.list_commands():
            params = self._extract_typed_params(reg.func)
            if params:
                test_case = self._create_test_case(reg.name, "command", params)
                if test_case:
                    result.test_cases.append(test_case)

        # Generate tests for queries
        for reg in self.app.registry.list_queries():
            params = self._extract_typed_params(reg.func)
            if params:
                test_case = self._create_test_case(reg.name, "query", params)
                if test_case:
                    result.test_cases.append(test_case)

        # Generate code
        if result.test_cases:
            result.code = self._render_test_module(result.test_cases)
        else:
            result.warnings.append("No commands/queries with refinement type parameters found")
            result.code = self._render_empty_module()

        return result

    def _extract_typed_params(
        self,
        func: Any,
    ) -> list[dict[str, Any]]:
        """Extract parameters with refinement types from a function.

        Args:
            func: Function to extract parameters from.

        Returns:
            List of parameter info dicts with type and strategy info.
        """
        params = []

        # Build a namespace that includes hive.types for resolving type hints
        import hive.types as hive_types

        globalns = getattr(func, "__globals__", {}).copy()
        # Add all exported names from hive.types to the namespace
        for name in hive_types.__all__:
            globalns[name] = getattr(hive_types, name)

        try:
            # Use include_extras=True to preserve Annotated wrappers
            hints = get_type_hints(func, globalns=globalns, include_extras=True)
        except Exception:
            # Can't get type hints (e.g., forward references)
            return params

        sig = inspect.signature(func)

        for param_name, param in sig.parameters.items():
            # Skip ctx (execution context) and self
            if param_name in ("ctx", "self"):
                continue

            # Get the type hint
            param_type = hints.get(param_name)
            if param_type is None:
                continue

            # Check if it's a supported refinement type
            type_name = self._get_type_name(param_type)
            if type_name in SUPPORTED_REFINEMENT_TYPES or type_name in (
                "int",
                "str",
                "float",
                "bool",
            ):
                params.append(
                    {
                        "name": param_name,
                        "type": param_type,
                        "type_name": type_name,
                        "has_default": param.default is not inspect.Parameter.empty,
                        "default": param.default
                        if param.default is not inspect.Parameter.empty
                        else None,
                    }
                )

        return params

    def _get_type_name(self, type_hint: Any) -> str:
        """Get the string name of a type hint.

        Args:
            type_hint: Type hint to get name from.

        Returns:
            String name of the type.
        """
        # Check against our refinement type map first (Annotated types)
        if type_hint in REFINEMENT_TYPE_MAP:
            return REFINEMENT_TYPE_MAP[type_hint]
        # Basic types with __name__
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__
        # Handle typing generics
        if hasattr(type_hint, "__origin__"):
            return str(type_hint)
        return str(type_hint)

    def _create_test_case(
        self,
        name: str,
        target_type: str,
        parameters: list[dict[str, Any]],
    ) -> PropertyTestCase | None:
        """Create a test case for a command/query.

        Args:
            name: Command/query name.
            target_type: Type of target.
            parameters: Parameter information.

        Returns:
            PropertyTestCase or None if cannot generate.
        """
        # Generate test name
        safe_name = name.replace("-", "_")
        test_name = f"test_{safe_name}_accepts_valid_inputs"

        # Generate test body
        test_body = self._generate_test_body(name, target_type, parameters)

        return PropertyTestCase(
            name=test_name,
            target_name=name,
            target_type=target_type,
            parameters=parameters,
            test_body=test_body,
        )

    def _generate_test_body(
        self,
        name: str,
        target_type: str,
        parameters: list[dict[str, Any]],
    ) -> str:
        """Generate test body for property test.

        Args:
            name: Command/query name.
            target_type: Type of target.
            parameters: Parameter information.

        Returns:
            Python code for test body.
        """
        invoke_method = "invoke" if target_type == "command" else "query"

        # Build given decorator arguments
        given_args = []
        for param in parameters:
            type_name = param["type_name"]
            param_name = param["name"]

            if type_name in SUPPORTED_REFINEMENT_TYPES:
                given_args.append(f"{param_name}=strategy_for_type({type_name})")
            elif type_name == "int":
                given_args.append(f"{param_name}=st.integers()")
            elif type_name == "str":
                given_args.append(f"{param_name}=st.text()")
            elif type_name == "float":
                given_args.append(f"{param_name}=st.floats(allow_nan=False)")
            elif type_name == "bool":
                given_args.append(f"{param_name}=st.booleans()")

        # Build parameter kwargs for invoke
        invoke_kwargs = ", ".join(f"{p['name']}={p['name']}" for p in parameters)

        return f'''\
"""Test that {name} accepts valid inputs from strategy_for_type."""
# Generated property test using hypothesis
async with TestClient(app) as client:
    # This should not raise - valid inputs should be accepted
    try:
        await client.{invoke_method}("{name}", {invoke_kwargs})
    except CommandError:
        # Contract violations are expected for some inputs
        pass'''

    def _render_test_module(self, test_cases: list[PropertyTestCase]) -> str:
        """Render complete test module.

        Args:
            test_cases: List of test cases to include.

        Returns:
            Complete Python test file content.
        """
        # Collect all needed type imports
        type_imports = set()
        for tc in test_cases:
            for param in tc.parameters:
                if param["type_name"] in SUPPORTED_REFINEMENT_TYPES:
                    type_imports.add(param["type_name"])

        type_import_line = ""
        if type_imports:
            type_import_line = f"from hive.types import {', '.join(sorted(type_imports))}\n"

        settings_args = [f"max_examples={self.max_examples}"]
        if self.suppress_health_check:
            settings_args.append("suppress_health_check=[HealthCheck.too_slow]")
        settings_str = ", ".join(settings_args)

        header = f'''\
"""Property-based tests for {self.app.name}.

Auto-generated by Hive property test generator.
These tests verify that commands/queries accept valid inputs.

Run with: pytest {self.app.name}_properties.py
"""

import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

from hive.errors import CommandError
from hive.testing import TestClient, strategy_for_type
{type_import_line}
# Import your app - adjust path as needed
from app import app  # noqa: F401


@settings({settings_str})
class TestProperties:
    """Property-based tests for commands and queries."""

'''

        test_code = ""
        for tc in test_cases:
            # Build given decorator
            given_args = []
            for param in tc.parameters:
                type_name = param["type_name"]
                param_name = param["name"]

                if type_name in SUPPORTED_REFINEMENT_TYPES:
                    given_args.append(f"{param_name}=strategy_for_type({type_name})")
                elif type_name == "int":
                    given_args.append(f"{param_name}=st.integers()")
                elif type_name == "str":
                    given_args.append(f"{param_name}=st.text()")
                elif type_name == "float":
                    given_args.append(f"{param_name}=st.floats(allow_nan=False)")
                elif type_name == "bool":
                    given_args.append(f"{param_name}=st.booleans()")

            given_str = ", ".join(given_args)
            param_names = ", ".join(p["name"] for p in tc.parameters)

            test_code += f"    @given({given_str})\n"
            test_code += "    @pytest.mark.asyncio\n"
            test_code += f"    async def {tc.name}(self, {param_names}) -> None:\n"
            test_code += textwrap.indent(tc.test_body, "        ")
            test_code += "\n\n"

        return header + test_code.rstrip() + "\n"

    def _render_empty_module(self) -> str:
        """Render empty test module when no typed parameters found.

        Returns:
            Python test file with no tests.
        """
        return f'''\
"""Property-based tests for {self.app.name}.

Auto-generated by Hive property test generator.

No commands/queries with refinement type parameters were found.
Add refinement types (PositiveInt, NonEmptyStr, etc.) to your
command parameters to generate property tests.

Example:
    from hive.types import PositiveInt, NonEmptyStr

    @command(app)
    async def create_task(ctx, title: NonEmptyStr, priority: PositiveInt):
        ...
"""

# No tests generated - add refinement types to enable property testing.
'''
