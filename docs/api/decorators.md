# Decorators

Hive provides decorators to register commands, queries, entities, screens, and services with your application. These decorators are applied at import time and enable automatic generation of CLI, TUI, and API interfaces.

## Overview

| Decorator | Purpose | Target |
|-----------|---------|--------|
| `@command` | State-modifying operations | Async functions |
| `@query` | Read-only operations | Async functions |
| `@entity` | Database table definitions | SQLModel classes |
| `@screen` | TUI screen definitions | Textual Screen classes |
| `@service` | External API clients | Factory functions |

## @command

Register a state-modifying operation (create, update, delete).

```python
from hive import App, command

app = App("myapp")

@command(app, entities=[Task])
async def add_task(ctx, title: str) -> Task:
    """Add a new task."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    return task
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | The application instance |
| `entities` | `list[type]` | `[]` | Related entity classes for documentation/cache invalidation |
| `name` | `str \| None` | `None` | Override command name (defaults to function name) |
| `aliases` | `list[str]` | `[]` | Alternative names for the command |
| `hidden` | `bool` | `False` | If True, hide from help text |

### Example with Options

```python
@command(app, entities=[Task], name="new", aliases=["create", "add"], hidden=False)
async def add_task(ctx, title: str, priority: int = 1) -> Task:
    """Create a new task with optional priority."""
    ...
```

## @query

Register a read-only operation with optional caching.

```python
from hive import App, query

app = App("myapp")

@query(app, entities=[Task], cache_ttl=300)
async def list_tasks(ctx, completed: bool = False) -> list[Task]:
    """List all tasks, optionally filtered by completion status."""
    ...
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | The application instance |
| `entities` | `list[type]` | `[]` | Related entity classes for cache invalidation |
| `cache_ttl` | `int \| None` | `None` | Cache time-to-live in seconds |
| `name` | `str \| None` | `None` | Override query name (defaults to function name) |

### Caching Example

```python
# Cache results for 5 minutes
@query(app, entities=[User], cache_ttl=300)
async def get_user_stats(ctx, user_id: int) -> dict:
    """Get user statistics (cached for 5 minutes)."""
    ...

# No caching
@query(app, entities=[Task])
async def search_tasks(ctx, query: str) -> list[Task]:
    """Search tasks by title (not cached)."""
    ...
```

## @entity

Register a SQLModel class as a database entity.

```python
from hive import App, entity
from sqlmodel import Field, SQLModel

app = App("myapp")

@entity(app)
class Task(SQLModel, table=True):
    """A task in the system."""
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False
    priority: int = 1
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | The application instance |

### Field Definitions

Use SQLModel's `Field` to define column attributes:

```python
from sqlmodel import Field, SQLModel
from datetime import datetime

@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=1, ge=1, le=5)
```

## @screen

Register a TUI screen for Textual-based interfaces.

```python
from hive import App, screen
from textual.screen import Screen
from textual.widgets import Static

app = App("myapp")

@screen(app, default=True, keybinding="d", queries=["list_tasks"])
class DashboardScreen(Screen):
    """Main dashboard showing task overview."""

    def compose(self):
        yield Static("Dashboard")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | The application instance |
| `default` | `bool` | `False` | If True, this is the startup screen |
| `keybinding` | `str \| None` | `None` | Global key to navigate to this screen |
| `name` | `str \| None` | `None` | Override screen name (defaults to class name) |
| `queries` | `list[str]` | `[]` | Query names to auto-load when screen mounts |

### Screen Navigation Example

```python
@screen(app, default=True, keybinding="1")
class HomeScreen(Screen):
    """Home screen."""
    ...

@screen(app, keybinding="2")
class TaskListScreen(Screen):
    """Task list screen."""
    ...

@screen(app, keybinding="3", queries=["get_settings"])
class SettingsScreen(Screen):
    """Settings screen with auto-loaded data."""
    ...
```

## @service

Register an external API client with credential management.

```python
from hive import App, service
import httpx

app = App("myapp")

@service(app, credentials="keyring:github_token")
def github_client(credentials: str) -> httpx.Client:
    """GitHub API client."""
    return httpx.Client(
        base_url="https://api.github.com",
        headers={"Authorization": f"token {credentials}"},
    )
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | The application instance |
| `credentials` | `str \| None` | `None` | Credential specification string |
| `name` | `str \| None` | `None` | Override service name (defaults to function name) |
| `cleanup` | `Callable` | `None` | Optional cleanup function called on context exit |

### Credential Specification

The `credentials` parameter supports multiple formats:

- `keyring:<service_name>` - System keyring lookup
- `env:<VAR_NAME>` - Environment variable
- Falls back to `HIVE_{SERVICE}_CREDENTIAL` environment variable

### Service with Cleanup

```python
@service(app, credentials="env:DATABASE_URL", cleanup=lambda db: db.close())
def database(credentials: str) -> Database:
    """Database connection."""
    return Database(credentials)
```

### Using Services in Commands

```python
@command(app)
async def list_repos(ctx) -> list[dict]:
    """List GitHub repositories."""
    client = ctx.services.github_client
    response = client.get("/user/repos")
    return response.json()
```

## Context Parameter

All commands and queries receive a `ctx` parameter providing:

| Attribute | Description |
|-----------|-------------|
| `ctx.db` | Async SQLModel session |
| `ctx.services.<name>` | Lazy-loaded service clients |
| `ctx.config` | Pydantic settings |
| `ctx.output` | Format-aware output (respects `--json`) |

```python
@command(app)
async def example(ctx, name: str) -> dict:
    """Example showing context usage."""
    # Database access
    result = await ctx.db.execute(select(Task))

    # Service access
    github = ctx.services.github_client

    # Configuration access
    debug = ctx.config.debug

    # Output (respects --json flag)
    ctx.output.print(f"Hello, {name}!")

    return {"name": name}
```

## API Reference

::: hive.command
    options:
      show_root_heading: true
      show_source: false

::: hive.query
    options:
      show_root_heading: true
      show_source: false

::: hive.entity
    options:
      show_root_heading: true
      show_source: false

::: hive.screen
    options:
      show_root_heading: true
      show_source: false

::: hive.service
    options:
      show_root_heading: true
      show_source: false
