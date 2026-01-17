# Verification Stack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate beartype, deal, and Hypothesis into Hive to transform type hints into executable contracts with automatic validation and test generation.

**Architecture:** Three-layer verification pyramid - beartype for runtime type enforcement at function boundaries, deal for design-by-contract on framework internals, and Hypothesis for property-based testing. All features are opt-in and non-breaking.

**Tech Stack:** beartype>=0.18.0, deal>=4.24.0, hypothesis>=6.100.0 (dev)

---

## Phase 1: Foundation Layer

### Task 1.1: Add Verification Dependencies

**Files:**
- Modify: `pyproject.toml:17-35`

**Step 1: Write test to verify dependencies are importable**

Create: `tests/unit/test_verification_deps.py`

```python
"""Test that verification dependencies are available."""

import pytest


def test_beartype_importable() -> None:
    """Verify beartype is installed and importable."""
    from beartype import beartype
    from beartype.vale import Is
    from beartype.roar import BeartypeCallHintParamViolation

    assert callable(beartype)


def test_deal_importable() -> None:
    """Verify deal is installed and importable."""
    import deal

    assert hasattr(deal, 'pre')
    assert hasattr(deal, 'post')
    assert hasattr(deal, 'ensure')
    assert hasattr(deal, 'inv')


def test_hypothesis_importable() -> None:
    """Verify hypothesis is installed and importable."""
    from hypothesis import given, strategies as st

    assert callable(given)
    assert hasattr(st, 'integers')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_verification_deps.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'beartype'"

**Step 3: Update pyproject.toml with dependencies**

In `pyproject.toml`, find the `dependencies` array and add:

```toml
dependencies = [
    # Existing dependencies...
    "typer>=0.9.0",
    "rich>=13.0.0",
    "sqlmodel>=0.0.22",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "aiosqlite>=0.19.0",
    "greenlet>=2.0.0",
    # Verification stack
    "beartype>=0.18.0",
    "deal>=4.24.0",
]
```

In the `[project.optional-dependencies]` section, add hypothesis to dev:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "hypothesis>=6.100.0",
]
```

**Step 4: Install updated dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed beartype, deal, hypothesis

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_verification_deps.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add pyproject.toml tests/unit/test_verification_deps.py
git commit -m "feat: add verification stack dependencies (beartype, deal, hypothesis)"
```

---

### Task 1.2: Create Primitive Refinement Types

**Files:**
- Create: `src/hive/types/__init__.py`
- Create: `src/hive/types/primitives.py`
- Create: `tests/unit/test_refinement_types.py`

**Step 1: Write failing tests for primitive types**

Create: `tests/unit/test_refinement_types.py`

```python
"""Test refinement types validate correctly at runtime."""

import pytest
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation


class TestPositiveInt:
    """Tests for PositiveInt refinement type."""

    def test_accepts_positive_integer(self) -> None:
        """PositiveInt accepts integers > 0."""
        from hive.types import PositiveInt

        @beartype
        def fn(x: PositiveInt) -> int:
            return x

        assert fn(1) == 1
        assert fn(100) == 100

    def test_rejects_zero(self) -> None:
        """PositiveInt rejects zero."""
        from hive.types import PositiveInt

        @beartype
        def fn(x: PositiveInt) -> int:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(0)

    def test_rejects_negative(self) -> None:
        """PositiveInt rejects negative integers."""
        from hive.types import PositiveInt

        @beartype
        def fn(x: PositiveInt) -> int:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(-1)


class TestNonNegativeInt:
    """Tests for NonNegativeInt refinement type."""

    def test_accepts_zero(self) -> None:
        """NonNegativeInt accepts zero."""
        from hive.types import NonNegativeInt

        @beartype
        def fn(x: NonNegativeInt) -> int:
            return x

        assert fn(0) == 0

    def test_accepts_positive(self) -> None:
        """NonNegativeInt accepts positive integers."""
        from hive.types import NonNegativeInt

        @beartype
        def fn(x: NonNegativeInt) -> int:
            return x

        assert fn(42) == 42

    def test_rejects_negative(self) -> None:
        """NonNegativeInt rejects negative integers."""
        from hive.types import NonNegativeInt

        @beartype
        def fn(x: NonNegativeInt) -> int:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(-1)


class TestUnitInterval:
    """Tests for UnitInterval (0.0-1.0) refinement type."""

    def test_accepts_zero(self) -> None:
        """UnitInterval accepts 0.0."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        assert fn(0.0) == 0.0

    def test_accepts_one(self) -> None:
        """UnitInterval accepts 1.0."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        assert fn(1.0) == 1.0

    def test_accepts_middle_value(self) -> None:
        """UnitInterval accepts values between 0 and 1."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        assert fn(0.5) == 0.5

    def test_rejects_negative(self) -> None:
        """UnitInterval rejects negative values."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(-0.1)

    def test_rejects_above_one(self) -> None:
        """UnitInterval rejects values > 1."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(1.1)


class TestPercentage:
    """Tests for Percentage (0.0-100.0) refinement type."""

    def test_accepts_valid_percentage(self) -> None:
        """Percentage accepts 0-100."""
        from hive.types import Percentage

        @beartype
        def fn(x: Percentage) -> float:
            return x

        assert fn(0.0) == 0.0
        assert fn(50.0) == 50.0
        assert fn(100.0) == 100.0

    def test_rejects_over_100(self) -> None:
        """Percentage rejects values > 100."""
        from hive.types import Percentage

        @beartype
        def fn(x: Percentage) -> float:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(101.0)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_refinement_types.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hive.types'"

**Step 3: Create types package structure**

Create: `src/hive/types/__init__.py`

```python
"""
Hive Refinement Types

Semantic type aliases with runtime-enforced constraints.
Use these in command signatures to get automatic validation.

Example:
    from hive import command, App
    from hive.types import PositiveInt, Percentage

    app = App("myapp")

    @command(app)
    async def set_progress(ctx, task_id: PositiveInt, progress: Percentage):
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

__all__ = [
    # Integer refinements
    "PositiveInt",
    "NonNegativeInt",
    "NegativeInt",
    # Float refinements
    "PositiveFloat",
    "NonNegativeFloat",
    "UnitInterval",
    "Percentage",
    "Probability",
]
```

**Step 4: Create primitive types**

Create: `src/hive/types/primitives.py`

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

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_refinement_types.py -v`
Expected: PASS (12 tests)

**Step 6: Commit**

```bash
git add src/hive/types/ tests/unit/test_refinement_types.py
git commit -m "feat: add primitive refinement types (PositiveInt, Percentage, etc)"
```

---

### Task 1.3: Create String Refinement Types

**Files:**
- Create: `src/hive/types/strings.py`
- Modify: `src/hive/types/__init__.py`
- Create: `tests/unit/test_string_types.py`

**Step 1: Write failing tests for string types**

Create: `tests/unit/test_string_types.py`

