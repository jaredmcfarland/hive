# Public API Contract: Core Framework

**Feature**: 001-core-framework
**Date**: 2026-01-11

## Overview

This document defines the public Python API for the Hive core framework. These are the interfaces that framework users (application developers) will interact with.

## Top-Level Exports

The following symbols are exported from `hive` package:

```python
from hive import (
    # Core class
    App,

    # Decorators
    command,
    query,
    entity,
    screen,

    # Types for annotations
    Argument,
    Option,

    # Errors
    CommandError,
    ConfigurationError,
    HiveError,
)
```

## App Class

### Constructor

```python
App(
    name: str,                           # Package name (e.g., "my-app")
    version: str = "0.1.0",              # Semantic version
    description: str = "",               # Human-readable description
    cli_command: str | None = None,      # CLI entry point name (defaults to name)
    tui_title: str | None = None,        # TUI window title
    database: str = "sqlite:///~/.{name}/data.db",  # Database URL
    mcp_server: bool = False,            # Enable MCP server generation
    rest_api: bool = False,              # Enable REST API generation
) -> App
```

### Properties

```python
app.name: str                            # Application name
app.version: str                         # Version string
app.registry: ApplicationRegistry        # Access to registration data (read-only)
```

### Methods

```python
app.validate() -> list[ValidationError]  # Validate all registrations
app.cli() -> typer.Typer                 # Get generated Typer app
```

## Decorators

### @command

```python
@command(
    app: App,                            # Application instance
    entities: list[type] = [],           # Related entity classes
    name: str | None = None,             # Override command name
    aliases: list[str] = [],             # Alternative names
    hidden: bool = False,                # Hide from help
) -> Callable[[F], F]
```

**Usage**:
```python
@command(app, entities=[Task])
async def add(ctx, title: str) -> Task:
    """Add a new task."""
    ...
```

### @query

```python
@query(
    app: App,                            # Application instance
    entities: list[type] = [],           # Related entity classes
    cache_ttl: int | None = None,        # Cache TTL in seconds
    name: str | None = None,             # Override query name
) -> Callable[[F], F]
```

**Usage**:
```python
@query(app, entities=[Task], cache_ttl=300)
async def list_tasks(ctx, completed: bool = False) -> list[Task]:
    """List all tasks."""
    ...
```

### @entity

```python
@entity(
    app: App,                            # Application instance
) -> Callable[[T], T]
```

**Usage**:
```python
@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False
```

### @screen

```python
@screen(
    app: App,                            # Application instance
    default: bool = False,               # Is startup screen?
    keybinding: str | None = None,       # Navigation key
    name: str | None = None,             # Override screen name
) -> Callable[[T], T]
```

**Usage**:
```python
@screen(app, default=True, keybinding="d")
class DashboardScreen(Screen):
    """Main dashboard."""
    ...
```

## Type Annotations

### Argument

Used with `Annotated` to mark positional CLI arguments.

```python
from typing import Annotated
from hive import Argument

async def add(
    ctx,
    title: Annotated[str, Argument(help="Task title")],
) -> Task:
    ...
```

**Parameters**:
```python
Argument(
    help: str | None = None,             # Help text
)
```

### Option

Used with `Annotated` to mark named CLI options.

```python
from typing import Annotated
from hive import Option

async def list_tasks(
    ctx,
    completed: Annotated[bool, Option("--completed", "-c", help="Show completed")] = False,
) -> list[Task]:
    ...
```

**Parameters**:
```python
Option(
    *names: str,                         # Long and short flags (e.g., "--name", "-n")
    help: str | None = None,             # Help text
)
```

## Execution Context

Commands receive a context object as their first parameter.

### Context Properties

```python
ctx.db: AsyncSession                     # Database session
ctx.config: AppSettings                  # Application configuration
ctx.output: OutputFormatter              # Output handler
ctx.command_name: str                    # Current command name
ctx.output_format: OutputFormat          # Requested output format
ctx.interactive: bool                    # True if TTY attached
```

### Context Database Methods

```python
await ctx.db.exec(statement)             # Execute query, return results
await ctx.db.get(Model, id)              # Get by primary key
ctx.db.add(instance)                     # Stage for insert
await ctx.db.commit()                    # Commit transaction
await ctx.db.rollback()                  # Rollback transaction
await ctx.db.refresh(instance)           # Reload from database
```

### Context Output Methods

```python
ctx.output.result(data: BaseModel)       # Output command result
ctx.output.table(items, columns)         # Output as table
ctx.output.info(message: str)            # Info message (hidden in JSON mode)
ctx.output.warning(message: str)         # Warning message
ctx.output.error(message: str)           # Error message
ctx.output.confirm(prompt: str) -> bool  # Confirmation (respects --yes)
```

## Errors

### HiveError

Base class for all Hive errors.

```python
class HiveError(Exception):
    exit_code: int = 1
```

### CommandError

Raised when a command fails due to user input or business logic.

```python
class CommandError(HiveError):
    def __init__(self, message: str, exit_code: int = 1): ...
```

**Usage**:
```python
@command(app)
async def delete(ctx, task_id: int) -> None:
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task {task_id} not found")
    ...
```

### ConfigurationError

Raised when configuration is missing or invalid.

```python
class ConfigurationError(HiveError):
    exit_code = 78  # EX_CONFIG
```

## CLI Generation Contract

The generated CLI follows these conventions:

### Standard Flags

All commands receive these flags automatically:

| Flag | Short | Description |
|------|-------|-------------|
| --json | | Output as JSON |
| --format | -f | Output format (json, table, csv) |
| --quiet | -q | Suppress non-essential output |
| --verbose | -v | Enable verbose logging |
| --yes | -y | Bypass confirmation prompts |
| --help | | Show help and exit |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | CLI usage error |
| 78 | Configuration error |

### Output Behavior

- **JSON mode**: Only command result is output (no status messages)
- **Table mode**: Rich-formatted tables with headers
- **CSV mode**: Standard CSV format

## ApplicationRegistry Contract

Read-only access to registration data.

```python
registry.commands: Mapping[str, CommandRegistration]
registry.queries: Mapping[str, QueryRegistration]
registry.entities: Mapping[str, EntityRegistration]
registry.screens: Mapping[str, ScreenRegistration]

registry.get_command(name: str) -> CommandRegistration | None
registry.list_commands() -> list[CommandRegistration]
registry.get_entity(name: str) -> EntityRegistration | None
registry.list_entities() -> list[EntityRegistration]
```
