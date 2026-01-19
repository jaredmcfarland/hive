# Data Model: Specification and Distribution

**Branch**: `003-spec-distribution` | **Date**: 2026-01-18

## Overview

This phase primarily deals with **data transformation and export** rather than persistent data models. The core entities are internal representations that serialize to external formats (JSON Schema, TOML, MCP, REST).

## Core Data Structures

### Specification (Export Container)

The root container for all exportable specification data.

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SpecificationMetadata(BaseModel):
    """Metadata about the exported specification."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(description="Application name")
    version: str = Field(description="Specification version (semver)")
    generated_at: datetime = Field(description="Export timestamp")
    hive_version: str = Field(description="Hive framework version")
    schema_dialect: str = Field(
        default="https://json-schema.org/draft/2020-12/schema",
        description="JSON Schema version"
    )


class Specification(BaseModel):
    """Complete application specification."""

    model_config = ConfigDict(strict=True, frozen=True)

    metadata: SpecificationMetadata
    commands: dict[str, CommandSchema] = Field(default_factory=dict)
    queries: dict[str, QuerySchema] = Field(default_factory=dict)
    entities: dict[str, EntitySchema] = Field(default_factory=dict)
    types: dict[str, TypeSchema] = Field(
        default_factory=dict,
        description="Shared type definitions ($defs)"
    )
```

### CommandSchema / QuerySchema

Schema representation for commands and queries.

```python
class ParameterSchema(BaseModel):
    """JSON Schema representation of a parameter."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    type: str = Field(description="JSON Schema type")
    description: str | None = None
    required: bool = True
    default: Any | None = None

    # Constraints (mapped from ConstraintMetadata)
    minimum: float | None = None
    maximum: float | None = None
    min_length: int | None = Field(default=None, alias="minLength")
    max_length: int | None = Field(default=None, alias="maxLength")
    pattern: str | None = None
    format: str | None = None  # email, uri, date-time, etc.


class CommandSchema(BaseModel):
    """JSON Schema for a command."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    description: str | None = None
    parameters: list[ParameterSchema] = Field(default_factory=list)
    return_type: dict[str, Any] = Field(
        description="JSON Schema for return type"
    )
    aliases: list[str] = Field(default_factory=list)
    entities: list[str] = Field(
        default_factory=list,
        description="Entity names this command operates on"
    )


class QuerySchema(BaseModel):
    """JSON Schema for a query."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    description: str | None = None
    parameters: list[ParameterSchema] = Field(default_factory=list)
    return_type: dict[str, Any]
    cache_ttl: int | None = Field(
        default=None,
        description="Cache duration in seconds"
    )
    entities: list[str] = Field(default_factory=list)
```

### EntitySchema

Schema representation for entities (database tables).

```python
class FieldSchema(BaseModel):
    """JSON Schema for an entity field."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    type: str
    description: str | None = None
    primary_key: bool = False
    nullable: bool = False
    indexed: bool = False
    default: Any | None = None

    # Constraints
    minimum: float | None = None
    maximum: float | None = None
    min_length: int | None = Field(default=None, alias="minLength")
    max_length: int | None = Field(default=None, alias="maxLength")
    pattern: str | None = None


class RelationshipSchema(BaseModel):
    """Schema for entity relationships."""

    model_config = ConfigDict(strict=True, frozen=True)

    field_name: str
    target_entity: str
    relationship_type: Literal["one-to-one", "one-to-many", "many-to-one"]
    foreign_key: str


class EntitySchema(BaseModel):
    """JSON Schema for an entity."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str
    table_name: str
    description: str | None = None
    fields: list[FieldSchema] = Field(default_factory=list)
    relationships: list[RelationshipSchema] = Field(default_factory=list)
```

### SpecificationDiff

Result of comparing two specifications.

```python
class DiffItem(BaseModel):
    """Single difference between specifications."""

    model_config = ConfigDict(strict=True, frozen=True)

    path: str = Field(description="JSON path to changed element")
    change_type: Literal["added", "removed", "modified"]
    old_value: Any | None = None
    new_value: Any | None = None
    breaking: bool = Field(
        default=False,
        description="True if this is a breaking change"
    )


class SpecificationDiff(BaseModel):
    """Comparison result between two specifications."""

    model_config = ConfigDict(strict=True, frozen=True)

    v1_version: str
    v2_version: str
    compared_at: datetime
    changes: list[DiffItem] = Field(default_factory=list)
    breaking_changes: list[DiffItem] = Field(default_factory=list)

    @property
    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

    @property
    def summary(self) -> str:
        added = sum(1 for c in self.changes if c.change_type == "added")
        removed = sum(1 for c in self.changes if c.change_type == "removed")
        modified = sum(1 for c in self.changes if c.change_type == "modified")
        return f"+{added} -{removed} ~{modified} ({len(self.breaking_changes)} breaking)"
