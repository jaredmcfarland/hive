# Data Model: Core Framework

**Feature**: 001-core-framework
**Date**: 2026-01-11

## Overview

The core framework's data model consists of registration types (metadata about decorated items) and runtime types (context, configuration). These are internal framework types, not user-facing entities.

## Registration Types

### CommandRegistration

Represents a decorated command function.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | str | Command name (CLI subcommand) | Unique within registry; lowercase; no spaces |
| func | Callable | Reference to original function | Must be async callable |
| parameters | list[ParameterInfo] | Extracted parameter metadata | Ordered; excludes ctx |
| return_type | type | Function return type annotation | Must be serializable (Pydantic model or primitive) |
| docstring | str \| None | Function docstring | First paragraph = short help |
| entities | list[type] | Related entity classes | For documentation/cache invalidation |
| aliases | list[str] | Alternative command names | Optional; must be unique |
| hidden | bool | Exclude from help text | Default False |

### QueryRegistration

Represents a decorated query function (read-only operation).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | str | Query name | Same constraints as command |
| func | Callable | Reference to original function | Must be async callable |
| parameters | list[ParameterInfo] | Extracted parameter metadata | Same as command |
| return_type | type | Function return type annotation | Same as command |
| docstring | str \| None | Function docstring | Same as command |
| entities | list[type] | Related entity classes | For cache invalidation |
| cache_ttl | int \| None | Cache time-to-live in seconds | None = no caching; 0 = cache indefinitely |

### EntityRegistration

Represents a decorated entity class (data model).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | str | Entity name | Unique; typically class name |
| cls | type | Reference to model class | Must be SQLModel subclass |
| fields | list[FieldInfo] | Extracted field metadata | From Pydantic model_fields |
| table_name | str | Database table name | Derived from class name or explicit |
| relationships | list[RelationshipInfo] | Foreign key references | To other registered entities |

### ScreenRegistration

Represents a decorated screen class (TUI view).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | str | Screen identifier | Unique; used for navigation |
| cls | type | Reference to screen class | Must be Textual Screen subclass |
| default | bool | Is this the startup screen? | Only one can be True |
| keybinding | str \| None | Global key to navigate here | Single character; unique |
| docstring | str \| None | Screen description | For command palette |

## Supporting Types

### ParameterInfo

Metadata about a single function parameter.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Parameter name |
| type | type | Type annotation |
| default | Any \| REQUIRED | Default value or sentinel |
| kind | ParameterKind | POSITIONAL, KEYWORD, etc. |
| help | str \| None | From Annotated metadata |
| short | str \| None | Short flag (e.g., "-s") |

### FieldInfo

Metadata about an entity field.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Field name |
| type | type | Type annotation |
| primary_key | bool | Is primary key? |
| nullable | bool | Allows None? |
| default | Any \| None | Default value |
| index | bool | Is indexed? |

### RelationshipInfo

Metadata about entity relationships.

| Field | Type | Description |
|-------|------|-------------|
| field_name | str | Field name on this entity |
| target_entity | str | Name of related entity |
| relationship_type | str | "one-to-one", "one-to-many", "many-to-one" |
| foreign_key | str | Foreign key column |

## Runtime Types

### ExecutionContext

Runtime container provided to commands.

| Field | Type | Description |
|-------|------|-------------|
| db | AsyncSession | Database session for operations |
| config | AppSettings | Application configuration |
| output | OutputFormatter | Format-aware output handler |
| command_name | str | Name of executing command |
| output_format | OutputFormat | JSON, TABLE, CSV |
| interactive | bool | True if TTY attached |

### OutputFormat (Enum)

| Value | CLI Flag | Description |
|-------|----------|-------------|
| JSON | --json | Machine-readable JSON output |
| TABLE | (default) | Human-readable Rich table |
| CSV | --format csv | Comma-separated values |

### AppSettings (Pydantic Settings)

| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| database_url | str | sqlite:///~/.hive/data.db | HIVE_DATABASE_URL |
| debug | bool | False | HIVE_DEBUG |
| log_level | str | INFO | HIVE_LOG_LEVEL |

## Entity Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     ApplicationRegistry                          │
├─────────────────────────────────────────────────────────────────┤
│ commands: dict[str, CommandRegistration]                        │
│ queries: dict[str, QueryRegistration]                           │
│ entities: dict[str, EntityRegistration]                         │
│ screens: dict[str, ScreenRegistration]                          │
├─────────────────────────────────────────────────────────────────┤
│ + register_command(reg: CommandRegistration)                    │
│ + register_query(reg: QueryRegistration)                        │
│ + register_entity(reg: EntityRegistration)                      │
│ + register_screen(reg: ScreenRegistration)                      │
│ + get_command(name: str) -> CommandRegistration                 │
│ + list_commands() -> list[CommandRegistration]                  │
│ + validate() -> list[ValidationError]                           │
└─────────────────────────────────────────────────────────────────┘
         │
         │ contains
         ▼
┌─────────────────────┐    ┌─────────────────────┐
│ CommandRegistration │    │  QueryRegistration  │
├─────────────────────┤    ├─────────────────────┤
│ name                │    │ name                │
│ func                │    │ func                │
│ parameters ─────────┼───►│ parameters          │
│ return_type         │    │ return_type         │
│ docstring           │    │ docstring           │
│ entities ───────────┼───►│ entities            │
│ aliases             │    │ cache_ttl           │
│ hidden              │    └─────────────────────┘
└─────────────────────┘
         │
         │ references
         ▼
┌─────────────────────┐    ┌─────────────────────┐
│ EntityRegistration  │    │  ScreenRegistration │
├─────────────────────┤    ├─────────────────────┤
│ name                │    │ name                │
│ cls                 │    │ cls                 │
│ fields ─────────────┼───►│ default             │
│ table_name          │    │ keybinding          │
│ relationships       │    │ docstring           │
└─────────────────────┘    └─────────────────────┘
```

## State Transitions

### Registration Lifecycle

```
[Not Registered] ──@decorator──► [Registered] ──app.validate()──► [Validated]
                                      │
                                      │ duplicate name
                                      ▼
                                [RegistrationError]
```

### Context Lifecycle

```
[Created] ──__aenter__──► [Active] ──command execution──► [Active]
                              │                               │
                              │ exception                     │ success
                              ▼                               ▼
                        [Rollback] ──__aexit__──►        [Commit] ──__aexit__──► [Closed]
                              │                               │
                              └───────────────────────────────┘
                                              │
                                              ▼
                                          [Closed]
```

## Validation Rules

1. **Command/Query names**: Must be unique across both registries (can't have command and query with same name)
2. **Entity names**: Must be unique; class name used by default
3. **Screen default**: Exactly one screen may have `default=True`
4. **Keybindings**: Must be unique across all screens
5. **Entity references**: Commands/queries referencing entities must reference registered entities (warning if not)
6. **Return types**: Must be JSON-serializable (Pydantic BaseModel or primitive types)
