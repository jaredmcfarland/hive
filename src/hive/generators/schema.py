"""JSON Schema generation for Hive framework.

This module provides utilities for generating JSON Schema (Draft 2020-12)
from Pydantic models and Python types, with support for Hive refinement types.

The HiveSchemaGenerator extends Pydantic's built-in schema generation to:
1. Always include the $schema dialect URI
2. Map Hive refinement types to JSON Schema constraints
3. Generate schemas suitable for cross-language consumption
"""

from __future__ import annotations

from datetime import date, datetime
import types
from typing import TYPE_CHECKING, Annotated, Any, Union, get_args, get_origin, override
from uuid import UUID

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode

from hive.types.introspection import extract_constraints

if TYPE_CHECKING:
    from pydantic_core import CoreSchema


# =============================================================================
# Type Mapping Constants
# =============================================================================

# JSON Schema dialect for Draft 2020-12
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# Mapping from Python types to JSON Schema types
_BASIC_TYPE_MAP: dict[type, dict[str, Any]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    type(None): {"type": "null"},
}

# Mapping from Python types to JSON Schema format
_FORMAT_TYPE_MAP: dict[type, dict[str, Any]] = {
    datetime: {"type": "string", "format": "date-time"},
    date: {"type": "string", "format": "date"},
    UUID: {"type": "string", "format": "uuid"},
}

# Known Hive refinement type names and their schema mappings
# These are used when we can identify the type by name
_REFINEMENT_TYPE_SCHEMAS: dict[str, dict[str, Any]] = {
    "PositiveInt": {"type": "integer", "minimum": 1},
    "NonNegativeInt": {"type": "integer", "minimum": 0},
    "NegativeInt": {"type": "integer", "maximum": -1},
    "PositiveFloat": {"type": "number", "exclusiveMinimum": 0},
    "NonNegativeFloat": {"type": "number", "minimum": 0},
    "UnitInterval": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "Percentage": {"type": "number", "minimum": 0, "maximum": 100},
    "Probability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "Port": {"type": "integer", "minimum": 1, "maximum": 65535},
    "HttpStatusCode": {"type": "integer", "minimum": 100, "maximum": 599},
    "Year": {"type": "integer", "minimum": 1, "maximum": 9999},
    "Month": {"type": "integer", "minimum": 1, "maximum": 12},
    "Day": {"type": "integer", "minimum": 1, "maximum": 31},
    "Hour": {"type": "integer", "minimum": 0, "maximum": 23},
    "Minute": {"type": "integer", "minimum": 0, "maximum": 59},
    "Second": {"type": "integer", "minimum": 0, "maximum": 59},
    "NonEmptyStr": {"type": "string", "minLength": 1},
    "TrimmedStr": {"type": "string"},
    "Identifier": {"type": "string", "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$"},
    "Slug": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
    "Email": {"type": "string", "format": "email"},
    "Url": {"type": "string", "format": "uri"},
    "FilePath": {"type": "string"},
}


# =============================================================================
# Schema Generation Utilities
# =============================================================================


def python_type_to_json_schema(type_hint: Any) -> dict[str, Any]:  # noqa: PLR0911
    """Convert a Python type hint to JSON Schema.

    Handles:
    - Basic types (str, int, float, bool, None)
    - Date/time types (datetime, date, UUID)
    - Collection types (list, dict)
    - Optional/Union types
    - Hive refinement types with constraint extraction

    Args:
        type_hint: A Python type annotation.

    Returns:
        A JSON Schema dict representing the type.
    """
    # Handle None type
    if type_hint is type(None):
        return {"type": "null"}

    # Handle basic types
    if type_hint in _BASIC_TYPE_MAP:
        return _BASIC_TYPE_MAP[type_hint].copy()

    # Handle format types
    if type_hint in _FORMAT_TYPE_MAP:
        return _FORMAT_TYPE_MAP[type_hint].copy()

    # Get the origin for generic types
    origin = get_origin(type_hint)

    # Handle Annotated types (including refinement types)
    if origin is Annotated:
        return _handle_annotated_type(type_hint)

    # Handle Optional (Union with None) - both typing.Union and types.UnionType
    if origin is Union or isinstance(type_hint, types.UnionType):
        return _handle_union_type(type_hint)

    # Handle list types
    if origin is list:
        args = get_args(type_hint)
        item_schema = python_type_to_json_schema(args[0]) if args else {}
        return {"type": "array", "items": item_schema}

    # Handle dict types
    if origin is dict:
        args = get_args(type_hint)
        value_schema = python_type_to_json_schema(args[1]) if len(args) > 1 else {}
        return {"type": "object", "additionalProperties": value_schema}

    # Handle Pydantic models
    if isinstance(type_hint, type) and issubclass(type_hint, BaseModel):
        return {"$ref": f"#/$defs/{type_hint.__name__}"}

    # Check if this is a known refinement type by name
    type_name = getattr(type_hint, "__name__", str(type_hint))
    if type_name in _REFINEMENT_TYPE_SCHEMAS:
        return _REFINEMENT_TYPE_SCHEMAS[type_name].copy()

    # Fallback: return object type for unknown types
    return {"type": "object"}