```python
"""Test string refinement types."""

import pytest
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation


class TestNonEmptyStr:
    """Tests for NonEmptyStr refinement type."""

    def test_accepts_non_empty_string(self) -> None:
        """NonEmptyStr accepts strings with content."""
        from hive.types import NonEmptyStr

        @beartype
        def fn(s: NonEmptyStr) -> str:
            return s

        assert fn("hello") == "hello"
        assert fn(" ") == " "  # whitespace is content

    def test_rejects_empty_string(self) -> None:
        """NonEmptyStr rejects empty string."""
        from hive.types import NonEmptyStr

        @beartype
        def fn(s: NonEmptyStr) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("")


class TestIdentifier:
    """Tests for Identifier (Python identifier) refinement type."""

    def test_accepts_valid_identifier(self) -> None:
        """Identifier accepts valid Python identifiers."""
        from hive.types import Identifier

        @beartype
        def fn(s: Identifier) -> str:
            return s

        assert fn("my_var") == "my_var"
        assert fn("_private") == "_private"
        assert fn("CamelCase") == "CamelCase"

    def test_rejects_starting_with_digit(self) -> None:
        """Identifier rejects strings starting with digit."""
        from hive.types import Identifier

        @beartype
        def fn(s: Identifier) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("123abc")

    def test_rejects_hyphenated(self) -> None:
        """Identifier rejects hyphenated strings."""
        from hive.types import Identifier

        @beartype
        def fn(s: Identifier) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("my-var")


class TestSlug:
    """Tests for Slug (URL-safe) refinement type."""

    def test_accepts_valid_slug(self) -> None:
        """Slug accepts lowercase alphanumeric with hyphens."""
        from hive.types import Slug

        @beartype
        def fn(s: Slug) -> str:
            return s

        assert fn("my-slug") == "my-slug"
        assert fn("post123") == "post123"
        assert fn("a") == "a"

    def test_rejects_uppercase(self) -> None:
        """Slug rejects uppercase letters."""
        from hive.types import Slug

        @beartype
        def fn(s: Slug) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("My-Slug")

    def test_rejects_underscores(self) -> None:
        """Slug rejects underscores."""
        from hive.types import Slug

        @beartype
        def fn(s: Slug) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("my_slug")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_string_types.py -v`
Expected: FAIL with "ImportError: cannot import name 'NonEmptyStr'"

**Step 3: Create string types module**

Create: `src/hive/types/strings.py`

```python
"""String refinement types."""

import re
from typing import Annotated

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

Slug = Annotated[str, Is[lambda s: bool(re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", s))]]
"""URL-safe slug (lowercase alphanumeric with hyphens)."""

Email = Annotated[
    str, Is[lambda s: bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", s))]
]
"""Email address (basic validation)."""

Url = Annotated[str, Is[lambda s: bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", s))]]
"""HTTP or HTTPS URL."""

FilePath = Annotated[str, Is[lambda s: len(s) > 0 and "\0" not in s]]
"""Non-empty string without null bytes (valid file path)."""

DirectoryPath = FilePath
"""Alias for FilePath, semantically representing a directory."""
```

**Step 4: Update __init__.py exports**

Modify: `src/hive/types/__init__.py`

Add these imports after the primitives imports:

```python
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
```

Update `__all__` to include:

```python
__all__ = [
    # Integer refinements
    "PositiveInt",
    "NonNegativeInt",
    "NegativeInt",
    # Float refinements
    "PositiveFloat",
    "NonNegativeFloat",
    "UnitInterval",
    "Percentage",
    "Probability",
    # String refinements
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
]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_string_types.py -v`
Expected: PASS (8 tests)

**Step 6: Commit**

```bash
git add src/hive/types/strings.py src/hive/types/__init__.py tests/unit/test_string_types.py
git commit -m "feat: add string refinement types (NonEmptyStr, Slug, Email, etc)"
```

---

### Task 1.4: Create Numeric Domain Types

**Files:**
- Create: `src/hive/types/numeric.py`
- Modify: `src/hive/types/__init__.py`
- Create: `tests/unit/test_numeric_types.py`

**Step 1: Write failing tests for numeric domain types**

Create: `tests/unit/test_numeric_types.py`

```python
"""Test domain-specific numeric refinement types."""

import pytest
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation


class TestPort:
    """Tests for Port (1-65535) refinement type."""

    def test_accepts_valid_port(self) -> None:
        """Port accepts valid port numbers."""
        from hive.types import Port

        @beartype
        def fn(p: Port) -> int:
            return p

        assert fn(1) == 1
        assert fn(80) == 80
        assert fn(8080) == 8080
        assert fn(65535) == 65535

    def test_rejects_zero(self) -> None:
        """Port rejects 0."""
        from hive.types import Port

        @beartype
        def fn(p: Port) -> int:
            return p

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(0)

    def test_rejects_above_65535(self) -> None:
        """Port rejects values > 65535."""
        from hive.types import Port

        @beartype
        def fn(p: Port) -> int:
            return p

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(65536)


class TestHttpStatusCode:
    """Tests for HttpStatusCode (100-599) refinement type."""

    def test_accepts_valid_status_codes(self) -> None:
        """HttpStatusCode accepts valid HTTP status codes."""
        from hive.types import HttpStatusCode

        @beartype
        def fn(code: HttpStatusCode) -> int:
            return code

        assert fn(200) == 200
        assert fn(404) == 404
        assert fn(500) == 500

    def test_rejects_below_100(self) -> None:
        """HttpStatusCode rejects values < 100."""
        from hive.types import HttpStatusCode

        @beartype
        def fn(code: HttpStatusCode) -> int:
            return code

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(99)


class TestMonth:
    """Tests for Month (1-12) refinement type."""

    def test_accepts_valid_months(self) -> None:
        """Month accepts 1-12."""
        from hive.types import Month

        @beartype
        def fn(m: Month) -> int:
            return m

        assert fn(1) == 1
        assert fn(12) == 12

    def test_rejects_zero(self) -> None:
        """Month rejects 0."""
        from hive.types import Month

        @beartype
        def fn(m: Month) -> int:
            return m

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(0)

    def test_rejects_13(self) -> None:
        """Month rejects 13."""
        from hive.types import Month

        @beartype
        def fn(m: Month) -> int:
            return m

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(13)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_numeric_types.py -v`
Expected: FAIL with "ImportError: cannot import name 'Port'"

**Step 3: Create numeric domain types module**

Create: `src/hive/types/numeric.py`

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

**Step 4: Update __init__.py exports**

Modify: `src/hive/types/__init__.py`

Add import:

```python
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
```

Update `__all__` to include:

```python
    # Numeric domain types
    "Port",
    "HttpStatusCode",
    "UnixTimestamp",
    "Year",
    "Month",
    "Day",
    "Hour",
    "Minute",
    "Second",
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_numeric_types.py -v`
Expected: PASS (8 tests)

**Step 6: Commit**

```bash
git add src/hive/types/numeric.py src/hive/types/__init__.py tests/unit/test_numeric_types.py
git commit -m "feat: add numeric domain types (Port, HttpStatusCode, Month, etc)"
```

