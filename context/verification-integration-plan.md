# Verification Stack Integration Plan for Hive

## Executive Summary

This document details the integration of **beartype**, **deal**, and **Hypothesis** into the Hive framework to complete its specification-driven development vision. These tools transform Hive's type hints from documentation into executable contracts, enabling:

- **Refinement types** as first-class specification primitives
- **Design-by-contract** guarantees on framework internals
- **Property-based testing** for comprehensive framework validation
- **Automatic test generation** for user-defined commands

The integration is designed to be **layered and non-breaking**, extending Hive's existing patterns rather than replacing them.

---

## Table of Contents

1. [Philosophy Alignment](#1-philosophy-alignment)
2. [Integration Architecture](#2-integration-architecture)
3. [Phase 1: Foundation Layer](#3-phase-1-foundation-layer)
4. [Phase 2: Contract Layer](#4-phase-2-contract-layer)
5. [Phase 3: Specification Export](#5-phase-3-specification-export)
6. [Phase 4: Testing Utilities](#6-phase-4-testing-utilities)
7. [Migration Strategy](#7-migration-strategy)
8. [Risk Assessment](#8-risk-assessment)
9. [Dependency Management](#9-dependency-management)
10. [Success Criteria](#10-success-criteria)

---

## 1. Philosophy Alignment

### Hive's Core Principle

> "Decorated Python code is the specification source of truth."

### How Verification Tools Complete This Vision

| Current State | Enhanced State |
|---------------|----------------|
| `age: int` → CLI accepts any integer | `age: Age` → CLI accepts 0-150, validates automatically |
| Docstrings describe preconditions | `@deal.pre` enforces preconditions at runtime |
| Manual test writing | `deal.cases` generates tests from contracts |
| Unit tests with examples | Property tests verify behavior for all valid inputs |

### The Verification Pyramid in Hive

```
                    ┌─────────────────────────────────────┐
                    │         Hypothesis + deal.cases     │  Test-time verification
                    │      Property-based test generation │  (comprehensive coverage)
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │              deal                    │  Runtime contracts
                    │    Pre/post conditions, invariants   │  (framework internals)
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │            beartype                  │  Runtime type enforcement
                    │    Refinement types as primitives    │  (every function call)
                    └─────────────────────────────────────┘
```

---

## 2. Integration Architecture

### Module Structure

```
src/hive/
├── __init__.py                    # Add: Refinement type exports
├── types/                         # NEW: Refinement types module
│   ├── __init__.py               # Public type exports
│   ├── primitives.py             # Core refinement types
│   ├── strings.py                # String refinement types
│   ├── numeric.py                # Numeric refinement types
│   ├── collections.py            # Collection refinement types
│   └── domain.py                 # Domain-specific types (optional)
├── contracts/                     # NEW: Contract utilities
│   ├── __init__.py               # Contract decorator exports
│   ├── decorators.py             # Hive-specific contract wrappers
│   └── validators.py             # Reusable validation functions
├── core/
│   ├── decorators.py             # MODIFY: Extract refinement metadata
│   ├── registry.py               # MODIFY: Store refinement constraints
│   └── types.py                  # MODIFY: Add constraint fields
├── runtime/
│   ├── context.py                # MODIFY: Add deal invariants
│   └── output.py                 # MODIFY: Add deal contracts
├── generators/
│   └── cli.py                    # MODIFY: Generate validation from refinements
└── testing/                       # NEW: Testing utilities (Phase 4)
    ├── __init__.py
    ├── strategies.py             # Hypothesis strategies for Hive types
    ├── properties.py             # Property test generators
    └── cases.py                  # deal.cases integration
```

### Integration Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Code                                       │
│                                                                             │
│   @command(app)                                                             │
│   @deal.pre(lambda ctx, task_id: task_id > 0)  ◄── Optional user contracts │
│   async def get_task(ctx, task_id: PositiveInt) -> Task:  ◄── Refinements  │
│       ...                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Decorator Layer                                    │
│                                                                             │
│   @command extracts:                                                        │
│   - Type hints (including Annotated metadata)                               │
│   - Refinement constraints (beartype Is[] predicates)                       │
│   - deal contracts (pre/post/ensure)                                        │
│   - Docstrings                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Registry                                        │
│                                                                             │
│   CommandRegistration now includes:                                         │
│   - parameters: List[ParameterInfo]  (with constraints field)               │
│   - preconditions: List[ContractInfo]                                       │
│   - postconditions: List[ContractInfo]                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │    CLI    │   │    TUI    │   │  Schema   │
            │ Generator │   │ Generator │   │  Export   │
            └───────────┘   └───────────┘   └───────────┘
                 │               │               │
                 ▼               ▼               ▼
            Typer with      Textual with    JSON Schema
            validation      input widgets   with constraints
```

---

## 3. Phase 1: Foundation Layer

### 3.1 Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # Existing
    "typer>=0.9.0",
    "rich>=13.0.0",
    "sqlmodel>=0.0.22",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "aiosqlite>=0.19.0",
    "greenlet>=2.0.0",
    # NEW: Verification stack
    "beartype>=0.18.0",
    "deal>=4.24.0",
]

[project.optional-dependencies]
dev = [
    # Existing
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    # NEW: Property-based testing
    "hypothesis>=6.100.0",
]
```

### 3.2 Refinement Types Module

#### `src/hive/types/__init__.py`

```python
"""
Hive Refinement Types

Semantic type aliases with runtime-enforced constraints.
Use these in command signatures to get automatic validation
in CLI, TUI, and API interfaces.

Example:
    from hive import command, App
    from hive.types import PositiveInt, Email, NonEmptyStr

    app = App("myapp")

    @command(app)
    async def create_user(ctx, name: NonEmptyStr, email: Email, age: PositiveInt):
        ...
"""

from hive.types.primitives import (
    PositiveInt,
    NonNegativeInt,
    NegativeInt,
    PositiveFloat,
    NonNegativeFloat,
    UnitInterval,
    Percentage,
    Probability,
)
from hive.types.strings import (
    NonEmptyStr,
    TrimmedStr,
    LowercaseStr,
    UppercaseStr,
    Identifier,
    Slug,
    Email,
    Url,
    FilePath,
    DirectoryPath,
)
from hive.types.numeric import (
    Port,
    HttpStatusCode,
    UnixTimestamp,
    Year,
    Month,
    Day,
    Hour,
    Minute,
    Second,
)
from hive.types.collections import (
    NonEmptyList,
    UniqueList,
    SortedList,
    NonEmptyDict,
    NonEmptySet,
)

__all__ = [
    # Primitives
    "PositiveInt",
    "NonNegativeInt",
    "NegativeInt",
    "PositiveFloat",
    "NonNegativeFloat",
    "UnitInterval",
    "Percentage",
    "Probability",
    # Strings
    "NonEmptyStr",
    "TrimmedStr",
    "LowercaseStr",
    "UppercaseStr",
    "Identifier",
    "Slug",
    "Email",
    "Url",
    "FilePath",
    "DirectoryPath",
    # Numeric
    "Port",
    "HttpStatusCode",
    "UnixTimestamp",
    "Year",
    "Month",
    "Day",
    "Hour",
    "Minute",
    "Second",
    # Collections
    "NonEmptyList",
    "UniqueList",
    "SortedList",
    "NonEmptyDict",
    "NonEmptySet",
]
```

#### `src/hive/types/primitives.py`

```python
"""Core numeric refinement types."""

from typing import Annotated
from beartype.vale import Is

# Integer refinements
PositiveInt = Annotated[int, Is[lambda x: x > 0]]
"""Integer greater than zero."""

NonNegativeInt = Annotated[int, Is[lambda x: x >= 0]]
"""Integer greater than or equal to zero."""

NegativeInt = Annotated[int, Is[lambda x: x < 0]]
"""Integer less than zero."""

# Float refinements
PositiveFloat = Annotated[float, Is[lambda x: x > 0.0]]
"""Float greater than zero."""

NonNegativeFloat = Annotated[float, Is[lambda x: x >= 0.0]]
"""Float greater than or equal to zero."""

UnitInterval = Annotated[float, Is[lambda x: 0.0 <= x <= 1.0]]
"""Float between 0.0 and 1.0 inclusive."""

Percentage = Annotated[float, Is[lambda x: 0.0 <= x <= 100.0]]
"""Float between 0.0 and 100.0 inclusive."""

Probability = UnitInterval
"""Alias for UnitInterval, semantically representing probability."""
```

#### `src/hive/types/strings.py`

```python
"""String refinement types."""

from typing import Annotated
import re
from beartype.vale import Is

NonEmptyStr = Annotated[str, Is[lambda s: len(s) > 0]]
"""Non-empty string."""

TrimmedStr = Annotated[str, Is[lambda s: s == s.strip()]]
"""String with no leading or trailing whitespace."""

LowercaseStr = Annotated[str, Is[lambda s: s == s.lower()]]
"""Lowercase string."""

UppercaseStr = Annotated[str, Is[lambda s: s == s.upper()]]
"""Uppercase string."""

Identifier = Annotated[str, Is[lambda s: s.isidentifier()]]
"""Valid Python identifier."""

Slug = Annotated[str, Is[lambda s: bool(re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', s))]]
"""URL-safe slug (lowercase alphanumeric with hyphens)."""

Email = Annotated[str, Is[lambda s: bool(re.match(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', s
))]]
"""Email address (basic validation)."""

Url = Annotated[str, Is[lambda s: bool(re.match(
    r'^https?://[^\s/$.?#].[^\s]*$', s
))]]
"""HTTP or HTTPS URL."""

FilePath = Annotated[str, Is[lambda s: len(s) > 0 and '\0' not in s]]
"""Non-empty string without null bytes (valid file path)."""

DirectoryPath = FilePath
"""Alias for FilePath, semantically representing a directory."""
```

#### `src/hive/types/numeric.py`

```python
"""Domain-specific numeric refinement types."""

from typing import Annotated
from beartype.vale import Is

Port = Annotated[int, Is[lambda x: 1 <= x <= 65535]]
"""Valid TCP/UDP port number (1-65535)."""

HttpStatusCode = Annotated[int, Is[lambda x: 100 <= x <= 599]]
"""HTTP status code (100-599)."""

UnixTimestamp = Annotated[int, Is[lambda x: x >= 0]]
"""Unix timestamp (non-negative integer)."""

Year = Annotated[int, Is[lambda x: 1 <= x <= 9999]]
"""Year (1-9999)."""

Month = Annotated[int, Is[lambda x: 1 <= x <= 12]]
"""Month (1-12)."""

Day = Annotated[int, Is[lambda x: 1 <= x <= 31]]
"""Day of month (1-31)."""

Hour = Annotated[int, Is[lambda x: 0 <= x <= 23]]
"""Hour (0-23)."""

Minute = Annotated[int, Is[lambda x: 0 <= x <= 59]]
"""Minute (0-59)."""

Second = Annotated[int, Is[lambda x: 0 <= x <= 59]]
"""Second (0-59)."""
```

#### `src/hive/types/collections.py`

```python
"""Collection refinement types."""

from typing import Annotated, TypeVar, List, Dict, Set, Any
from beartype.vale import Is

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

NonEmptyList = Annotated[List[T], Is[lambda x: len(x) > 0]]
"""List with at least one element."""

UniqueList = Annotated[List[T], Is[lambda x: len(x) == len(set(x))]]
"""List with no duplicate elements."""

SortedList = Annotated[List[T], Is[lambda x: x == sorted(x)]]
"""List in ascending sorted order."""

NonEmptyDict = Annotated[Dict[K, V], Is[lambda x: len(x) > 0]]
"""Dictionary with at least one key-value pair."""

NonEmptySet = Annotated[Set[T], Is[lambda x: len(x) > 0]]
"""Set with at least one element."""
```

### 3.3 Constraint Extraction Utilities

#### `src/hive/types/introspection.py`

```python
"""Utilities for extracting constraint metadata from refinement types."""

from typing import Any, get_origin, get_args, Annotated, Optional
from dataclasses import dataclass
import re


@dataclass
class ConstraintInfo:
    """Extracted constraint metadata from a refinement type."""

    base_type: type
    """The underlying Python type (int, str, float, etc.)."""

    description: str
    """Human-readable description of the constraint."""

    validator: Optional[callable]
    """The validation function, if extractable."""

    min_value: Optional[float] = None
    """Minimum value for numeric types."""

    max_value: Optional[float] = None
    """Maximum value for numeric types."""

    pattern: Optional[str] = None
    """Regex pattern for string types."""

    min_length: Optional[int] = None
    """Minimum length for string/collection types."""

    max_length: Optional[int] = None
    """Maximum length for string/collection types."""


def extract_constraints(type_hint: Any) -> Optional[ConstraintInfo]:
    """
    Extract constraint metadata from a type hint.

    Handles:
    - Plain types (int, str) -> returns None
    - Annotated types with beartype Is[] validators
    - Nested Annotated types

    Returns:
        ConstraintInfo if constraints found, None otherwise.
    """
    origin = get_origin(type_hint)

    if origin is not Annotated:
        return None

    args = get_args(type_hint)
    if not args:
        return None

    base_type = args[0]
    validators = args[1:]

    # Extract constraint info
    info = ConstraintInfo(
        base_type=base_type,
        description="",
        validator=None,
    )

    for validator in validators:
        # Handle beartype Is[] validators
        if hasattr(validator, '_is_valid'):
            info.validator = validator._is_valid

            # Try to extract numeric bounds from lambda source
            bounds = _extract_numeric_bounds(validator)
            if bounds:
                info.min_value, info.max_value = bounds

            # Try to extract string pattern
            pattern = _extract_string_pattern(validator)
            if pattern:
                info.pattern = pattern

            # Try to extract length constraints
            lengths = _extract_length_constraints(validator)
            if lengths:
                info.min_length, info.max_length = lengths

    # Generate description from constraints
    info.description = _generate_description(info)

    return info


def _extract_numeric_bounds(validator) -> Optional[tuple[Optional[float], Optional[float]]]:
    """Extract min/max bounds from a numeric validator."""
    try:
        import inspect
        source = inspect.getsource(validator._is_valid)

        # Match patterns like: x > 0, x >= 0, x < 100, x <= 100
        # Also compound: 0 <= x <= 100, 1 <= x <= 65535

        min_val = None
        max_val = None

        # Pattern: value <= x or value < x (minimum)
        match = re.search(r'(\d+(?:\.\d+)?)\s*<=?\s*x', source)
        if match:
            min_val = float(match.group(1))

        # Pattern: x > value or x >= value (minimum)
        match = re.search(r'x\s*>=?\s*(\d+(?:\.\d+)?)', source)
        if match:
            val = float(match.group(1))
            if min_val is None or val > min_val:
                min_val = val

        # Pattern: x <= value or x < value (maximum)
        match = re.search(r'x\s*<=?\s*(\d+(?:\.\d+)?)', source)
        if match:
            max_val = float(match.group(1))

        # Pattern: value >= x (maximum)
        match = re.search(r'(\d+(?:\.\d+)?)\s*>=?\s*x', source)
        if match:
            val = float(match.group(1))
            if max_val is None or val < max_val:
                max_val = val

        if min_val is not None or max_val is not None:
            return (min_val, max_val)
    except Exception:
        pass

    return None


def _extract_string_pattern(validator) -> Optional[str]:
    """Extract regex pattern from a string validator."""
    try:
        import inspect
        source = inspect.getsource(validator._is_valid)

        # Match: re.match(r'pattern', s)
        match = re.search(r"re\.match\(r?['\"](.+?)['\"]", source)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def _extract_length_constraints(validator) -> Optional[tuple[Optional[int], Optional[int]]]:
    """Extract length constraints from a validator."""
    try:
        import inspect
        source = inspect.getsource(validator._is_valid)

        min_len = None
        max_len = None

        # Pattern: len(x) > value or len(x) >= value
        match = re.search(r'len\([^)]+\)\s*>=?\s*(\d+)', source)
        if match:
            min_len = int(match.group(1))

        # Pattern: len(x) < value or len(x) <= value
        match = re.search(r'len\([^)]+\)\s*<=?\s*(\d+)', source)
        if match:
            max_len = int(match.group(1))

        if min_len is not None or max_len is not None:
            return (min_len, max_len)
    except Exception:
        pass

    return None


def _generate_description(info: ConstraintInfo) -> str:
    """Generate human-readable description from constraint info."""
    parts = []

    if info.base_type == int:
        type_name = "integer"
    elif info.base_type == float:
        type_name = "number"
    elif info.base_type == str:
        type_name = "string"
    else:
        type_name = info.base_type.__name__

    if info.min_value is not None and info.max_value is not None:
        parts.append(f"{type_name} between {info.min_value} and {info.max_value}")
    elif info.min_value is not None:
        parts.append(f"{type_name} >= {info.min_value}")
    elif info.max_value is not None:
        parts.append(f"{type_name} <= {info.max_value}")
    else:
        parts.append(type_name)

    if info.pattern:
        parts.append(f"matching pattern: {info.pattern}")

    if info.min_length is not None:
        parts.append(f"at least {info.min_length} characters")

    if info.max_length is not None:
        parts.append(f"at most {info.max_length} characters")

    return ", ".join(parts) if parts else ""
```

### 3.4 Decorator Layer Updates

#### Update `src/hive/core/types.py`

Add constraint storage to `ParameterInfo`:

```python
from dataclasses import dataclass, field
from typing import Any, Optional, List

@dataclass
class ConstraintMetadata:
    """Constraint information extracted from refinement types."""

    description: str = ""
    """Human-readable constraint description."""

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    validator: Optional[callable] = field(default=None, repr=False)
    """Runtime validation function."""


@dataclass
class ParameterInfo:
    """Information about a command/query parameter."""

    name: str
    type_hint: Any
    default: Any = None
    required: bool = True
    description: str = ""

    # NEW: Constraint metadata from refinement types
    constraints: Optional[ConstraintMetadata] = None
```

#### Update `src/hive/core/decorators.py`

Modify parameter extraction to capture constraints:

```python
from hive.types.introspection import extract_constraints, ConstraintInfo

def _extract_parameters(func: Callable) -> List[ParameterInfo]:
    """Extract parameter information including refinement constraints."""
    sig = inspect.signature(func)
    hints = get_type_hints(func, include_extras=True)  # include_extras for Annotated

    params = []
    for name, param in sig.parameters.items():
        if name == 'ctx':
            continue

        type_hint = hints.get(name, str)

        # Extract constraint metadata from refinement types
        constraint_info = extract_constraints(type_hint)
        constraints = None
        if constraint_info:
            constraints = ConstraintMetadata(
                description=constraint_info.description,
                min_value=constraint_info.min_value,
                max_value=constraint_info.max_value,
                pattern=constraint_info.pattern,
                min_length=constraint_info.min_length,
                max_length=constraint_info.max_length,
                validator=constraint_info.validator,
            )

        params.append(ParameterInfo(
            name=name,
            type_hint=type_hint,
            default=param.default if param.default is not param.empty else None,
            required=param.default is param.empty,
            description="",  # Extracted from docstring elsewhere
            constraints=constraints,
        ))

    return params
```

### 3.5 CLI Generator Updates

#### Update `src/hive/generators/cli.py`

Add validation from constraints:

```python
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation

def _create_wrapper(self, registration: CommandRegistration) -> Callable:
    """Create CLI wrapper with constraint validation."""
    func = registration.func

    # Apply beartype decorator for runtime validation
    validated_func = beartype(func)

    async def wrapper(**kwargs):
        # Convert CLI arguments to proper types
        converted = {}
        for param in registration.parameters:
            value = kwargs.get(param.name)
            if value is not None:
                converted[param.name] = self._convert_value(value, param.type_hint)
            elif param.required:
                raise CommandError(f"Missing required argument: {param.name}")

        # Create execution context and run
        async with ExecutionContext(self._config) as ctx:
            try:
                result = await validated_func(ctx, **converted)
                return result
            except BeartypeCallHintParamViolation as e:
                # Convert beartype errors to user-friendly CommandError
                raise CommandError(self._format_validation_error(e))

    return wrapper


def _format_validation_error(self, error: BeartypeCallHintParamViolation) -> str:
    """Format beartype validation error for CLI output."""
    # Extract parameter name and constraint from error message
    msg = str(error)

    # Make error message user-friendly
    # "parameter 'age' violates constraint: Is[lambda x: x > 0]"
    # becomes: "Invalid value for 'age': must be a positive integer"

    # This is a simplified version - full implementation would parse
    # the error and look up the parameter's ConstraintMetadata
    return f"Validation error: {msg}"
```

---

## 4. Phase 2: Contract Layer

### 4.1 ExecutionContext Invariants

#### Update `src/hive/runtime/context.py`

```python
import deal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession


@deal.inv(lambda self: self._session is not None or self._closed)
@deal.inv(lambda self: not (self._committed and not self._closed))
@deal.inv(lambda self: not (self._rolled_back and self._committed))
class ExecutionContext:
    """
    Execution context for commands with transaction management.

    Invariants:
    - Session is always available unless context is closed
    - Cannot be both committed and still open
    - Cannot be both committed and rolled back
    """

    def __init__(self, config: AppSettings):
        self._config = config
        self._session: Optional[AsyncSession] = None
        self._closed = False
        self._committed = False
        self._rolled_back = False
        self._output = OutputFormatter(OutputMode.TEXT)

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.post(lambda result: result is not None)
    @property
    def db(self) -> AsyncSession:
        """Database session for the current context."""
        return self._session

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.pre(lambda self: not self._committed, message="Already committed")
    @deal.post(lambda self, result: self._committed)
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
        self._committed = True

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.pre(lambda self: not self._rolled_back, message="Already rolled back")
    @deal.post(lambda self, result: self._rolled_back)
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()
        self._rolled_back = True

    async def __aenter__(self) -> 'ExecutionContext':
        """Enter context and initialize session."""
        self._session = await create_session_factory(self._config.database_url)()
        return self

    @deal.ensure(lambda self, *args: self._closed)
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context, commit or rollback based on exception."""
        try:
            if exc_type is None and not self._committed and not self._rolled_back:
                await self.commit()
            elif exc_type is not None and not self._rolled_back:
                await self.rollback()
        finally:
            await self._session.close()
            self._closed = True
```

### 4.2 OutputFormatter Contracts

#### Update `src/hive/runtime/output.py`

```python
import deal
import json
from typing import Any


class OutputFormatter:
    """Format-aware output handler with contracts."""

    @deal.pre(lambda self, data: data is not None)
    @deal.post(lambda result: isinstance(result, str))
    @deal.post(lambda result: len(result) > 0)
    def result(self, data: Any) -> str:
        """Format result data according to output mode."""
        if self._mode == OutputMode.JSON:
            return self._format_json(data)
        elif self._mode == OutputMode.TABLE:
            return self._format_table(data)
        else:
            return self._format_text(data)

    @deal.pre(lambda self, data: data is not None)
    @deal.post(lambda result: self._is_valid_json(result))
    def _format_json(self, data: Any) -> str:
        """Format data as JSON."""
        if hasattr(data, 'model_dump'):
            return json.dumps(data.model_dump(), indent=2, default=str)
        return json.dumps(data, indent=2, default=str)

    def _is_valid_json(self, s: str) -> bool:
        """Validate JSON string."""
        try:
            json.loads(s)
            return True
        except json.JSONDecodeError:
            return False
```

### 4.3 Registry Contracts

#### Update `src/hive/core/registry.py`

```python
import deal
from typing import Optional


class ApplicationRegistry:
    """Registry for application components with contracts."""

    @deal.pre(lambda self, reg: reg.name is not None)
    @deal.pre(lambda self, reg: len(reg.name) > 0)
    @deal.pre(lambda self, reg: reg.func is not None)
    @deal.pre(
        lambda self, reg: reg.name not in self._commands,
        message="Command already registered"
    )
    @deal.ensure(lambda self, reg, result: reg.name in self._commands)
    def register_command(self, reg: CommandRegistration) -> None:
        """Register a command."""
        self._commands[reg.name] = reg

    @deal.pre(lambda self, name: name is not None)
    @deal.pre(lambda self, name: len(name) > 0)
    def get_command(self, name: str) -> Optional[CommandRegistration]:
        """Get a command by name."""
        return self._commands.get(name)

    @deal.post(lambda result: isinstance(result, list))
    def list_commands(self) -> list[CommandRegistration]:
        """List all registered commands."""
        return list(self._commands.values())
```

### 4.4 Contract Utilities for Users

#### `src/hive/contracts/__init__.py`

```python
"""
Contract utilities for Hive commands.

Optional decorators for adding pre/post conditions to commands.
These integrate with deal but provide Hive-specific error handling.

Example:
    from hive import command, App
    from hive.contracts import requires, ensures

    app = App("myapp")

    @command(app)
    @requires(lambda ctx, task_id: task_id > 0, "Task ID must be positive")
    @ensures(lambda ctx, task_id, result: result.id == task_id)
    async def get_task(ctx, task_id: int) -> Task:
        ...
"""

from hive.contracts.decorators import requires, ensures, invariant

__all__ = ["requires", "ensures", "invariant"]
```

#### `src/hive/contracts/decorators.py`

```python
"""Hive-specific contract decorators wrapping deal."""

import deal
from functools import wraps
from typing import Callable, Any
from hive.errors import CommandError


def requires(condition: Callable[..., bool], message: str = "") -> Callable:
    """
    Precondition decorator for Hive commands.

    Like deal.pre but raises CommandError instead of PreContractError,
    ensuring proper CLI exit codes and user-friendly messages.

    Args:
        condition: Lambda that returns True if precondition is met.
                   Receives same arguments as decorated function.
        message: Error message if precondition fails.

    Example:
        @command(app)
        @requires(lambda ctx, user_id: user_id > 0, "User ID must be positive")
        async def get_user(ctx, user_id: int) -> User:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not condition(*args, **kwargs):
                raise CommandError(message or "Precondition failed", exit_code=1)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def ensures(condition: Callable[..., bool], message: str = "") -> Callable:
    """
    Postcondition decorator for Hive commands.

    Like deal.ensure but raises CommandError for Hive integration.

    Args:
        condition: Lambda that returns True if postcondition is met.
                   Receives original arguments plus 'result' keyword.
        message: Error message if postcondition fails.

    Example:
        @command(app)
        @ensures(lambda ctx, task_id, result: result.id == task_id)
        async def get_task(ctx, task_id: int) -> Task:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if not condition(*args, result=result, **kwargs):
                raise CommandError(message or "Postcondition failed", exit_code=70)
            return result
        return wrapper
    return decorator


def invariant(condition: Callable[[Any], bool], message: str = "") -> Callable:
    """
    Class invariant decorator for Hive entities.

    Wraps deal.inv with Hive-specific error handling.

    Example:
        @entity(app)
        @invariant(lambda self: self.balance >= 0, "Balance cannot be negative")
        class Account(SQLModel, table=True):
            balance: float = 0.0
    """
    return deal.inv(condition, message=message)
```

---

## 5. Phase 3: Specification Export

### 5.1 JSON Schema with Constraints

#### `src/hive/generators/schema.py`

```python
"""JSON Schema generation with refinement type constraints."""

from typing import Any, Dict, get_origin, get_args, Annotated
from hive.types.introspection import extract_constraints
from hive.core.registry import ApplicationRegistry


def generate_json_schema(registry: ApplicationRegistry) -> Dict[str, Any]:
    """
    Generate JSON Schema from registry with constraint metadata.

    Refinement types become JSON Schema constraints:
    - PositiveInt -> {"type": "integer", "minimum": 1}
    - Email -> {"type": "string", "pattern": "^...@...$"}
    - NonEmptyStr -> {"type": "string", "minLength": 1}
    """
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": registry.app_name,
        "definitions": {},
        "commands": {},
        "queries": {},
    }

    # Generate command schemas
    for cmd in registry.list_commands():
        schema["commands"][cmd.name] = _generate_command_schema(cmd)

    # Generate query schemas
    for query in registry.list_queries():
        schema["queries"][query.name] = _generate_query_schema(query)

    # Generate entity schemas
    for entity in registry.list_entities():
        schema["definitions"][entity.name] = _generate_entity_schema(entity)

    return schema


def _generate_parameter_schema(param) -> Dict[str, Any]:
    """Generate JSON Schema for a parameter including constraints."""
    schema = {}

    # Get base type
    base_type = _get_base_type(param.type_hint)
    schema["type"] = _python_type_to_json_type(base_type)

    # Add constraint metadata
    if param.constraints:
        if param.constraints.min_value is not None:
            if schema["type"] == "integer":
                schema["minimum"] = int(param.constraints.min_value)
            else:
                schema["minimum"] = param.constraints.min_value

        if param.constraints.max_value is not None:
            if schema["type"] == "integer":
                schema["maximum"] = int(param.constraints.max_value)
            else:
                schema["maximum"] = param.constraints.max_value

        if param.constraints.pattern:
            schema["pattern"] = param.constraints.pattern

        if param.constraints.min_length is not None:
            schema["minLength"] = param.constraints.min_length

        if param.constraints.max_length is not None:
            schema["maxLength"] = param.constraints.max_length

        if param.constraints.description:
            schema["description"] = param.constraints.description

    return schema


def _python_type_to_json_type(python_type: type) -> str:
    """Convert Python type to JSON Schema type."""
    mapping = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return mapping.get(python_type, "string")


def _get_base_type(type_hint: Any) -> type:
    """Extract base type from potentially Annotated type hint."""
    origin = get_origin(type_hint)
    if origin is Annotated:
        args = get_args(type_hint)
        return args[0] if args else str
    return type_hint if isinstance(type_hint, type) else str
```

### 5.2 OpenAPI Extension for REST

When REST API generation is implemented, constraints become OpenAPI specs:

```python
def _generate_openapi_parameter(param) -> Dict[str, Any]:
    """Generate OpenAPI parameter spec with constraints."""
    spec = {
        "name": param.name,
        "in": "query",
        "required": param.required,
        "schema": _generate_parameter_schema(param),
    }

    if param.constraints and param.constraints.description:
        spec["description"] = param.constraints.description

    return spec
```

---

## 6. Phase 4: Testing Utilities

### 6.1 Hypothesis Strategies for Hive Types

#### `src/hive/testing/strategies.py`

```python
"""Hypothesis strategies for Hive refinement types."""

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from typing import Any, get_origin, get_args, Annotated, TypeVar
from hive.types.introspection import extract_constraints

T = TypeVar('T')


def strategy_for_type(type_hint: Any) -> SearchStrategy:
    """
    Generate a Hypothesis strategy that produces valid values for a type.

    Handles:
    - Plain types (int, str, float, bool)
    - Annotated types with beartype constraints
    - Generic types (List[T], Dict[K, V])

    Example:
        from hive.testing import strategy_for_type
        from hive.types import PositiveInt, Email

        @given(x=strategy_for_type(PositiveInt))
        def test_positive(x):
            assert x > 0

        @given(email=strategy_for_type(Email))
        def test_email(email):
            assert "@" in email
    """
    origin = get_origin(type_hint)

    if origin is Annotated:
        return _strategy_for_annotated(type_hint)

    return _strategy_for_plain_type(type_hint)


def _strategy_for_plain_type(type_hint: Any) -> SearchStrategy:
    """Generate strategy for plain (non-Annotated) types."""
    if type_hint == int:
        return st.integers()
    elif type_hint == float:
        return st.floats(allow_nan=False, allow_infinity=False)
    elif type_hint == str:
        return st.text()
    elif type_hint == bool:
        return st.booleans()
    elif type_hint == bytes:
        return st.binary()
    else:
        # Fallback to Hypothesis's from_type
        return st.from_type(type_hint)


def _strategy_for_annotated(type_hint: Any) -> SearchStrategy:
    """Generate strategy for Annotated types with constraints."""
    args = get_args(type_hint)
    base_type = args[0]

    # Get base strategy
    base_strategy = _strategy_for_plain_type(base_type)

    # Extract constraints
    constraints = extract_constraints(type_hint)

    if constraints:
        # Apply numeric bounds
        if base_type in (int, float):
            if constraints.min_value is not None or constraints.max_value is not None:
                min_val = constraints.min_value if constraints.min_value is not None else None
                max_val = constraints.max_value if constraints.max_value is not None else None

                if base_type == int:
                    base_strategy = st.integers(
                        min_value=int(min_val) if min_val else None,
                        max_value=int(max_val) if max_val else None
                    )
                else:
                    base_strategy = st.floats(
                        min_value=min_val,
                        max_value=max_val,
                        allow_nan=False,
                        allow_infinity=False
                    )

        # Apply string pattern (generate matching strings)
        if base_type == str and constraints.pattern:
            base_strategy = st.from_regex(constraints.pattern, fullmatch=True)

        # Apply length constraints
        if constraints.min_length is not None or constraints.max_length is not None:
            if base_type == str:
                base_strategy = st.text(
                    min_size=constraints.min_length or 0,
                    max_size=constraints.max_length or 100
                )

        # Apply validator as filter (fallback for complex constraints)
        if constraints.validator:
            base_strategy = base_strategy.filter(constraints.validator)

    return base_strategy


# Pre-built strategies for common Hive types
positive_integers = st.integers(min_value=1)
non_negative_integers = st.integers(min_value=0)
percentages = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
unit_intervals = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
ports = st.integers(min_value=1, max_value=65535)
non_empty_strings = st.text(min_size=1)
emails = st.emails()  # Hypothesis has built-in email strategy
```

### 6.2 Property Test Generators

#### `src/hive/testing/properties.py`

```python
"""Property test generators for Hive commands."""

from hypothesis import given, settings, HealthCheck
from typing import Callable, Dict, Any
from hive.core.registry import CommandRegistration
from hive.testing.strategies import strategy_for_type


def property_test_command(registration: CommandRegistration) -> Callable:
    """
    Generate a property-based test for a Hive command.

    Creates a Hypothesis test that:
    1. Generates valid inputs based on parameter types
    2. Runs the command
    3. Verifies postconditions (if any)

    Example:
        from hive.testing import property_test_command

        # In your test file
        test_create_user = property_test_command(app.registry.get_command("create_user"))
    """
    # Build strategies for each parameter
    strategies = {}
    for param in registration.parameters:
        strategies[param.name] = strategy_for_type(param.type_hint)

    @given(**strategies)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    async def test_command(**kwargs):
        # Create mock context
        from hive.testing.mocks import MockExecutionContext
        async with MockExecutionContext() as ctx:
            # Run command
            result = await registration.func(ctx, **kwargs)

            # Verify postconditions if defined
            if hasattr(registration, 'postconditions'):
                for postcond in registration.postconditions:
                    assert postcond(ctx, result=result, **kwargs), \
                        f"Postcondition failed: {postcond}"

    test_command.__name__ = f"test_{registration.name}_properties"
    return test_command


def property_test_query(registration) -> Callable:
    """Generate property-based test for a Hive query."""
    # Similar to property_test_command but for queries
    ...
```

### 6.3 deal.cases Integration

#### `src/hive/testing/cases.py`

```python
"""Integration with deal.cases for automatic test generation."""

import deal
from typing import Callable
from hive.core.registry import CommandRegistration


def cases_for_command(registration: CommandRegistration) -> Callable:
    """
    Generate deal.cases test for a Hive command.

    Uses deal's automatic test generation from contracts.
    Requires the command to have @requires/@ensures decorators.

    Example:
        from hive.testing import cases_for_command

        test_get_task = cases_for_command(app.registry.get_command("get_task"))
    """
    return deal.cases(registration.func)


def generate_all_cases(registry) -> Dict[str, Callable]:
    """
    Generate deal.cases tests for all commands with contracts.

    Returns:
        Dictionary mapping command names to test functions.
    """
    tests = {}

    for cmd in registry.list_commands():
        # Check if command has deal contracts
        if _has_contracts(cmd.func):
            tests[f"test_{cmd.name}_contracts"] = deal.cases(cmd.func)

    return tests


def _has_contracts(func: Callable) -> bool:
    """Check if function has deal contracts."""
    return hasattr(func, '__wrapped__') and hasattr(func, '_deal_validators')
```

### 6.4 Mock Utilities

#### `src/hive/testing/mocks.py`

```python
"""Mock utilities for testing Hive commands."""

from typing import Optional, Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


class MockExecutionContext:
    """
    Mock ExecutionContext for testing commands without database.

    Example:
        async with MockExecutionContext() as ctx:
            result = await my_command(ctx, arg1="value")
            assert ctx.db.add.called
    """

    def __init__(self):
        self._session = AsyncMock(spec=AsyncSession)
        self._config = MagicMock()
        self._output = MagicMock()
        self._entities: Dict[str, List[Any]] = {}

    @property
    def db(self) -> AsyncMock:
        return self._session

    @property
    def config(self) -> MagicMock:
        return self._config

    @property
    def output(self) -> MagicMock:
        return self._output

    async def __aenter__(self) -> 'MockExecutionContext':
        return self

    async def __aexit__(self, *args) -> None:
        pass

    def seed(self, entity_type: type, instances: List[Any]) -> None:
        """Seed mock database with test entities."""
        self._entities[entity_type.__name__] = instances

        # Configure session.exec to return seeded data
        async def mock_exec(statement):
            # Simplified mock - real implementation would parse statement
            result = MagicMock()
            result.all.return_value = self._entities.get(
                entity_type.__name__, []
            )
            result.first.return_value = (
                self._entities.get(entity_type.__name__, [None])[0]
            )
            return result

        self._session.exec = mock_exec
```

---

## 7. Migration Strategy

### 7.1 Incremental Adoption

The verification stack can be adopted incrementally:

```
Week 1: Add dependencies, no code changes
        - Add beartype, deal, hypothesis to pyproject.toml
        - All existing code continues to work

Week 2: Add refinement types module
        - Create src/hive/types/ with all refinement types
        - Export from hive.types (optional import for users)
        - Framework code unchanged

Week 3: Enable beartype on framework internals
        - Add @beartype to ExecutionContext, OutputFormatter
        - Run existing tests to verify no regressions

Week 4: Add deal contracts to framework internals
        - Add invariants to ExecutionContext
        - Add pre/post to Registry, generators
        - Run tests, fix any contract violations

Week 5: Update decorator layer
        - Extract constraint metadata from refinement types
        - Store in ParameterInfo.constraints
        - CLI generator uses constraints for validation messages

Week 6: Add testing utilities
        - Create src/hive/testing/ module
        - Add Hypothesis strategies
        - Add property test generators
```

### 7.2 Backward Compatibility

**All changes are additive:**

| Component | Before | After |
|-----------|--------|-------|
| `@command(app)` with `int` | Works | Works (unchanged) |
| `@command(app)` with `PositiveInt` | N/A | Works (new feature) |
| Manual validation in commands | Works | Works (unchanged) |
| Using refinement types | N/A | Optional (new feature) |
| Using contracts | N/A | Optional (new feature) |

**No breaking changes:**
- Existing commands work without modification
- Refinement types are opt-in
- Contracts are opt-in
- Testing utilities are opt-in

### 7.3 Documentation Updates

Add new sections to documentation:

1. **Refinement Types Guide**
   - What refinement types are
   - Available types in hive.types
   - Creating custom refinement types
   - How constraints become CLI validation

2. **Contracts Guide** (Advanced)
   - Using @requires/@ensures
   - Class invariants with @invariant
   - When to use contracts vs refinement types

3. **Testing Guide**
   - Property-based testing with Hypothesis
   - Using strategy_for_type
   - Generating tests with deal.cases

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| beartype breaks with Python 3.12+ | Low | High | Pin version, monitor releases |
| deal overhead too high | Low | Medium | Provide disable() for production |
| Hypothesis tests too slow | Medium | Low | Use profiles (fast/default/thorough) |
| Constraint extraction fragile | Medium | Medium | Fallback to string description |
| Complex Annotated types break introspection | Low | Medium | Test with edge cases |

### 8.2 User Experience Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Learning curve too steep | Medium | Medium | Make all features opt-in |
| Error messages confusing | Medium | High | Custom error formatting |
| Too "academic" feel | Low | Medium | Practical examples in docs |
| Debugging harder with contracts | Low | Low | Clear stack traces |

### 8.3 Maintenance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Three new dependencies | Low | Medium | All are well-maintained |
| Contract testing doubles test complexity | Medium | Medium | Separate test profiles |
| Version conflicts with user deps | Low | High | Wide version ranges |

---

## 9. Dependency Management

### 9.1 Version Constraints

```toml
[project]
dependencies = [
    # Core verification stack
    "beartype>=0.18.0,<1.0.0",    # Stable API since 0.18
    "deal>=4.24.0,<5.0.0",         # Stable API
]

[project.optional-dependencies]
dev = [
    "hypothesis>=6.100.0,<7.0.0",  # Stable API
]

# Optional: Full verification for CI
verification = [
    "hypothesis>=6.100.0",
    "deal[lint]>=4.24.0",          # Includes static linter
]
```

### 9.2 Transitive Dependencies

| Package | Transitive Deps | Notes |
|---------|-----------------|-------|
| beartype | None | Zero dependencies |
| deal | None | Zero runtime deps |
| hypothesis | sortedcontainers, attrs | Well-maintained |

### 9.3 Production Disable Option

```python
# src/hive/config.py
import os

# Disable contracts in production for performance
if os.getenv("HIVE_PRODUCTION") == "1":
    import deal
    deal.disable()

    # Note: beartype cannot be globally disabled,
    # but overhead is ~1-10μs per call (negligible)
```

---

## 10. Success Criteria

### 10.1 Phase 1 Complete When:

- [ ] beartype, deal, hypothesis in pyproject.toml
- [ ] `hive.types` module exists with all refinement types
- [ ] Constraint extraction works for numeric bounds, patterns, lengths
- [ ] CLI generator extracts constraints from ParameterInfo
- [ ] All existing tests pass
- [ ] New tests for refinement type extraction pass

### 10.2 Phase 2 Complete When:

- [ ] ExecutionContext has deal invariants
- [ ] Registry has deal contracts
- [ ] OutputFormatter has deal contracts
- [ ] `hive.contracts` module provides @requires/@ensures
- [ ] Contract violations raise CommandError with proper exit codes
- [ ] All tests pass with contracts enabled

### 10.3 Phase 3 Complete When:

- [ ] JSON Schema export includes constraint metadata
- [ ] OpenAPI export includes constraint metadata (when REST implemented)
- [ ] MCP tool schemas include constraints (when MCP implemented)

### 10.4 Phase 4 Complete When:

- [ ] `hive.testing` module exists
- [ ] strategy_for_type generates valid inputs for all Hive types
- [ ] property_test_command generates working property tests
- [ ] deal.cases integration works
- [ ] Mock utilities work for command testing
- [ ] Documentation complete for all testing utilities

### 10.5 Overall Success Metrics

| Metric | Target |
|--------|--------|
| Test coverage | Maintain >90% |
| Contract violations caught in tests | >50 (indicates contracts finding bugs) |
| Property tests per command | 1-3 automatically generated |
| CLI validation errors from refinements | Clear, actionable messages |
| Performance overhead | <1ms per command execution |
| User adoption of refinement types | Optional but documented |

---

## Appendix A: Example Application

Complete example showing all features integrated:

```python
"""Task management app with full verification stack."""

from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr, Percentage
from hive.contracts import requires, ensures
from sqlmodel import Field
from datetime import datetime

app = App(
    name="tasks",
    version="1.0.0",
    description="Task management with verification",
)


@entity(app)
class Task:
    """A task with progress tracking."""
    id: int | None = Field(default=None, primary_key=True)
    title: NonEmptyStr
    progress: Percentage = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


@command(app, entities=[Task])
@requires(lambda ctx, title: len(title.strip()) > 0, "Title cannot be empty")
@ensures(lambda ctx, title, result: result.title == title)
async def create_task(ctx, title: NonEmptyStr) -> Task:
    """Create a new task."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    await ctx.db.refresh(task)
    return task


@command(app, entities=[Task])
@requires(lambda ctx, task_id, progress: 0 <= progress <= 100, "Progress must be 0-100")
async def update_progress(ctx, task_id: PositiveInt, progress: Percentage) -> Task:
    """Update task progress."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task {task_id} not found")
    task.progress = progress
    await ctx.db.commit()
    return task


@query(app, entities=[Task])
async def list_tasks(ctx, min_progress: Percentage = 0.0) -> list[Task]:
    """List tasks with at least the given progress."""
    from sqlmodel import select
    stmt = select(Task).where(Task.progress >= min_progress)
    result = await ctx.db.exec(stmt)
    return result.all()


# Generated CLI:
#   tasks create-task --title "My Task"
#   tasks update-progress --task-id 1 --progress 50.0
#   tasks list-tasks --min-progress 25.0 --json

# Validation happens automatically:
#   tasks create-task --title ""
#   Error: Title cannot be empty (from @requires)
#
#   tasks update-progress --task-id -1 --progress 50.0
#   Error: task_id must be a positive integer (from PositiveInt)
#
#   tasks update-progress --task-id 1 --progress 150.0
#   Error: progress must be between 0.0 and 100.0 (from Percentage)
```

---

## Appendix B: Test Suite Example

```python
"""Tests for task management app with property-based testing."""

import pytest
from hypothesis import given, settings
from hive.testing import strategy_for_type, property_test_command, MockExecutionContext
from hive.types import PositiveInt, NonEmptyStr, Percentage
from myapp import app, Task, create_task, update_progress


# Automatically generated property test
test_create_task_properties = property_test_command(
    app.registry.get_command("create_task")
)


# Custom property test with strategies
@given(
    title=strategy_for_type(NonEmptyStr),
    progress=strategy_for_type(Percentage)
)
@settings(max_examples=100)
async def test_task_lifecycle(title, progress):
    """Property: Creating and updating a task preserves data."""
    async with MockExecutionContext() as ctx:
        # Create
        task = await create_task(ctx, title=title)
        assert task.title == title
        assert task.progress == 0.0

        # Seed for update
        ctx.seed(Task, [task])

        # Update
        updated = await update_progress(ctx, task_id=task.id, progress=progress)
        assert updated.progress == progress


# Contract-derived tests
from hive.testing import cases_for_command

test_create_task_contracts = cases_for_command(
    app.registry.get_command("create_task")
)

test_update_progress_contracts = cases_for_command(
    app.registry.get_command("update_progress")
)
```

---

*Document Version: 1.0*
*Last Updated: 2025-01-14*
*Status: Proposal for Review*