def _handle_annotated_type(type_hint: Any) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Handle Annotated types, including Hive refinement types."""
    # First, check if this type has a __name__ that matches a known refinement type
    # This handles type aliases like Email = Annotated[str, Is[...]]
    type_repr = repr(type_hint)
    for type_name, schema in _REFINEMENT_TYPE_SCHEMAS.items():
        # Check if the type representation indicates this is a known type
        if f"hive.types.strings.{type_name}" in type_repr:
            return schema.copy()
        if f"hive.types.numeric.{type_name}" in type_repr:
            return schema.copy()

    args = get_args(type_hint)
    if not args:
        return {"type": "object"}

    base_type = args[0]

    # Try to extract constraints from the type
    constraints = extract_constraints(type_hint)

    if constraints:
        # Build schema from base type
        if constraints.base_type in _BASIC_TYPE_MAP:
            schema = _BASIC_TYPE_MAP[constraints.base_type].copy()
        elif constraints.base_type in _FORMAT_TYPE_MAP:
            schema = _FORMAT_TYPE_MAP[constraints.base_type].copy()
        else:
            schema = python_type_to_json_schema(constraints.base_type)

        # Add constraints
        if constraints.min_value is not None:
            # For x > 0, min_value is 0, but we want minimum: 1 for PositiveInt
            # Check if this is an exclusive minimum
            if constraints.min_value == 0 and schema.get("type") == "integer":
                schema["minimum"] = 1
            else:
                schema["minimum"] = constraints.min_value

        if constraints.max_value is not None:
            schema["maximum"] = constraints.max_value

        if constraints.min_length is not None:
            schema["minLength"] = constraints.min_length

        if constraints.max_length is not None:
            schema["maxLength"] = constraints.max_length

        if constraints.pattern:
            # Check if the pattern indicates a known format type
            if "email" in constraints.pattern.lower() or "@" in constraints.pattern:
                schema["format"] = "email"
            elif "http" in constraints.pattern.lower():
                schema["format"] = "uri"
            else:
                schema["pattern"] = constraints.pattern

        return schema

    # No constraints extracted, just return the base type schema
    return python_type_to_json_schema(base_type)


def _handle_union_type(type_hint: Any) -> dict[str, Any]:
    """Handle Union types including Optional."""
    args = get_args(type_hint)
    if not args:
        return {"type": "object"}

    # Check if this is Optional (Union with None)
    non_none_args = [a for a in args if a is not type(None)]
    has_none = len(non_none_args) < len(args)

    if len(non_none_args) == 1:
        # Optional[T] case
        base_schema = python_type_to_json_schema(non_none_args[0])
        if has_none:
            return {"anyOf": [base_schema, {"type": "null"}]}
        return base_schema

    # Multiple non-None types: create anyOf
    schemas = [python_type_to_json_schema(arg) for arg in args]
    return {"anyOf": schemas}


# =============================================================================
# Hive Schema Generator
# =============================================================================


class HiveSchemaGenerator(GenerateJsonSchema):
    """Custom JSON Schema generator for Hive applications.

    Extends Pydantic's GenerateJsonSchema to:
    1. Always include $schema dialect URI (Draft 2020-12)
    2. Support Hive refinement type constraints
    3. Generate schemas suitable for cross-language consumption
    """

    def __init__(
        self,
        by_alias: bool = True,
        ref_template: str = "#/$defs/{model}",
    ) -> None:
        """Initialize the schema generator.

        Args:
            by_alias: Use field aliases in generated schema.
            ref_template: Template for $ref URIs.
        """
        super().__init__(by_alias=by_alias, ref_template=ref_template)

    def generate_schema(
        self,
        model: type[BaseModel],
        mode: JsonSchemaMode = "validation",
    ) -> dict[str, Any]:
        """Generate JSON Schema for a Pydantic model.

        Args:
            model: A Pydantic model class.
            mode: Schema mode ('validation' or 'serialization').

        Returns:
            A JSON Schema dict with $schema dialect included.
        """
        schema = model.model_json_schema(
            by_alias=True,
            ref_template=self.ref_template,
            mode=mode,
        )

        # Ensure $schema is set to Draft 2020-12
        schema["$schema"] = SCHEMA_DIALECT

        return schema

    @override
    def generate(
        self,
        schema: CoreSchema,
        mode: JsonSchemaMode = "validation",
    ) -> dict[str, Any]:
        """Generate JSON Schema from a CoreSchema.

        This method is called by Pydantic internally. We override to ensure
        the $schema dialect is always included.

        Args:
            schema: A Pydantic CoreSchema.
            mode: Schema mode.

        Returns:
            A JSON Schema dict.
        """
        result = super().generate(schema, mode=mode)

        # Add schema dialect if not present
        if "$schema" not in result:
            result["$schema"] = SCHEMA_DIALECT

        return result