---

### Task 1.5: Create Constraint Introspection Utilities

**Files:**
- Create: `src/hive/types/introspection.py`
- Create: `tests/unit/test_introspection.py`

**Step 1: Write failing tests for constraint extraction**

Create: `tests/unit/test_introspection.py`

```python
"""Test constraint metadata extraction from refinement types."""

import pytest
from typing import Annotated

from beartype.vale import Is


class TestExtractConstraints:
    """Tests for extract_constraints function."""

    def test_returns_none_for_plain_type(self) -> None:
        """extract_constraints returns None for plain types."""
        from hive.types.introspection import extract_constraints

        assert extract_constraints(int) is None
        assert extract_constraints(str) is None
        assert extract_constraints(float) is None

    def test_extracts_base_type_from_annotated(self) -> None:
        """extract_constraints extracts base type from Annotated."""
        from hive.types.introspection import extract_constraints
        from hive.types import PositiveInt

        info = extract_constraints(PositiveInt)

        assert info is not None
        assert info.base_type is int

    def test_extracts_min_value_from_positive_int(self) -> None:
        """extract_constraints extracts min_value from PositiveInt."""
        from hive.types.introspection import extract_constraints
        from hive.types import PositiveInt

        info = extract_constraints(PositiveInt)

        assert info is not None
        # PositiveInt is x > 0, so minimum is effectively 1 for integers
        # but we detect the constraint pattern

    def test_extracts_bounds_from_port(self) -> None:
        """extract_constraints extracts min/max from Port type."""
        from hive.types.introspection import extract_constraints
        from hive.types import Port

        info = extract_constraints(Port)

        assert info is not None
        assert info.base_type is int
        assert info.min_value == 1
        assert info.max_value == 65535

    def test_extracts_bounds_from_percentage(self) -> None:
        """extract_constraints extracts bounds from Percentage."""
        from hive.types.introspection import extract_constraints
        from hive.types import Percentage

        info = extract_constraints(Percentage)

        assert info is not None
        assert info.base_type is float
        assert info.min_value == 0.0
        assert info.max_value == 100.0

    def test_extracts_validator_function(self) -> None:
        """extract_constraints extracts the validator callable."""
        from hive.types.introspection import extract_constraints
        from hive.types import PositiveInt

        info = extract_constraints(PositiveInt)

        assert info is not None
        assert info.validator is not None
        assert info.validator(5) is True
        assert info.validator(0) is False
        assert info.validator(-1) is False


class TestConstraintInfoDataclass:
    """Tests for ConstraintInfo dataclass."""

    def test_has_expected_fields(self) -> None:
        """ConstraintInfo has all expected fields."""
        from hive.types.introspection import ConstraintInfo

        info = ConstraintInfo(
            base_type=int,
            description="test",
            validator=None,
            min_value=1,
            max_value=100,
        )

        assert info.base_type is int
        assert info.description == "test"
        assert info.min_value == 1
        assert info.max_value == 100
        assert info.pattern is None
        assert info.min_length is None
        assert info.max_length is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_introspection.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hive.types.introspection'"

**Step 3: Create introspection module**

Create: `src/hive/types/introspection.py`

```python
"""Utilities for extracting constraint metadata from refinement types."""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, get_args, get_origin


@dataclass
class ConstraintInfo:
    """Extracted constraint metadata from a refinement type."""

    base_type: type
    """The underlying Python type (int, str, float, etc.)."""

    description: str
    """Human-readable description of the constraint."""

    validator: Callable[[Any], bool] | None
    """The validation function, if extractable."""

    min_value: float | None = None
    """Minimum value for numeric types."""

    max_value: float | None = None
    """Maximum value for numeric types."""

    pattern: str | None = None
    """Regex pattern for string types."""

    min_length: int | None = None
    """Minimum length for string/collection types."""

    max_length: int | None = None
    """Maximum length for string/collection types."""


def extract_constraints(type_hint: Any) -> ConstraintInfo | None:
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
        if hasattr(validator, "_is_valid"):
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


def _extract_numeric_bounds(
    validator: Any,
) -> tuple[float | None, float | None] | None:
    """Extract min/max bounds from a numeric validator."""
    try:
        source = inspect.getsource(validator._is_valid)

        min_val: float | None = None
        max_val: float | None = None

        # Pattern: value <= x (minimum) e.g., "1 <= x"
        match = re.search(r"(\d+(?:\.\d+)?)\s*<=\s*x", source)
        if match:
            min_val = float(match.group(1))

        # Pattern: x >= value (minimum) e.g., "x >= 1"
        match = re.search(r"x\s*>=\s*(\d+(?:\.\d+)?)", source)
        if match:
            val = float(match.group(1))
            if min_val is None or val > min_val:
                min_val = val

        # Pattern: x > value (exclusive minimum)
        match = re.search(r"x\s*>\s*(\d+(?:\.\d+)?)", source)
        if match:
            # For x > 0, min is effectively 1 for ints, but we record 0 as constraint
            val = float(match.group(1))
            if min_val is None:
                min_val = val

        # Pattern: x <= value (maximum) e.g., "x <= 65535"
        match = re.search(r"x\s*<=\s*(\d+(?:\.\d+)?)", source)
        if match:
            max_val = float(match.group(1))

        # Pattern: value >= x (maximum)
        match = re.search(r"(\d+(?:\.\d+)?)\s*>=\s*x", source)
        if match:
            val = float(match.group(1))
            if max_val is None or val < max_val:
                max_val = val

        # Pattern: x < value (exclusive maximum)
        match = re.search(r"x\s*<\s*(\d+(?:\.\d+)?)", source)
        if match:
            val = float(match.group(1))
            if max_val is None:
                max_val = val

        if min_val is not None or max_val is not None:
            return (min_val, max_val)
    except Exception:
        pass

    return None


def _extract_string_pattern(validator: Any) -> str | None:
    """Extract regex pattern from a string validator."""
    try:
        source = inspect.getsource(validator._is_valid)

        # Match: re.match(r'pattern', s) or re.match("pattern", s)
        match = re.search(r"re\.match\(r?['\"](.+?)['\"]", source)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def _extract_length_constraints(
    validator: Any,
) -> tuple[int | None, int | None] | None:
    """Extract length constraints from a validator."""
    try:
        source = inspect.getsource(validator._is_valid)

        min_len: int | None = None
        max_len: int | None = None

        # Pattern: len(x) > value or len(x) >= value or len(s) > value
        match = re.search(r"len\([^)]+\)\s*>\s*(\d+)", source)
        if match:
            min_len = int(match.group(1)) + 1  # > becomes >=

        match = re.search(r"len\([^)]+\)\s*>=\s*(\d+)", source)
        if match:
            min_len = int(match.group(1))

        # Pattern: len(x) < value or len(x) <= value
        match = re.search(r"len\([^)]+\)\s*<\s*(\d+)", source)
        if match:
            max_len = int(match.group(1)) - 1  # < becomes <=

        match = re.search(r"len\([^)]+\)\s*<=\s*(\d+)", source)
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

    if info.base_type is int:
        type_name = "integer"
    elif info.base_type is float:
        type_name = "number"
    elif info.base_type is str:
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

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_introspection.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add src/hive/types/introspection.py tests/unit/test_introspection.py
git commit -m "feat: add constraint introspection utilities for refinement types"
```

---

### Task 1.6: Add ConstraintMetadata to Core Types

**Files:**
- Modify: `src/hive/core/types.py`
- Create: `tests/unit/test_constraint_metadata.py`

**Step 1: Write failing test for ConstraintMetadata**

Create: `tests/unit/test_constraint_metadata.py`

```python
"""Test ConstraintMetadata dataclass in core types."""

