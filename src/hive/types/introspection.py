"""Utilities for extracting constraint metadata from refinement types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import inspect
import re
from typing import Annotated, Any, get_args, get_origin


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


def get_base_type(type_hint: Any) -> type:
    """Extract base type from Annotated or return type as-is.

    For `Annotated[int, Is[...]]`, returns `int`.
    For plain types like `str`, returns `str`.

    Args:
        type_hint: A type annotation, possibly Annotated.

    Returns:
        The base type without Annotated wrapper.

    Example:
        >>> from typing import Annotated
        >>> get_base_type(Annotated[int, "constraint"])
        <class 'int'>
        >>> get_base_type(str)
        <class 'str'>
    """
    origin = get_origin(type_hint)
    if origin is Annotated:
        args = get_args(type_hint)
        return args[0] if args else type_hint
    return type_hint


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


def _get_validator_source(validator: Any) -> str | None:
    """
    Extract the original lambda source code from a beartype Is[] validator.

    This uses CPython internals because beartype wraps the user's lambda in its
    own validation machinery. Direct inspect.getsource() returns beartype's wrapper,
    not the original constraint like `lambda x: x > 0`.

    To recover the original source, we inspect the closure cells (`__closure__`)
    of beartype's `_is_valid` function. Closure cells store variables captured from
    enclosing scopes - including the original lambda passed to Is[]. We search
    for callable objects in these cells and extract their source.

    Note: This relies on CPython implementation details and may break if beartype
    changes its internal structure. It's a best-effort optimization for generating
    helpful error messages and Hypothesis strategies.
    """
    try:
        # Try closure variables first - beartype stores the original lambda source there
        if hasattr(validator, "_is_valid"):
            fn = validator._is_valid
            if hasattr(fn, "__closure__") and fn.__closure__:
                candidates = []
                for cell in fn.__closure__:
                    try:
                        val = cell.cell_contents
                        if callable(val):
                            source = inspect.getsource(val)
                            # Check if this looks like our lambda source with constraint
                            if "lambda" in source:
                                candidates.append(source)
                    except (ValueError, TypeError, OSError):
                        # Closure cells may not be inspectable (empty cells raise ValueError)
                        # or may contain non-callable values; skip and try other candidates
                        pass
                # Prefer the source that looks like an actual constraint lambda
                # (contains comparison operators or function calls like re.match)
                for source in candidates:
                    if any(
                        op in source
                        for op in ["<=", ">=", "<", ">", "==", "re.match", "len(", ".is"]
                    ):
                        return source
                # Fall back to first candidate if no constraint-like lambda found
                if candidates:
                    return candidates[0]
        # Fallback to direct getsource
        return inspect.getsource(validator._is_valid)
    except Exception:
        return None


def _extract_numeric_bounds(
    validator: Any,
) -> tuple[float | None, float | None] | None:
    """Extract min/max bounds from a numeric validator."""
    try:
        source = _get_validator_source(validator)
        if source is None:
            return None

        min_val: float | None = None
        max_val: float | None = None

        # Pattern: value <= x <= value (compound comparison) e.g., "1 <= x <= 65535"
        match = re.search(r"(\d+(?:\.\d+)?)\s*<=\s*x\s*<=\s*(\d+(?:\.\d+)?)", source)
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            return (min_val, max_val)

        # Pattern: value <= x (minimum) e.g., "1 <= x"
        match = re.search(r"(\d+(?:\.\d+)?)\s*<=\s*x(?!\s*<=)", source)
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
    except Exception:  # nosec B110
        # Bounds extraction is best-effort; source may be unavailable or unparsable
        pass

    return None


def _extract_string_pattern(validator: Any) -> str | None:
    """Extract regex pattern from a string validator."""
    try:
        source = _get_validator_source(validator)
        if source is None:
            return None

        # Match: re.match(r'pattern', s) or re.match("pattern", s)
        match = re.search(r"re\.match\(r?['\"](.+?)['\"]", source)
        if match:
            return match.group(1)
    except Exception:  # nosec B110
        # Pattern extraction is best-effort; malformed source or complex validators may fail
        pass

    return None


def _extract_length_constraints(
    validator: Any,
) -> tuple[int | None, int | None] | None:
    """Extract length constraints from a validator."""
    try:
        source = _get_validator_source(validator)
        if source is None:
            return None

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
    except Exception:  # nosec B110
        # Length extraction is optional; fall back to no length constraints on failure
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
