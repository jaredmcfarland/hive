# App

The `App` class is the central entry point for building Hive applications. It manages the registry of commands, queries, entities, screens, and services, and provides methods to generate CLI, TUI, and API interfaces.

## Basic Usage

```python
from hive import App, command

app = App(
    name="my-app",
    version="1.0.0",
    description="My awesome application",
)

@command(app)
async def hello(ctx, name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    app.cli()()
```

## Constructor

```python
App(
    name: str,
    version: str = "0.1.0",
    description: str = "",
    *,
    cli_command: str | None = None,
    tui_title: str | None = None,
    database: str | None = None,
    mcp_server: bool = False,
    rest_api: bool = False,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Package name (e.g., "my-app") |
| `version` | `str` | `"0.1.0"` | Semantic version string |
| `description` | `str` | `""` | Human-readable description |
| `cli_command` | `str \| None` | `None` | CLI entry point name (defaults to name) |
| `tui_title` | `str \| None` | `None` | TUI window title |
| `database` | `str \| None` | `None` | Database URL (defaults to `sqlite:///~/.{name}/data.db`) |
| `mcp_server` | `bool` | `False` | Enable MCP server generation |
| `rest_api` | `bool` | `False` | Enable REST API generation |

## Properties

### `name`

```python
@property
def name(self) -> str:
    """Application name."""
```

### `version`

```python
@property
def version(self) -> str:
    """Application version."""
```

### `description`

```python
@property
def description(self) -> str:
    """Application description."""
```

### `registry`

```python
@property
def registry(self) -> ApplicationRegistry:
    """Access to registration data (read-only)."""
```

The registry provides access to all registered commands, queries, entities, screens, and services.

## Methods

### `cli()`

```python
def cli(self) -> typer.Typer:
    """Get the generated Typer CLI application."""
```

Returns a configured Typer app with all registered commands.

**Example:**

```python
app = App("myapp")

@command(app)
async def greet(ctx, name: str) -> str:
    return f"Hello, {name}!"

# Run the CLI
if __name__ == "__main__":
    app.cli()()
```

### `validate()`

```python
def validate(self) -> list[ValidationError]:
    """Validate all registrations."""
```

Checks for:

- Commands/queries referencing unregistered entities
- Return types that aren't JSON-serializable
- Multiple default screens
- Other consistency issues

Returns a list of validation errors found. Empty if valid.

**Example:**

```python
app = App("myapp")

# Register commands and entities...

errors = app.validate()
if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

## Full Example

```python
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr
from sqlmodel import Field, SQLModel

app = App(
    name="task-manager",
    version="1.0.0",
    description="A simple task manager",
    database="sqlite:///tasks.db",
)

@entity(app)
class Task(SQLModel, table=True):
    """A task in the system."""
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False

@command(app, entities=[Task])
async def add_task(ctx, title: NonEmptyStr) -> Task:
    """Add a new task."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    return task

@command(app, entities=[Task])
async def complete_task(ctx, task_id: PositiveInt) -> Task:
    """Mark a task as completed."""
    task = await ctx.db.get(Task, task_id)
    task.completed = True
    await ctx.db.commit()
    return task

@query(app, entities=[Task])
async def list_tasks(ctx, completed: bool | None = None) -> list[Task]:
    """List tasks, optionally filtered by completion status."""
    query = ctx.db.query(Task)
    if completed is not None:
        query = query.filter(Task.completed == completed)
    return await query.all()

if __name__ == "__main__":
    # Validate before running
    errors = app.validate()
    if errors:
        for error in errors:
            print(f"Error: {error}")
        exit(1)

    # Run the CLI
    app.cli()()
```

## API Reference

::: hive.App
    options:
      show_root_heading: true
      show_source: false
      members:
        - __init__
        - name
        - version
        - description
        - registry
        - cli
        - validate