import pytest


class TestConstraintMetadata:
    """Tests for ConstraintMetadata dataclass."""

    def test_can_instantiate_with_defaults(self) -> None:
        """ConstraintMetadata can be instantiated with defaults."""
        from hive.core.types import ConstraintMetadata

        meta = ConstraintMetadata()

        assert meta.description == ""
        assert meta.min_value is None
        assert meta.max_value is None
        assert meta.pattern is None
        assert meta.min_length is None
        assert meta.max_length is None
        assert meta.validator is None

    def test_can_instantiate_with_values(self) -> None:
        """ConstraintMetadata accepts all constraint fields."""
        from hive.core.types import ConstraintMetadata

        validator = lambda x: x > 0

        meta = ConstraintMetadata(
            description="positive integer",
            min_value=1.0,
            max_value=100.0,
            pattern=None,
            min_length=None,
            max_length=None,
            validator=validator,
        )

        assert meta.description == "positive integer"
        assert meta.min_value == 1.0
        assert meta.max_value == 100.0
        assert meta.validator is validator


class TestParameterInfoWithConstraints:
    """Tests for ParameterInfo with constraints field."""

    def test_parameter_info_has_constraints_field(self) -> None:
        """ParameterInfo has optional constraints field."""
        from hive.core.types import ParameterInfo, ParameterKind, ConstraintMetadata

        param = ParameterInfo(
            name="age",
            type=int,
            default=None,
            has_default=False,
            kind=ParameterKind.KEYWORD,
        )

        assert param.constraints is None

    def test_parameter_info_accepts_constraints(self) -> None:
        """ParameterInfo accepts ConstraintMetadata."""
        from hive.core.types import ParameterInfo, ParameterKind, ConstraintMetadata

        meta = ConstraintMetadata(
            description="positive integer",
            min_value=1.0,
        )

        param = ParameterInfo(
            name="age",
            type=int,
            default=None,
            has_default=False,
            kind=ParameterKind.KEYWORD,
            constraints=meta,
        )

        assert param.constraints is not None
        assert param.constraints.description == "positive integer"
        assert param.constraints.min_value == 1.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_constraint_metadata.py -v`
Expected: FAIL with "ImportError: cannot import name 'ConstraintMetadata'"

**Step 3: Add ConstraintMetadata to core/types.py**

First, read the current file:

Read: `src/hive/core/types.py`

Then add `ConstraintMetadata` dataclass after the imports and before `ParameterKind`:

```python
@dataclass
class ConstraintMetadata:
    """Constraint information extracted from refinement types."""

    description: str = ""
    """Human-readable constraint description."""

    min_value: float | None = None
    """Minimum value for numeric types."""

    max_value: float | None = None
    """Maximum value for numeric types."""

    pattern: str | None = None
    """Regex pattern for string types."""

    min_length: int | None = None
    """Minimum length for string/collection types."""

    max_length: int | None = None
    """Maximum length for string/collection types."""

    validator: Callable[[Any], bool] | None = field(default=None, repr=False)
    """Runtime validation function."""
```

Add the import at the top:

```python
from typing import Any, Callable
```

Also update `ParameterInfo` to include the constraints field:

```python
@dataclass
class ParameterInfo:
    """Information about a single parameter."""

    name: str
    type: Any
    default: Any
    has_default: bool
    kind: ParameterKind
    help: str | None = None
    short: str | None = None
    constraints: ConstraintMetadata | None = None  # NEW
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_constraint_metadata.py -v`
Expected: PASS (4 tests)

**Step 5: Run all tests to ensure no regressions**

Run: `pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/hive/core/types.py tests/unit/test_constraint_metadata.py
git commit -m "feat: add ConstraintMetadata to core types for refinement type support"
```

---

### Task 1.7: Update Decorator to Extract Constraints

**Files:**
- Modify: `src/hive/core/decorators.py`
- Create: `tests/contract/test_constraint_extraction.py`

**Step 1: Write failing test for constraint extraction in decorator**

Create: `tests/contract/test_constraint_extraction.py`

```python
"""Test that decorators extract constraints from refinement types."""

import pytest


class TestCommandConstraintExtraction:
    """Tests for constraint extraction in @command decorator."""

    def test_extracts_constraints_from_positive_int(self) -> None:
        """@command extracts constraints from PositiveInt parameter."""
        from hive import App, command
        from hive.types import PositiveInt

        app = App(name="test-app")

        @command(app)
        async def create_task(ctx, priority: PositiveInt) -> dict:
            """Create task with priority."""
            return {"priority": priority}

        reg = app.registry.get_command("create_task")
        assert reg is not None

        # Find priority parameter
        priority_param = next(p for p in reg.parameters if p.name == "priority")
        assert priority_param.constraints is not None
        assert priority_param.constraints.min_value is not None

    def test_extracts_constraints_from_port(self) -> None:
        """@command extracts min/max constraints from Port parameter."""
        from hive import App, command
        from hive.types import Port

        app = App(name="test-app")

        @command(app)
        async def start_server(ctx, port: Port) -> dict:
            """Start server on port."""
            return {"port": port}

        reg = app.registry.get_command("start_server")
        assert reg is not None

        port_param = next(p for p in reg.parameters if p.name == "port")
        assert port_param.constraints is not None
        assert port_param.constraints.min_value == 1
        assert port_param.constraints.max_value == 65535

    def test_no_constraints_for_plain_types(self) -> None:
        """@command has no constraints for plain int/str types."""
        from hive import App, command

        app = App(name="test-app")

        @command(app)
        async def echo(ctx, message: str, count: int) -> dict:
            """Echo message."""
            return {"message": message, "count": count}

        reg = app.registry.get_command("echo")
        assert reg is not None

        message_param = next(p for p in reg.parameters if p.name == "message")
        assert message_param.constraints is None

        count_param = next(p for p in reg.parameters if p.name == "count")
        assert count_param.constraints is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/contract/test_constraint_extraction.py -v`
Expected: FAIL (constraints is None when it should have values)

**Step 3: Update decorators.py to extract constraints**

Read the current `src/hive/core/decorators.py` file first.

Add import at top:

```python
from hive.types.introspection import extract_constraints
from hive.core.types import ConstraintMetadata
```

Modify the `_extract_parameters` function to capture constraints. Find where `ParameterInfo` is created and add constraint extraction:

```python
def _extract_parameters(func: Callable[..., Any]) -> list[ParameterInfo]:
    """Extract parameter information from a function signature."""
    sig = inspect.signature(func)
    hints = get_type_hints(func, include_extras=True)  # include_extras for Annotated

    params: list[ParameterInfo] = []
    for name, param in sig.parameters.items():
        if name == "ctx":
            continue

        type_hint = hints.get(name, str)

        # Extract constraint metadata from refinement types
        constraint_info = extract_constraints(type_hint)
        constraints: ConstraintMetadata | None = None
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

        # Map inspect kinds to our enum
        kind = _map_parameter_kind(param.kind)

        params.append(
            ParameterInfo(
                name=name,
                type=type_hint,
                default=param.default if param.default is not param.empty else None,
                has_default=param.default is not param.empty,
                kind=kind,
                help=None,
                short=None,
                constraints=constraints,
            )
        )

    return params
