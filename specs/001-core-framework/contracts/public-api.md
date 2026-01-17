# Public API Contract: Core Framework

**Feature**: 001-core-framework
**Created**: 2026-01-11
**Updated**: 2026-01-17

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

# Refinement types from hive.types
from hive.types import (
    # Numeric types
    PositiveInt,
    NonNegativeInt,
    NegativeInt,
    PositiveFloat,
    NonNegativeFloat,
    UnitInterval,
    Percentage,
    Probability,
    Port,
    HttpStatusCode,
    Year, Month, Day,
    Hour, Minute, Second,

    # String types
    NonEmptyStr,
    TrimmedStr,
    Identifier,
    Slug,
    Email,
    Url,
    FilePath,

    # Introspection
    extract_constraints,
    TypeConstraints,
)

# Contract decorators from hive.contracts
from hive.contracts import (
    requires,
    ensures,
    invariant,
)

# Testing utilities from hive.testing
from hive.testing import (
    strategy_for_type,
    MockExecutionContext,
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

## Refinement Types

Type aliases using `Annotated` with beartype validators for runtime validation.

### Numeric Types

```python
from hive.types import PositiveInt, Port, Percentage

def my_func(
    count: PositiveInt,       # int > 0
    port: Port,               # 1 <= int <= 65535
    progress: Percentage,     # 0.0 <= float <= 100.0
) -> None: ...
```

### String Types

```python
from hive.types import NonEmptyStr, Email, Slug

def my_func(
    name: NonEmptyStr,        # len > 0
    email: Email,             # valid email format
    slug: Slug,               # lowercase, hyphens only
) -> None: ...
```

### Constraint Introspection

```python
from hive.types import extract_constraints, Port

constraints = extract_constraints(Port)
# TypeConstraints(
#     min_value=1,
#     max_value=65535,
#     min_length=None,
#     max_length=None,
#     pattern=None,
#     description="integer between 1 and 65535"
# )
```

## Contract Decorators

Design-by-contract decorators wrapping the deal library.

### @requires (Precondition)

```python
from hive.contracts import requires

@command(app)
@requires(lambda ctx, user_id: user_id > 0, "User ID must be positive")
async def get_user(ctx, user_id: int) -> User:
    ...
```

**On violation**: Raises `CommandError` with the specified message.

### @ensures (Postcondition)

```python
from hive.contracts import ensures

@command(app)
@ensures(lambda ctx, user_id, result: result.id == user_id, "Must return correct user")
async def get_user(ctx, user_id: int) -> User:
    ...
```

**On violation**: Raises `CommandError` with the specified message.

### @invariant (Class Invariant)

```python
from hive.contracts import invariant

@invariant(lambda self: self.balance >= 0, "Balance cannot be negative")
class Account:
    balance: float
```

**On violation**: Raises `CommandError` when invariant check fails.

## Testing Utilities

Hypothesis integration and mock context for testing.

### strategy_for_type

```python
from hypothesis import given
from hive.testing import strategy_for_type
from hive.types import PositiveInt, Email

@given(
    count=strategy_for_type(PositiveInt),
    email=strategy_for_type(Email),
)
def test_my_function(count, email):
    assert count > 0
    assert "@" in email
```

**Returns**: A Hypothesis strategy that generates only values satisfying the type constraints.

### MockExecutionContext

```python
from hive.testing import MockExecutionContext

async def test_my_command():
    async with MockExecutionContext() as ctx:
        result = await my_command(ctx, arg="value")

        # Verify database interactions
        assert ctx.db.add.called
        assert ctx.db.commit.called

        # Verify output
        assert ctx.output.result.called
```

**Properties**:
- `ctx.db` - MagicMock for database session
- `ctx.config` - Test AppSettings instance
- `ctx.output` - MagicMock for output formatter
- `ctx.command_name` - "test_command"
- `ctx.output_format` - OutputFormat.JSON
- `ctx.interactive` - False
