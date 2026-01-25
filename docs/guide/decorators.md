# Decorators

Hive uses Python decorators to register functions and classes with your application. These decorators are applied at import time, building a registry that enables automatic generation of CLI, TUI, MCP, and REST interfaces.

## Overview

| Decorator | Purpose | Target |
|-----------|---------|--------|
| `@entity` | Database table definitions | Class (SQLModel) |
| `@command` | State-modifying operations | Async function |
| `@query` | Read-only data retrieval | Async function |
| `@screen` | TUI screen definitions | Class (HiveScreen) |
| `@service` | External API clients | Factory function |

## How Registration Works

When you decorate a function or class, Hive extracts metadata and stores it in the application registry:

```python
from hive import App, command, query, entity

app = App("myapp")

@entity(app)
class Task(SQLModel, table=True):
    # Registered as EntityRegistration
    ...

@command(app, entities=[Task])
async def add(ctx, title: str) -> Task:
    # Registered as CommandRegistration
    ...

@query(app, entities=[Task])
async def list_tasks(ctx) -> list[Task]:
    # Registered as QueryRegistration
    ...
```

The registry enables:

- **CLI generation**: Typer commands with type-hint driven argument parsing
- **TUI generation**: Textual screens with reactive data binding
- **MCP generation**: FastMCP tools for AI agent integration
- **REST generation**: FastAPI endpoints with OpenAPI documentation
- **Schema export**: JSON Schema for cross-language consumption

## Decorator Quick Reference

### @entity

Registers a SQLModel class as a database table.

```python
@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(description="Task title")
    completed: bool = Field(default=False)
```

### @command

Registers an async function as a state-modifying operation.

```python
@command(app, entities=[Task])
async def add(ctx, title: str) -> Task:
    """Add a new task."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    return task
```

### @query

Registers an async function as a read-only operation.

```python
@query(app, entities=[Task], cache_ttl=300)
async def list_tasks(ctx, completed: bool = False) -> list[Task]:
    """List tasks with optional filter."""
    stmt = select(Task).where(Task.completed == completed)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

### @screen

Registers a Textual screen class for the TUI.

```python
@screen(app, default=True, keybinding="d", queries=["list_tasks"])
class DashboardScreen(HiveScreen):
    """Main dashboard view."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Footer()
```

### @service

Registers an external service factory with credential management.

```python
@service(app, credentials="keyring:github_token")
def github_client(credentials: str) -> httpx.Client:
    """GitHub API client."""
    return httpx.Client(
        base_url="https://api.github.com",
        headers={"Authorization": f"token {credentials}"},
    )
```

## Common Patterns

### Combining Decorators

Commands and queries commonly work with entities:

```python
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr

app = App("tasks")

@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    priority: int = 1

@command(app, entities=[Task])
async def create(ctx, title: NonEmptyStr, priority: PositiveInt = 1) -> Task:
    """Create a new task with validated inputs."""
    task = Task(title=title, priority=priority)
    ctx.db.add(task)
    await ctx.db.commit()
    return task

@query(app, entities=[Task], cache_ttl=60)
async def get(ctx, task_id: PositiveInt) -> Task | None:
    """Get a task by ID with caching."""
    return await ctx.db.get(Task, task_id)
```

### Using Services in Commands

Access registered services through the execution context:

```python
@command(app)
async def sync_issues(ctx) -> int:
    """Sync issues from GitHub."""
    client = ctx.services.github_client
    response = client.get("/repos/owner/repo/issues")
    issues = response.json()

    for issue in issues:
        # Process and store issues
        ...

    return len(issues)
```

!!! tip "Lazy Loading"
    Services are lazily instantiated on first access. Credentials are only
    resolved when the service is actually used.

## Next Steps

- [Commands](commands.md) - Deep dive into state-modifying operations
- [Queries](queries.md) - Learn about read-only operations and caching
- [Entities](entities.md) - Database modeling with SQLModel
- [Services](services.md) - External API integration
- [Screens](screens.md) - Building TUI interfaces