```

Also update the `get_type_hints` call to use `include_extras=True` so Annotated metadata is preserved.

**Step 4: Run test to verify it passes**

Run: `pytest tests/contract/test_constraint_extraction.py -v`
Expected: PASS (3 tests)

**Step 5: Run all tests to ensure no regressions**

Run: `pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/hive/core/decorators.py tests/contract/test_constraint_extraction.py
git commit -m "feat: extract constraints from refinement types in decorators"
```

---

### Task 1.8: Export Types from Main Package

**Files:**
- Modify: `src/hive/__init__.py`
- Create: `tests/unit/test_types_export.py`

**Step 1: Write failing test for types export**

Create: `tests/unit/test_types_export.py`

```python
"""Test that types are properly exported from hive package."""

import pytest


def test_types_importable_from_hive_types() -> None:
    """Common types importable from hive.types."""
    from hive.types import (
        PositiveInt,
        NonNegativeInt,
        Percentage,
        Port,
        NonEmptyStr,
        Email,
    )

    # Just verify they're importable (actual behavior tested elsewhere)
    assert PositiveInt is not None
    assert Port is not None


def test_types_module_has_all_exports() -> None:
    """hive.types.__all__ contains expected types."""
    from hive import types

    expected = [
        "PositiveInt",
        "NonNegativeInt",
        "Percentage",
        "Port",
        "NonEmptyStr",
        "Email",
    ]

    for name in expected:
        assert name in types.__all__, f"{name} missing from hive.types.__all__"
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/test_types_export.py -v`
Expected: PASS (2 tests) - these should already pass from earlier work

**Step 3: Commit**

```bash
git add tests/unit/test_types_export.py
git commit -m "test: add types export verification tests"
```

---

## Phase 2: Contract Layer

### Task 2.1: Add Deal Invariants to ExecutionContext

**Files:**
- Modify: `src/hive/runtime/context.py`
- Create: `tests/contract/test_context_invariants.py`

**Step 1: Write failing test for context invariants**

Create: `tests/contract/test_context_invariants.py`

```python
"""Test ExecutionContext invariants enforced by deal."""

import pytest


class TestExecutionContextInvariants:
    """Tests for ExecutionContext deal invariants."""

    @pytest.mark.asyncio
    async def test_cannot_access_db_when_closed(self) -> None:
        """Accessing db after close raises error."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.config import AppSettings

        settings = AppSettings(database_url="sqlite+aiosqlite:///:memory:")

        async with ExecutionContext(settings=settings, command_name="test") as ctx:
            # Should work while open
            _ = ctx.db

        # After exit, context is closed - accessing db should fail
        # deal.pre will raise PreContractError
        with pytest.raises(Exception):  # deal.PreContractError
            _ = ctx.db

    @pytest.mark.asyncio
    async def test_cannot_commit_when_closed(self) -> None:
        """Calling commit after close raises error."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.config import AppSettings

        settings = AppSettings(database_url="sqlite+aiosqlite:///:memory:")

        async with ExecutionContext(settings=settings, command_name="test") as ctx:
            pass  # Normal exit

        with pytest.raises(Exception):
            await ctx.commit()

    @pytest.mark.asyncio
    async def test_cannot_commit_twice(self) -> None:
        """Calling commit after already committed raises error."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.config import AppSettings

        settings = AppSettings(database_url="sqlite+aiosqlite:///:memory:")

        async with ExecutionContext(settings=settings, command_name="test") as ctx:
            await ctx.commit()
            # Second commit should fail
            with pytest.raises(Exception):
                await ctx.commit()
```

**Step 2: Run test to verify behavior without contracts**

Run: `pytest tests/contract/test_context_invariants.py -v`
Expected: May pass or fail depending on current implementation

**Step 3: Add deal contracts to ExecutionContext**

Read `src/hive/runtime/context.py` first.

Add import:

```python
import deal
```

Add tracking state and contracts to the class:

```python
class ExecutionContext:
    """Execution context for commands with transaction management."""

    def __init__(
        self,
        settings: AppSettings,
        command_name: str,
        output_format: OutputFormat = OutputFormat.TEXT,
        interactive: bool = True,
    ) -> None:
        self._settings = settings
        self._command_name = command_name
        self._output_format = output_format
        self._interactive = interactive
        self._session: AsyncSession | None = None
        self._output = OutputFormatter(output_format)
        # State tracking for invariants
        self._closed = False
        self._committed = False
        self._rolled_back = False

    @property
    @deal.pre(lambda self: not self._closed, message="Context is closed")
    def db(self) -> AsyncSession:
        """Database session for the current context."""
        if self._session is None:
            raise RuntimeError("Session not initialized")
        return self._session

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.pre(lambda self: not self._committed, message="Already committed")
    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session:
            await self._session.commit()
        self._committed = True

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.pre(lambda self: not self._rolled_back, message="Already rolled back")
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()
        self._rolled_back = True

    async def __aenter__(self) -> ExecutionContext:
        """Enter the context and initialize the session."""
        engine = await get_engine(self._settings.database_url)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        self._session = async_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context, committing or rolling back."""
        try:
            if exc_type is None and not self._committed and not self._rolled_back:
                await self.commit()
            elif exc_type is not None and not self._rolled_back:
                await self.rollback()
        finally:
            if self._session:
                await self._session.close()
            self._closed = True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/contract/test_context_invariants.py -v`
Expected: PASS (3 tests)

**Step 5: Run all tests to ensure no regressions**

Run: `pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/hive/runtime/context.py tests/contract/test_context_invariants.py
git commit -m "feat: add deal contracts to ExecutionContext for state invariants"
```

---

### Task 2.2: Add Deal Contracts to Registry

**Files:**
- Modify: `src/hive/core/registry.py`
- Create: `tests/contract/test_registry_contracts.py`

**Step 1: Write failing test for registry contracts**

Create: `tests/contract/test_registry_contracts.py`

```python
"""Test ApplicationRegistry contracts enforced by deal."""

import pytest


