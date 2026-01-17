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
