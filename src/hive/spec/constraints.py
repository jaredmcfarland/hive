"""Constraint extraction utilities for specification export.

This module provides functions for extracting JSON Schema constraints
from Hive refinement types and ParameterInfo objects.
"""

from __future__ import annotations

from typing import Any

from hive.core.types import ConstraintMetadata, ParameterInfo
from hive.generators.schema import python_type_to_json_schema


def extract_json_schema_constraints(type_hint: Any) -> dict[str, Any]:
    """Extract JSON Schema constraints from a type hint.

    Handles:
    - Basic types (str, int, float, bool)
    - Hive refinement types (PositiveInt, Email, etc.)
    - Annotated types with beartype validators

    Args:
        type_hint: A Python type annotation.

    Returns:
        Dict with JSON Schema type and constraint fields.
    """
    return python_type_to_json_schema(type_hint)


def parameter_to_json_schema(param: ParameterInfo) -> dict[str, Any]:
    """Convert a ParameterInfo to JSON Schema dict.

    Args:
        param: Parameter information from command/query registration.

    Returns:
        Dict suitable for ParameterSchema construction.
    """
    # Get base type schema from the parameter type
    # This already handles refinement types correctly (e.g., PositiveInt -> minimum: 1)
    schema = python_type_to_json_schema(param.type)

    # Build result dict
    result: dict[str, Any] = {
        "name": param.name,
        "type": schema.get("type", "object"),
        "required": not param.has_default,
    }

    # Add default value if present
    if param.has_default:
        result["default"] = param.default

    # Add description from param.help or ConstraintMetadata
    if param.help:
        result["description"] = param.help
    elif param.constraints and param.constraints.description:
        result["description"] = param.constraints.description

    # Copy constraints from the type schema (which has correct handling for
    # exclusive bounds like x > 0 -> minimum: 1)
    for key in ["minimum", "maximum", "minLength", "maxLength", "pattern", "format"]:
        if key in schema:
            result[key] = schema[key]

    # For bare types with explicit ConstraintMetadata, apply constraints
    # only if not already set from the type schema
    if param.constraints:
        _apply_constraint_metadata(result, param.constraints)

    return result


def _apply_constraint_metadata(
    result: dict[str, Any],
    constraints: ConstraintMetadata,
) -> None:
    """Apply ConstraintMetadata to a result dict.

    Only sets values that are not already present in result.
    This allows type schema constraints to take precedence.
    """
    if constraints.min_value is not None and "minimum" not in result:
        result["minimum"] = constraints.min_value

    if constraints.max_value is not None and "maximum" not in result:
        result["maximum"] = constraints.max_value

    if constraints.min_length is not None and "minLength" not in result:
        result["minLength"] = constraints.min_length

    if constraints.max_length is not None and "maxLength" not in result:
        result["maxLength"] = constraints.max_length

    if constraints.pattern and "pattern" not in result:
        result["pattern"] = constraints.pattern