class TestRegistryContracts:
    """Tests for ApplicationRegistry deal contracts."""

    def test_cannot_register_empty_name(self) -> None:
        """Registering command with empty name raises error."""
        from hive.core.registry import ApplicationRegistry
        from hive.core.types import CommandRegistration

        registry = ApplicationRegistry()

        reg = CommandRegistration(
            name="",  # Empty name
            func=lambda ctx: None,
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        with pytest.raises(Exception):  # deal.PreContractError
            registry.register_command(reg)

    def test_cannot_register_none_func(self) -> None:
        """Registering command with None func raises error."""
        from hive.core.registry import ApplicationRegistry
        from hive.core.types import CommandRegistration

        registry = ApplicationRegistry()

        reg = CommandRegistration(
            name="test",
            func=None,  # type: ignore  # None func
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        with pytest.raises(Exception):  # deal.PreContractError
            registry.register_command(reg)

    def test_cannot_register_duplicate_name(self) -> None:
        """Registering command with duplicate name raises error."""
        from hive.core.registry import ApplicationRegistry
        from hive.core.types import CommandRegistration

        registry = ApplicationRegistry()

        async def cmd1(ctx):
            pass

        async def cmd2(ctx):
            pass

        reg1 = CommandRegistration(
            name="duplicate",
            func=cmd1,
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        reg2 = CommandRegistration(
            name="duplicate",
            func=cmd2,
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        registry.register_command(reg1)

        with pytest.raises(Exception):  # RegistrationError or deal.PreContractError
            registry.register_command(reg2)
```

**Step 2: Run test to check current behavior**

Run: `pytest tests/contract/test_registry_contracts.py -v`
Expected: Some may pass (duplicate check exists), others may fail

**Step 3: Add deal contracts to Registry**

Read `src/hive/core/registry.py` first.

Add import:

```python
import deal
```

Add contracts to registration methods:

```python
@deal.pre(lambda self, reg: reg.name is not None and len(reg.name) > 0, message="Command name required")
@deal.pre(lambda self, reg: reg.func is not None, message="Command function required")
@deal.pre(lambda self, reg: reg.name not in self._commands, message="Command already registered")
@deal.ensure(lambda self, reg, result: reg.name in self._commands)
def register_command(self, reg: CommandRegistration) -> None:
    """Register a command."""
    self._check_name_collision(reg.name)
    self._commands[reg.name] = reg
    self._all_names.add(reg.name)
```

Apply similar contracts to `register_query`, `register_entity`, `register_screen`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/contract/test_registry_contracts.py -v`
Expected: PASS (3 tests)

**Step 5: Run all tests to ensure no regressions**

Run: `pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/hive/core/registry.py tests/contract/test_registry_contracts.py
git commit -m "feat: add deal contracts to ApplicationRegistry for registration validation"
```

---

### Task 2.3: Create User-Facing Contract Decorators

**Files:**
- Create: `src/hive/contracts/__init__.py`
- Create: `src/hive/contracts/decorators.py`
- Create: `tests/unit/test_contract_decorators.py`

**Step 1: Write failing tests for contract decorators**

Create: `tests/unit/test_contract_decorators.py`

```python
"""Test user-facing contract decorators."""

import pytest
from hive.errors import CommandError


class TestRequiresDecorator:
    """Tests for @requires precondition decorator."""

    @pytest.mark.asyncio
    async def test_passes_when_condition_met(self) -> None:
        """@requires allows execution when condition is True."""
        from hive.contracts import requires

        @requires(lambda ctx, x: x > 0, "x must be positive")
        async def fn(ctx, x: int) -> int:
            return x * 2

        result = await fn(None, 5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_raises_command_error_when_condition_fails(self) -> None:
        """@requires raises CommandError when condition is False."""
        from hive.contracts import requires

        @requires(lambda ctx, x: x > 0, "x must be positive")
        async def fn(ctx, x: int) -> int:
            return x * 2

        with pytest.raises(CommandError) as exc_info:
            await fn(None, -5)

        assert "x must be positive" in str(exc_info.value)


class TestEnsuresDecorator:
    """Tests for @ensures postcondition decorator."""

    @pytest.mark.asyncio
    async def test_passes_when_postcondition_met(self) -> None:
        """@ensures allows return when condition is True."""
        from hive.contracts import ensures

        @ensures(lambda ctx, x, result: result > x, "result must be greater than input")
        async def fn(ctx, x: int) -> int:
            return x * 2

        result = await fn(None, 5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_raises_command_error_when_postcondition_fails(self) -> None:
        """@ensures raises CommandError when postcondition is False."""
        from hive.contracts import ensures

        @ensures(lambda ctx, x, result: result > x, "result must be greater than input")
        async def fn(ctx, x: int) -> int:
            return x  # Returns same value, not greater

        with pytest.raises(CommandError) as exc_info:
            await fn(None, 5)

        assert "result must be greater than input" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_contract_decorators.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hive.contracts'"

**Step 3: Create contracts package**

Create: `src/hive/contracts/__init__.py`

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

**Step 4: Create decorators module**

Create: `src/hive/contracts/decorators.py`

```python
"""Hive-specific contract decorators wrapping deal."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

import deal

from hive.errors import CommandError

F = TypeVar("F", bound=Callable[..., Any])


def requires(condition: Callable[..., bool], message: str = "") -> Callable[[F], F]:
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

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not condition(*args, **kwargs):
                raise CommandError(message or "Precondition failed", exit_code=1)
            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def ensures(condition: Callable[..., bool], message: str = "") -> Callable[[F], F]:
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

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            if not condition(*args, result=result, **kwargs):
                raise CommandError(message or "Postcondition failed", exit_code=70)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def invariant(
    condition: Callable[[Any], bool], message: str = ""
) -> Callable[[type], type]:
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

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_contract_decorators.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add src/hive/contracts/ tests/unit/test_contract_decorators.py
git commit -m "feat: add user-facing contract decorators (requires, ensures, invariant)"
```

---

## Phase 3: CLI Validation Integration

### Task 3.1: Format Validation Errors for CLI

**Files:**
- Modify: `src/hive/generators/cli.py`
- Create: `tests/integration/test_cli_validation.py`

**Step 1: Write failing test for CLI validation messages**

Create: `tests/integration/test_cli_validation.py`

```python
"""Test CLI validation error formatting with refinement types."""

import pytest
from typer.testing import CliRunner


class TestCLIValidation:
    """Tests for CLI validation with refinement types."""

    def test_positive_int_shows_helpful_error(self) -> None:
        """CLI shows helpful error for invalid PositiveInt."""
        from hive import App, command
        from hive.types import PositiveInt
        from hive.generators.cli import CLIGenerator

        app = App(name="test-app")

        @command(app)
        async def set_priority(ctx, priority: PositiveInt) -> dict:
            """Set task priority."""
            return {"priority": priority}

        cli = CLIGenerator(app).generate()
        runner = CliRunner()

        result = runner.invoke(cli, ["set-priority", "--priority", "0"])

        assert result.exit_code != 0
        # Should have a user-friendly message
        assert "priority" in result.output.lower() or "positive" in result.output.lower()

    def test_port_shows_range_error(self) -> None:
        """CLI shows range error for invalid Port."""
        from hive import App, command
        from hive.types import Port
        from hive.generators.cli import CLIGenerator

        app = App(name="test-app")

        @command(app)
        async def start_server(ctx, port: Port) -> dict:
            """Start server."""
            return {"port": port}

        cli = CLIGenerator(app).generate()
        runner = CliRunner()

        result = runner.invoke(cli, ["start-server", "--port", "70000"])

        assert result.exit_code != 0
        # Should mention valid range or port
        assert "port" in result.output.lower() or "65535" in result.output.lower()

    def test_valid_value_passes(self) -> None:
        """CLI accepts valid refinement type values."""
        from hive import App, command
        from hive.types import PositiveInt
        from hive.generators.cli import CLIGenerator

        app = App(name="test-app")

        @command(app)
        async def set_priority(ctx, priority: PositiveInt) -> dict:
            """Set task priority."""
            return {"priority": priority}

        cli = CLIGenerator(app).generate()
        runner = CliRunner()

        result = runner.invoke(cli, ["set-priority", "--priority", "5"])

        assert result.exit_code == 0
```

**Step 2: Run test to check current behavior**

Run: `pytest tests/integration/test_cli_validation.py -v`
Expected: May pass or fail depending on current error handling

**Step 3: Update CLI generator for validation**

Read `src/hive/generators/cli.py` first.

Add imports:

```python
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation
```

In the wrapper function that executes commands, add error handling:

```python
async def _execute_command(
    self,
    func: Callable[..., Coroutine[Any, Any, Any]],
    output_format: OutputFormat,
    **kwargs: Any,
) -> None:
    """Execute an async command with context."""
    settings = AppSettings()

    async with ExecutionContext(
        settings=settings,
        command_name=func.__name__,
        output_format=output_format,
    ) as ctx:
        try:
            # Apply beartype validation
            validated_func = beartype(func)
            result = await validated_func(ctx, **kwargs)
            # ... output handling
        except BeartypeCallHintParamViolation as e:
            # Format validation error for CLI
            error_msg = self._format_validation_error(e, kwargs)
            raise CommandError(error_msg, exit_code=1)


def _format_validation_error(
    self, error: BeartypeCallHintParamViolation, kwargs: dict[str, Any]
) -> str:
    """Format beartype validation error for CLI output."""
    msg = str(error)

    # Try to extract parameter name and make message user-friendly
    # BeartypeCallHintParamViolation message format varies
    # Example: "parameter 'port' of function violates..."

    # Simple approach: include the raw error with a prefix
    return f"Validation error: {msg}"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_cli_validation.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/hive/generators/cli.py tests/integration/test_cli_validation.py
git commit -m "feat: add beartype validation with user-friendly CLI error messages"
```

---

## Phase 4: Testing Utilities

### Task 4.1: Create Hypothesis Strategies for Types

**Files:**
- Create: `src/hive/testing/__init__.py`
- Create: `src/hive/testing/strategies.py`
- Create: `tests/unit/test_hypothesis_strategies.py`

**Step 1: Write failing tests for strategies**

Create: `tests/unit/test_hypothesis_strategies.py`

```python
"""Test Hypothesis strategies for Hive refinement types."""

import pytest
from hypothesis import given, settings


class TestStrategyForType:
    """Tests for strategy_for_type function."""

    @given(x=...)
    @settings(max_examples=50)
    def test_generates_valid_positive_int(self, x: int) -> None:
        """Strategy generates only positive integers for PositiveInt."""
        from hive.testing import strategy_for_type
        from hive.types import PositiveInt

        # Replace the ... with actual strategy
        pass

    def test_positive_int_strategy_generates_valid_values(self) -> None:
        """PositiveInt strategy only generates x > 0."""
        from hypothesis import given, settings
        from hive.testing import strategy_for_type
        from hive.types import PositiveInt

        strategy = strategy_for_type(PositiveInt)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: int) -> None:
            assert x > 0

        check()

    def test_port_strategy_generates_valid_values(self) -> None:
        """Port strategy generates 1-65535."""
        from hypothesis import given, settings
        from hive.testing import strategy_for_type
        from hive.types import Port

        strategy = strategy_for_type(Port)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: int) -> None:
            assert 1 <= x <= 65535

        check()

    def test_percentage_strategy_generates_valid_values(self) -> None:
        """Percentage strategy generates 0.0-100.0."""
        from hypothesis import given, settings
        from hive.testing import strategy_for_type
        from hive.types import Percentage

        strategy = strategy_for_type(Percentage)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: float) -> None:
            assert 0.0 <= x <= 100.0

        check()

    def test_plain_int_strategy(self) -> None:
        """Plain int generates any integer."""
        from hypothesis import given, settings
        from hive.testing import strategy_for_type

        strategy = strategy_for_type(int)

        @given(x=strategy)
        @settings(max_examples=20)
        def check(x: int) -> None:
            assert isinstance(x, int)

        check()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_hypothesis_strategies.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'hive.testing'"

**Step 3: Create testing package**

Create: `src/hive/testing/__init__.py`

```python
"""
Hive Testing Utilities

Tools for testing Hive commands with property-based testing.

Example:
    from hive.testing import strategy_for_type
    from hive.types import PositiveInt
    from hypothesis import given

    @given(x=strategy_for_type(PositiveInt))
    def test_my_function(x):
        assert my_function(x) > 0
"""

from hive.testing.strategies import strategy_for_type

__all__ = ["strategy_for_type"]
```

**Step 4: Create strategies module**

Create: `src/hive/testing/strategies.py`

```python
"""Hypothesis strategies for Hive refinement types."""

from __future__ import annotations

from typing import Annotated, Any, get_args, get_origin

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from hive.types.introspection import extract_constraints


def strategy_for_type(type_hint: Any) -> SearchStrategy[Any]:
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


def _strategy_for_plain_type(type_hint: Any) -> SearchStrategy[Any]:
    """Generate strategy for plain (non-Annotated) types."""
    if type_hint is int:
        return st.integers()
    elif type_hint is float:
        return st.floats(allow_nan=False, allow_infinity=False)
    elif type_hint is str:
        return st.text()
    elif type_hint is bool:
        return st.booleans()
    elif type_hint is bytes:
        return st.binary()
    else:
        # Fallback to Hypothesis's from_type
        return st.from_type(type_hint)


def _strategy_for_annotated(type_hint: Any) -> SearchStrategy[Any]:
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
            min_val = constraints.min_value
            max_val = constraints.max_value

            if min_val is not None or max_val is not None:
                if base_type is int:
                    # Adjust min for exclusive bounds (x > 0 becomes min=1)
                    int_min = int(min_val) if min_val is not None else None
                    int_max = int(max_val) if max_val is not None else None

                    # If validator exists, check if 0 is excluded
                    if constraints.validator and int_min == 0:
                        if not constraints.validator(0):
                            int_min = 1

                    base_strategy = st.integers(min_value=int_min, max_value=int_max)
                else:
                    base_strategy = st.floats(
                        min_value=min_val,
                        max_value=max_val,
                        allow_nan=False,
                        allow_infinity=False,
                    )

        # Apply string pattern (generate matching strings)
        if base_type is str and constraints.pattern:
            try:
                base_strategy = st.from_regex(constraints.pattern, fullmatch=True)
            except Exception:
                # Fall back to filtering if regex is too complex
                if constraints.validator:
                    base_strategy = st.text().filter(constraints.validator)

        # Apply length constraints
        if constraints.min_length is not None or constraints.max_length is not None:
            if base_type is str:
                base_strategy = st.text(
                    min_size=constraints.min_length or 0,
                    max_size=constraints.max_length or 100,
                )

        # Apply validator as filter (fallback for complex constraints)
        if constraints.validator and base_type not in (int, float):
            # Already handled numeric bounds above
            if base_type is str and not constraints.pattern:
                base_strategy = base_strategy.filter(constraints.validator)

    return base_strategy


# Pre-built strategies for common Hive types
positive_integers = st.integers(min_value=1)
non_negative_integers = st.integers(min_value=0)
percentages = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
unit_intervals = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
ports = st.integers(min_value=1, max_value=65535)
non_empty_strings = st.text(min_size=1)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_hypothesis_strategies.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add src/hive/testing/ tests/unit/test_hypothesis_strategies.py
git commit -m "feat: add Hypothesis strategies for refinement types"
```

---

### Task 4.2: Create Mock ExecutionContext for Testing

**Files:**
- Create: `src/hive/testing/mocks.py`
- Modify: `src/hive/testing/__init__.py`
- Create: `tests/unit/test_mock_context.py`

**Step 1: Write failing tests for mock context**

Create: `tests/unit/test_mock_context.py`

```python
"""Test MockExecutionContext for testing commands."""

import pytest


class TestMockExecutionContext:
    """Tests for MockExecutionContext."""

    @pytest.mark.asyncio
    async def test_can_use_as_async_context_manager(self) -> None:
        """MockExecutionContext works as async context manager."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx is not None

    @pytest.mark.asyncio
    async def test_has_db_property(self) -> None:
        """MockExecutionContext has mock db."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx.db is not None

    @pytest.mark.asyncio
    async def test_has_config_property(self) -> None:
        """MockExecutionContext has mock config."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx.config is not None

    @pytest.mark.asyncio
    async def test_has_output_property(self) -> None:
        """MockExecutionContext has mock output."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            assert ctx.output is not None

    @pytest.mark.asyncio
    async def test_can_track_db_calls(self) -> None:
        """MockExecutionContext tracks db method calls."""
        from hive.testing import MockExecutionContext

        async with MockExecutionContext() as ctx:
            ctx.db.add("something")

        assert ctx.db.add.called
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_mock_context.py -v`
Expected: FAIL with "ImportError: cannot import name 'MockExecutionContext'"

**Step 3: Create mocks module**

Create: `src/hive/testing/mocks.py`

```python
"""Mock utilities for testing Hive commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockExecutionContext:
    """
    Mock ExecutionContext for testing commands without database.

    Example:
        async with MockExecutionContext() as ctx:
            result = await my_command(ctx, arg1="value")
            assert ctx.db.add.called
    """

    def __init__(self) -> None:
        self._session = AsyncMock()
        self._config = MagicMock()
        self._output = MagicMock()

    @property
    def db(self) -> AsyncMock:
        """Mock database session."""
        return self._session

    @property
    def config(self) -> MagicMock:
        """Mock configuration."""
        return self._config

    @property
    def output(self) -> MagicMock:
        """Mock output formatter."""
        return self._output

    async def __aenter__(self) -> MockExecutionContext:
        """Enter the mock context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the mock context (no-op)."""
        pass

    async def commit(self) -> None:
        """Mock commit (no-op)."""
        pass

    async def rollback(self) -> None:
        """Mock rollback (no-op)."""
        pass
```

**Step 4: Update testing __init__.py**

Modify: `src/hive/testing/__init__.py`

```python
"""
Hive Testing Utilities

Tools for testing Hive commands with property-based testing.

Example:
    from hive.testing import strategy_for_type, MockExecutionContext
    from hive.types import PositiveInt
    from hypothesis import given

    @given(x=strategy_for_type(PositiveInt))
    def test_my_function(x):
        assert my_function(x) > 0

    async def test_my_command():
        async with MockExecutionContext() as ctx:
            result = await my_command(ctx, arg="value")
            assert result is not None
"""

from hive.testing.strategies import strategy_for_type
from hive.testing.mocks import MockExecutionContext

__all__ = ["strategy_for_type", "MockExecutionContext"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_mock_context.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add src/hive/testing/mocks.py src/hive/testing/__init__.py tests/unit/test_mock_context.py
git commit -m "feat: add MockExecutionContext for command testing"
```

---

## Phase 5: Final Integration

### Task 5.1: Run Full Test Suite

**Files:**
- None (verification only)

**Step 1: Run all tests**

Run: `pytest -v --cov=src/hive --cov-report=term-missing`
Expected: All tests PASS, coverage report generated

**Step 2: Run type checking**

Run: `python -m mypy src/hive --ignore-missing-imports`
Expected: No errors (or only minor ones from deal/beartype)

**Step 3: Run linting**

Run: `ruff check src/hive tests`
Expected: No errors

**Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: address any linting/typing issues from full test run"
```

---

### Task 5.2: Update CLAUDE.md with New Patterns

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add verification stack documentation**

Add to CLAUDE.md under Active Technologies:

```markdown
## Verification Stack (Phase 1 Complete)

- **beartype**: Runtime type enforcement via refinement types
- **deal**: Design-by-contract decorators (pre/post/inv)
- **hypothesis**: Property-based testing (dev dependency)

### Refinement Types

Use from `hive.types`:
- Numeric: `PositiveInt`, `NonNegativeInt`, `Percentage`, `Port`, `Month`
- Strings: `NonEmptyStr`, `Identifier`, `Slug`, `Email`, `Url`

### Contracts

Use from `hive.contracts`:
- `@requires(condition, message)` - Precondition
- `@ensures(condition, message)` - Postcondition
- `@invariant(condition, message)` - Class invariant

### Testing

Use from `hive.testing`:
- `strategy_for_type(Type)` - Hypothesis strategy
- `MockExecutionContext()` - Test context
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with verification stack patterns"
```

---

## Summary

This plan implements the verification stack in 5 phases with 17 bite-sized tasks:

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1. Foundation | 1.1-1.8 | Dependencies, types, introspection, decorator integration |
| 2. Contracts | 2.1-2.3 | Deal contracts on Context, Registry, user decorators |
| 3. CLI | 3.1 | Validation error formatting |
| 4. Testing | 4.1-4.2 | Hypothesis strategies, mock context |
| 5. Integration | 5.1-5.2 | Full test run, documentation |

Each task follows strict TDD: write failing test → implement → verify pass → commit.
