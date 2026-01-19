"""Specification export functionality.

This module provides functions for building Specification objects from
Hive App registries and exporting them to JSON Schema or TOML format.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from hive.spec.constraints import parameter_to_json_schema
from hive.spec.models import (
    CommandSchema,
    EntitySchema,
    FieldSchema,
    ParameterSchema,
    QuerySchema,
    RelationshipSchema,
    Specification,
    SpecificationMetadata,
)

if TYPE_CHECKING:
    from hive.app import App


def build_specification(app: App) -> Specification:
    """Build a Specification object from an App's registry.

    Converts all registered commands, queries, and entities to their
    schema representations.

    Args:
        app: A Hive App instance with registered commands/queries/entities.

    Returns:
        A Specification containing all registered items.
    """
    # Get version from app or default
    version = getattr(app, "version", "0.1.0")

    # Get hive version
    try:
        from hive import __version__ as hive_version  # noqa: PLC0415
    except ImportError:
        hive_version = "0.1.0"

    # Build metadata
    metadata = SpecificationMetadata(
        name=app.name,
        version=version,
        generated_at=datetime.now(tz=UTC),
        hive_version=hive_version,
    )

    # Build command schemas
    commands: dict[str, CommandSchema] = {}
    for cmd_reg in app.registry.list_commands():
        commands[cmd_reg.name] = _build_command_schema(cmd_reg)

    # Build query schemas
    queries: dict[str, QuerySchema] = {}
    for query_reg in app.registry.list_queries():
        queries[query_reg.name] = _build_query_schema(query_reg)

    # Build entity schemas
    entities: dict[str, EntitySchema] = {}
    for entity_reg in app.registry.list_entities():
        entities[entity_reg.name] = _build_entity_schema(entity_reg)

    return Specification(
        metadata=metadata,
        commands=commands,
        queries=queries,
        entities=entities,
    )


def _build_command_schema(cmd_reg: Any) -> CommandSchema:
    """Build CommandSchema from CommandRegistration."""
    from hive.core.types import CommandRegistration  # noqa: PLC0415

    if not isinstance(cmd_reg, CommandRegistration):
        msg = f"Expected CommandRegistration, got {type(cmd_reg)}"
        raise TypeError(msg)

    # Convert parameters, excluding 'ctx'
    parameters: list[ParameterSchema] = []
    for param in cmd_reg.parameters:
        if param.name == "ctx":
            continue
        param_dict = parameter_to_json_schema(param)
        parameters.append(
            ParameterSchema(
                name=param_dict["name"],
                type=param_dict["type"],
                description=param_dict.get("description"),
                required=param_dict.get("required", True),
                default=param_dict.get("default"),
                minimum=param_dict.get("minimum"),
                maximum=param_dict.get("maximum"),
                min_length=param_dict.get("minLength"),  # pyright: ignore[reportCallIssue]
                max_length=param_dict.get("maxLength"),  # pyright: ignore[reportCallIssue]
                pattern=param_dict.get("pattern"),
                format=param_dict.get("format"),
            )
        )

    # Build return type schema
    return_type: dict[str, Any] = {"type": "object"}
    if cmd_reg.return_type:
        from hive.generators.schema import python_type_to_json_schema  # noqa: PLC0415

        return_type = python_type_to_json_schema(cmd_reg.return_type)

    return CommandSchema(
        name=cmd_reg.name,
        description=cmd_reg.docstring,
        parameters=parameters,
        return_type=return_type,
        aliases=cmd_reg.aliases,
        entities=[e.__name__ for e in cmd_reg.entities] if cmd_reg.entities else [],
    )


def _build_query_schema(query_reg: Any) -> QuerySchema:
    """Build QuerySchema from QueryRegistration."""
    from hive.core.types import QueryRegistration  # noqa: PLC0415

    if not isinstance(query_reg, QueryRegistration):
        msg = f"Expected QueryRegistration, got {type(query_reg)}"
        raise TypeError(msg)

    # Convert parameters, excluding 'ctx'
    parameters: list[ParameterSchema] = []
    for param in query_reg.parameters:
        if param.name == "ctx":
            continue
        param_dict = parameter_to_json_schema(param)
        parameters.append(
            ParameterSchema(
                name=param_dict["name"],
                type=param_dict["type"],
                description=param_dict.get("description"),
                required=param_dict.get("required", True),
                default=param_dict.get("default"),
                minimum=param_dict.get("minimum"),
                maximum=param_dict.get("maximum"),
                min_length=param_dict.get("minLength"),  # pyright: ignore[reportCallIssue]
                max_length=param_dict.get("maxLength"),  # pyright: ignore[reportCallIssue]
                pattern=param_dict.get("pattern"),
                format=param_dict.get("format"),
            )
        )

    # Build return type schema
    return_type: dict[str, Any] = {"type": "object"}
    if query_reg.return_type:
        from hive.generators.schema import python_type_to_json_schema  # noqa: PLC0415

        return_type = python_type_to_json_schema(query_reg.return_type)

    return QuerySchema(
        name=query_reg.name,
        description=query_reg.docstring,
        parameters=parameters,
        return_type=return_type,
        cache_ttl=query_reg.cache_ttl,
        entities=[e.__name__ for e in query_reg.entities] if query_reg.entities else [],
    )


def _build_entity_schema(entity_reg: Any) -> EntitySchema:
    """Build EntitySchema from EntityRegistration."""
    from hive.core.types import EntityRegistration  # noqa: PLC0415

    if not isinstance(entity_reg, EntityRegistration):
        msg = f"Expected EntityRegistration, got {type(entity_reg)}"
        raise TypeError(msg)

    # Convert fields
    fields: list[FieldSchema] = [
        FieldSchema(
            name=field_info.name,
            type=_type_to_json_schema_type(field_info.type),
            primary_key=field_info.primary_key,
            nullable=field_info.nullable,
            indexed=field_info.index,
            default=field_info.default,
        )
        for field_info in entity_reg.fields
    ]

    # Convert relationships
    relationships: list[RelationshipSchema] = [
        RelationshipSchema(
            field_name=rel_info.field_name,
            target_entity=rel_info.target_entity,
            relationship_type=rel_info.relationship_type,  # type: ignore[arg-type]
            foreign_key=rel_info.foreign_key,
        )
        for rel_info in entity_reg.relationships
    ]

    return EntitySchema(
        name=entity_reg.name,
        table_name=entity_reg.table_name or entity_reg.name.lower() + "s",
        fields=fields,
        relationships=relationships,
    )


def _type_to_json_schema_type(type_hint: type) -> str:
    """Convert Python type to JSON Schema type string."""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    # Handle None and optional types
    if type_hint is type(None):
        return "null"

    # Get the base type name
    type_name = getattr(type_hint, "__name__", str(type_hint))
    return type_map.get(type_hint, type_name)


def export_specification(
    app: App,
    *,
    format: Literal["json", "toml"] = "json",  # noqa: A002
    output: str | Path | None = None,
    include_internal: bool = False,  # noqa: ARG001  # Reserved for future use
) -> str:
    """Export application specification to JSON Schema or TOML.

    Args:
        app: A Hive App instance.
        format: Output format ('json' or 'toml').
        output: Optional file path to write output.
        include_internal: Include hidden/internal commands.

    Returns:
        The specification as a formatted string.

    Raises:
        ValueError: If format is not 'json' or 'toml'.
    """
    spec = build_specification(app)

    if format == "json":
        # Convert to JSON Schema format
        output_dict = _spec_to_json_schema(spec)
        result = json.dumps(output_dict, indent=2, default=str)
    elif format == "toml":
        # TOML export - will be implemented in US5
        import tomli_w  # noqa: PLC0415

        output_dict = _spec_to_dict(spec)
        result = tomli_w.dumps(output_dict)
    else:
        msg = f"Unsupported format: {format}"
        raise ValueError(msg)

    # Write to file if output path specified
    if output:
        output_path = Path(output)
        output_path.write_text(result)

    return result


def _spec_to_json_schema(spec: Specification) -> dict[str, Any]:
    """Convert Specification to JSON Schema dict."""
    return {
        "$schema": spec.metadata.schema_dialect,
        "metadata": {
            "name": spec.metadata.name,
            "version": spec.metadata.version,
            "generated_at": spec.metadata.generated_at.isoformat(),
            "hive_version": spec.metadata.hive_version,
        },
        "commands": {name: _command_schema_to_dict(cmd) for name, cmd in spec.commands.items()},
        "queries": {name: _query_schema_to_dict(query) for name, query in spec.queries.items()},
        "entities": {
            name: _entity_schema_to_dict(entity) for name, entity in spec.entities.items()
        },
        "$defs": spec.types,
    }


def _spec_to_dict(spec: Specification) -> dict[str, Any]:
    """Convert Specification to plain dict (for TOML)."""
    return {
        "metadata": {
            "name": spec.metadata.name,
            "version": spec.metadata.version,
            "generated_at": spec.metadata.generated_at.isoformat(),
            "hive_version": spec.metadata.hive_version,
            "schema_dialect": spec.metadata.schema_dialect,
        },
        "commands": {name: _command_schema_to_dict(cmd) for name, cmd in spec.commands.items()},
        "queries": {name: _query_schema_to_dict(query) for name, query in spec.queries.items()},
        "entities": {
            name: _entity_schema_to_dict(entity) for name, entity in spec.entities.items()
        },
    }


def _command_schema_to_dict(cmd: CommandSchema) -> dict[str, Any]:
    """Convert CommandSchema to dict."""
    result: dict[str, Any] = {
        "name": cmd.name,
        "parameters": [_parameter_schema_to_dict(p) for p in cmd.parameters],
        "return_type": cmd.return_type,
    }
    if cmd.description:
        result["description"] = cmd.description
    if cmd.aliases:
        result["aliases"] = cmd.aliases
    if cmd.entities:
        result["entities"] = cmd.entities
    return result


def _query_schema_to_dict(query: QuerySchema) -> dict[str, Any]:
    """Convert QuerySchema to dict."""
    result: dict[str, Any] = {
        "name": query.name,
        "parameters": [_parameter_schema_to_dict(p) for p in query.parameters],
        "return_type": query.return_type,
    }
    if query.description:
        result["description"] = query.description
    if query.cache_ttl:
        result["cache_ttl"] = query.cache_ttl
    if query.entities:
        result["entities"] = query.entities
    return result


def _parameter_schema_to_dict(param: ParameterSchema) -> dict[str, Any]:
    """Convert ParameterSchema to dict."""
    result: dict[str, Any] = {
        "name": param.name,
        "type": param.type,
        "required": param.required,
    }
    if param.description:
        result["description"] = param.description
    if param.default is not None:
        result["default"] = param.default
    if param.minimum is not None:
        result["minimum"] = param.minimum
    if param.maximum is not None:
        result["maximum"] = param.maximum
    if param.min_length is not None:
        result["minLength"] = param.min_length
    if param.max_length is not None:
        result["maxLength"] = param.max_length
    if param.pattern:
        result["pattern"] = param.pattern
    if param.format:
        result["format"] = param.format
    return result


def _entity_schema_to_dict(entity: EntitySchema) -> dict[str, Any]:
    """Convert EntitySchema to dict."""
    result: dict[str, Any] = {
        "name": entity.name,
        "table_name": entity.table_name,
        "fields": [
            {
                "name": f.name,
                "type": f.type,
                "primary_key": f.primary_key,
                "nullable": f.nullable,
                "indexed": f.indexed,
            }
            for f in entity.fields
        ],
    }
    if entity.description:
        result["description"] = entity.description
    if entity.relationships:
        result["relationships"] = [
            {
                "field_name": r.field_name,
                "target_entity": r.target_entity,
                "relationship_type": r.relationship_type,
                "foreign_key": r.foreign_key,
            }
            for r in entity.relationships
        ]
    return result
