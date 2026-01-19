"""Specification data models for Hive framework.

This module contains Pydantic models for representing Hive application
specifications in a serializable format suitable for JSON Schema export,
TOML export, MCP tool generation, and REST API generation.

All models use ConfigDict(strict=True, frozen=True) for maximum validation
and immutability guarantees.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Specification Metadata
# =============================================================================


class SpecificationMetadata(BaseModel):
    """Metadata about the exported specification.

    Contains application name, version, generation timestamp, and
    schema dialect information.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(description="Application name")
    version: str = Field(description="Specification version (semver)")
    generated_at: datetime = Field(description="Export timestamp")
    hive_version: str = Field(description="Hive framework version")
    schema_dialect: str = Field(
        default="https://json-schema.org/draft/2020-12/schema",
        description="JSON Schema version",
    )


# =============================================================================
# Parameter and Field Schemas
# =============================================================================


class ParameterSchema(BaseModel):
    """JSON Schema representation of a command/query parameter.

    Maps Python function parameters to JSON Schema with constraint
    information extracted from type annotations and refinement types.
    """

    model_config = ConfigDict(strict=True, frozen=True, populate_by_name=True)

    name: str = Field(description="Parameter name")
    type: str = Field(description="JSON Schema type (string, integer, etc.)")
    description: str | None = Field(default=None, description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Any = Field(default=None, description="Default value if any")

    # Constraints (mapped from ConstraintMetadata)
    minimum: float | None = Field(default=None, description="Minimum value for numbers")
    maximum: float | None = Field(default=None, description="Maximum value for numbers")
    min_length: int | None = Field(
        default=None,
        alias="minLength",
        description="Minimum length for strings/arrays",
    )
    max_length: int | None = Field(
        default=None,
        alias="maxLength",
        description="Maximum length for strings/arrays",
    )
    pattern: str | None = Field(default=None, description="Regex pattern for strings")
    format: str | None = Field(
        default=None,
        description="String format (email, uri, date-time, etc.)",
    )


class FieldSchema(BaseModel):
    """JSON Schema for an entity field.

    Represents a column/field in a database entity with type information
    and constraint metadata.
    """

    model_config = ConfigDict(strict=True, frozen=True, populate_by_name=True)

    name: str = Field(description="Field name")
    type: str = Field(description="JSON Schema type")
    description: str | None = Field(default=None, description="Field description")
    primary_key: bool = Field(default=False, description="Is this the primary key")
    nullable: bool = Field(default=False, description="Can this field be null")
    indexed: bool = Field(default=False, description="Is this field indexed")
    default: Any = Field(default=None, description="Default value")

    # Constraints
    minimum: float | None = Field(default=None, description="Minimum value")
    maximum: float | None = Field(default=None, description="Maximum value")
    min_length: int | None = Field(
        default=None,
        alias="minLength",
        description="Minimum length",
    )
    max_length: int | None = Field(
        default=None,
        alias="maxLength",
        description="Maximum length",
    )
    pattern: str | None = Field(default=None, description="Regex pattern")


class RelationshipSchema(BaseModel):
    """Schema for entity relationships.

    Defines how entities relate to each other (one-to-one, one-to-many,
    many-to-one).
    """

    model_config = ConfigDict(strict=True, frozen=True)

    field_name: str = Field(description="Relationship field name")
    target_entity: str = Field(description="Target entity name")
    relationship_type: Literal["one-to-one", "one-to-many", "many-to-one"] = Field(
        description="Type of relationship",
    )
    foreign_key: str = Field(description="Foreign key field name")


# =============================================================================
# Command, Query, Entity Schemas
# =============================================================================


class CommandSchema(BaseModel):
    """JSON Schema for a command.

    Commands are state-modifying operations. This schema includes
    parameter definitions, return type, and associated entities.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(description="Command name")
    description: str | None = Field(default=None, description="Command description")
    parameters: list[ParameterSchema] = Field(
        default_factory=list,
        description="Command parameters",
    )
    return_type: dict[str, Any] = Field(
        description="JSON Schema for return type",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Command aliases",
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Entity names this command operates on",
    )


class QuerySchema(BaseModel):
    """JSON Schema for a query.

    Queries are read-only operations with optional caching.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(description="Query name")
    description: str | None = Field(default=None, description="Query description")
    parameters: list[ParameterSchema] = Field(
        default_factory=list,
        description="Query parameters",
    )
    return_type: dict[str, Any] = Field(description="JSON Schema for return type")
    cache_ttl: int | None = Field(
        default=None,
        description="Cache duration in seconds",
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Entity names this query reads from",
    )


class EntitySchema(BaseModel):
    """JSON Schema for an entity.

    Entities are database tables/models with fields and relationships.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(description="Entity name")
    table_name: str = Field(description="Database table name")
    description: str | None = Field(default=None, description="Entity description")
    fields: list[FieldSchema] = Field(
        default_factory=list,
        description="Entity fields",
    )
    relationships: list[RelationshipSchema] = Field(
        default_factory=list,
        description="Entity relationships",
    )


# =============================================================================
# Specification Diff Models
# =============================================================================


class DiffItem(BaseModel):
    """Single difference between specifications.

    Represents one change (added, removed, modified) at a specific
    JSON path in the specification.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    path: str = Field(description="JSON path to changed element")
    change_type: Literal["added", "removed", "modified"] = Field(
        description="Type of change",
    )
    old_value: Any = Field(default=None, description="Previous value (null for added)")
    new_value: Any = Field(default=None, description="New value (null for removed)")
    breaking: bool = Field(
        default=False,
        description="True if this is a breaking change",
    )


class SpecificationDiff(BaseModel):
    """Comparison result between two specifications.

    Contains all changes and highlights breaking changes that
    may affect API consumers.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    v1_version: str = Field(description="Version of first specification")
    v2_version: str = Field(description="Version of second specification")
    compared_at: datetime = Field(description="Comparison timestamp")
    changes: list[DiffItem] = Field(
        default_factory=list,
        description="All changes",
    )
    breaking_changes: list[DiffItem] = Field(
        default_factory=list,
        description="Breaking changes only",
    )

    @property
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return len(self.breaking_changes) > 0

    @property
    def summary(self) -> str:
        """Generate a human-readable summary of changes."""
        added = sum(1 for c in self.changes if c.change_type == "added")
        removed = sum(1 for c in self.changes if c.change_type == "removed")
        modified = sum(1 for c in self.changes if c.change_type == "modified")
        return f"+{added} -{removed} ~{modified} ({len(self.breaking_changes)} breaking)"


# =============================================================================
# Specification Container
# =============================================================================


class Specification(BaseModel):
    """Complete application specification.

    The root container for all exportable specification data including
    metadata, commands, queries, entities, and shared type definitions.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    metadata: SpecificationMetadata = Field(description="Specification metadata")
    commands: dict[str, CommandSchema] = Field(
        default_factory=dict,
        description="Command schemas by name",
    )
    queries: dict[str, QuerySchema] = Field(
        default_factory=dict,
        description="Query schemas by name",
    )
    entities: dict[str, EntitySchema] = Field(
        default_factory=dict,
        description="Entity schemas by name",
    )
    types: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Shared type definitions ($defs)",
    )