```

---

## MCP-Specific Data Structures

### MCPTool

Representation of a Hive command as an MCP tool.

```python
class MCPToolSchema(BaseModel):
    """MCP tool input schema."""

    model_config = ConfigDict(strict=True, frozen=True)

    type: Literal["object"] = "object"
    properties: dict[str, dict[str, Any]] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class MCPTool(BaseModel):
    """A command exposed as an MCP tool."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = Field(description="Tool identifier (command name)")
    description: str = Field(description="From command docstring")
    input_schema: MCPToolSchema


class MCPServerConfig(BaseModel):
    """Configuration for generated MCP server."""

    model_config = ConfigDict(strict=True)

    name: str
    description: str | None = None
    transport: Literal["stdio", "sse"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8080
    tools: list[MCPTool] = Field(default_factory=list)
```

---

## REST API Data Structures

### RESTEndpoint

Representation of a command/query as a REST endpoint.

```python
class RESTEndpoint(BaseModel):
    """A command or query exposed as REST endpoint."""

    model_config = ConfigDict(strict=True, frozen=True)

    path: str = Field(description="URL path, e.g., /commands/create_task")
    method: Literal["GET", "POST", "PUT", "DELETE"]
    operation_id: str
    summary: str | None = None
    description: str | None = None
    request_body_schema: dict[str, Any] | None = None
    response_schema: dict[str, Any]
    tags: list[str] = Field(default_factory=list)


class RESTAPIConfig(BaseModel):
    """Configuration for generated REST API."""

    model_config = ConfigDict(strict=True)

    title: str
    description: str | None = None
    version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8000
    base_path: str = ""
    endpoints: list[RESTEndpoint] = Field(default_factory=list)
```

---

## Project Template Data Structures

### ProjectTemplate

Structure for project scaffolding.

```python
class TemplateFile(BaseModel):
    """A file in a project template."""

    model_config = ConfigDict(strict=True, frozen=True)

    path: str = Field(description="Relative path from project root")
    content: str = Field(description="File content (may include {{variables}})")
    executable: bool = False


class ProjectTemplate(BaseModel):
    """Project scaffolding template."""

    model_config = ConfigDict(strict=True, frozen=True)

    name: str = "default"
    description: str = "Standard Hive project"
    files: list[TemplateFile] = Field(default_factory=list)
    dependencies: list[str] = Field(
        default_factory=list,
        description="Required pip packages"
    )
    dev_dependencies: list[str] = Field(default_factory=list)
    post_init_commands: list[str] = Field(
        default_factory=list,
        description="Commands to run after scaffolding"
    )
```

---

## Type Mappings

### Python → JSON Schema Type Mapping

| Python Type | JSON Schema Type | Format/Additional |
|-------------|------------------|-------------------|
| `str` | `string` | - |
| `int` | `integer` | - |
| `float` | `number` | - |
| `bool` | `boolean` | - |
| `None` | `null` | - |
| `list[T]` | `array` | `items: T` |
| `dict[str, T]` | `object` | `additionalProperties: T` |
| `datetime` | `string` | `format: date-time` |
| `date` | `string` | `format: date` |
| `UUID` | `string` | `format: uuid` |
| `Email` | `string` | `format: email` |
| `Url` | `string` | `format: uri` |
| `PositiveInt` | `integer` | `minimum: 1` |
| `Percentage` | `number` | `minimum: 0, maximum: 100` |
| `Port` | `integer` | `minimum: 1, maximum: 65535` |
| `NonEmptyStr` | `string` | `minLength: 1` |

### Constraint Mapping

| ConstraintMetadata | JSON Schema |
|--------------------|-------------|
| `min_value` | `minimum` |
| `max_value` | `maximum` |
| `min_length` | `minLength` |
| `max_length` | `maxLength` |
| `pattern` | `pattern` |

---

## Validation Rules

### Specification Export

1. All commands MUST have at least one parameter (the `ctx` parameter is excluded from export)
2. Return types MUST be serializable to JSON (Pydantic models or primitives)
3. Entity names MUST be unique within the specification
4. Command/query names MUST be valid identifiers

### Specification Diff

1. Breaking changes MUST be detected for:
   - Removed commands
   - Removed required parameters
   - Changed parameter types (narrowing)
   - Removed entities referenced by commands

2. Non-breaking changes:
   - Added commands/queries
   - Added optional parameters
   - Changed return type (widening)

### MCP Tool Generation

1. Tool names MUST match command names
2. Input schema MUST exclude `ctx` parameter
3. Descriptions MUST be non-empty (use function name if no docstring)

### REST Endpoint Generation

1. Command endpoints MUST use POST method
2. Query endpoints MUST use GET method
3. Path parameters MUST be URL-safe
4. Request/response schemas MUST be valid JSON Schema

---

## State Transitions

This phase does not introduce persistent state machines. All operations are stateless transformations:

```
Registry → Specification → JSON Schema
                        → TOML
                        → MCP Tools
                        → REST Endpoints
```

Diff operations:

```
Specification V1 + Specification V2 → SpecificationDiff
```