# =============================================================================
# MCP-Specific Models
# =============================================================================


class MCPToolSchema(BaseModel):
    """MCP tool input schema.

    Defines the JSON Schema for tool input parameters following
    the MCP protocol specification.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    type: Literal["object"] = Field(default="object", description="Always 'object'")
    properties: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Property schemas",
    )
    required: list[str] = Field(
        default_factory=list,
        description="Required property names",
    )


class MCPTool(BaseModel):
    """A command exposed as an MCP tool.

    Represents a Hive command formatted for MCP protocol consumption.
    """

    model_config = ConfigDict(strict=True, frozen=True, populate_by_name=True)

    name: str = Field(description="Tool identifier (command name)")
    description: str = Field(description="From command docstring")
    input_schema: MCPToolSchema = Field(
        alias="inputSchema",
        description="Tool input schema",
    )


class MCPServerConfig(BaseModel):
    """Configuration for generated MCP server.

    Defines server name, transport, and available tools.
    """

    model_config = ConfigDict(strict=True)

    name: str = Field(description="Server name")
    description: str | None = Field(default=None, description="Server description")
    transport: Literal["stdio", "sse"] = Field(
        default="stdio",
        description="Transport protocol",
    )
    host: str = Field(default="127.0.0.1", description="Host to bind (SSE only)")
    port: int = Field(default=8080, description="Port to listen on (SSE only)")
    tools: list[MCPTool] = Field(
        default_factory=list,
        description="Available tools",
    )


# =============================================================================
# REST API Models
# =============================================================================


class RESTEndpoint(BaseModel):
    """A command or query exposed as REST endpoint.

    Represents a Hive operation formatted for REST API consumption.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    path: str = Field(description="URL path, e.g., /commands/create_task")
    method: Literal["GET", "POST", "PUT", "DELETE"] = Field(
        description="HTTP method",
    )
    operation_id: str = Field(description="OpenAPI operation ID")
    summary: str | None = Field(default=None, description="Operation summary")
    description: str | None = Field(default=None, description="Operation description")
    request_body_schema: dict[str, Any] | None = Field(
        default=None,
        description="Request body JSON Schema",
    )
    response_schema: dict[str, Any] = Field(description="Response JSON Schema")
    tags: list[str] = Field(
        default_factory=list,
        description="OpenAPI tags",
    )


class RESTAPIConfig(BaseModel):
    """Configuration for generated REST API.

    Defines API metadata and available endpoints.
    """

    model_config = ConfigDict(strict=True)

    title: str = Field(description="API title")
    description: str | None = Field(default=None, description="API description")
    version: str = Field(default="0.1.0", description="API version")
    host: str = Field(default="127.0.0.1", description="Host to bind")
    port: int = Field(default=8000, description="Port to listen on")
    base_path: str = Field(default="", description="Base path prefix")
    endpoints: list[RESTEndpoint] = Field(
        default_factory=list,
        description="Available endpoints",
    )


# =============================================================================
# Project Template Models
# =============================================================================


class TemplateFile(BaseModel):
    """A file in a project template.

    Represents a single file to be created during project scaffolding.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    path: str = Field(description="Relative path from project root")
    content: str = Field(description="File content (may include {{variables}})")
    executable: bool = Field(default=False, description="Make file executable")


class ProjectTemplate(BaseModel):
    """Project scaffolding template.

    Defines the complete structure for a new Hive project.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(default="default", description="Template name")
    description: str = Field(default="Standard Hive project", description="Template description")
    files: list[TemplateFile] = Field(
        default_factory=list,
        description="Files to create",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Required pip packages",
    )
    dev_dependencies: list[str] = Field(
        default_factory=list,
        description="Dev pip packages",
    )
    post_init_commands: list[str] = Field(
        default_factory=list,
        description="Commands to run after scaffolding",
    )
