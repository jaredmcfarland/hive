# Quick Start

Build your first Hive application in minutes. This guide walks you through creating
a simple task manager with CLI, database persistence, and optional TUI interface.

## Create a New Project

Use the Hive CLI to scaffold a new project:

```bash
hive new myapp
cd myapp
```

This creates a project structure:

```
myapp/
├── pyproject.toml
├── src/
│   └── myapp/
│       ├── __init__.py
│       └── app.py
└── tests/
    └── test_app.py
```

!!! tip "Optional Features"
    Add TUI, MCP, or REST support during project creation:

    ```bash
    hive new myapp --features tui,mcp,rest
    ```

## Your First Application

Open `src/myapp/app.py` and replace its contents:

```python
"""A simple task manager built with Hive."""

from datetime import datetime
from typing import Optional

from pydantic import Field
from sqlmodel import SQLModel

from hive import App, command, entity, query

# Create the application
app = App("tasks", description="A simple task manager")


# Define an entity (database table)
@entity(app)
class Task(SQLModel, table=True):
    """A task to be completed."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(description="Task title")
    completed: bool = Field(default=False, description="Whether task is done")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the task was created"
    )


# Define a command (state-modifying operation)
@command(app, entities=[Task])
async def add(ctx, title: str) -> Task:
    """Add a new task.

    Args:
        ctx: Execution context with database access
        title: The title of the task to create

    Returns:
        The created task
    """
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    await ctx.db.refresh(task)
    ctx.output.success(f"Created task: {task.title}")
    return task


@command(app, entities=[Task])
async def complete(ctx, task_id: int) -> Task:
    """Mark a task as completed.

    Args:
        ctx: Execution context
        task_id: ID of the task to complete

    Returns:
        The updated task
    """
    task = await ctx.db.get(Task, task_id)
    if not task:
        ctx.output.error(f"Task {task_id} not found")
        raise ValueError(f"Task {task_id} not found")

    task.completed = True
    await ctx.db.commit()
    ctx.output.success(f"Completed: {task.title}")
    return task


# Define a query (read-only operation)
@query(app, entities=[Task])
async def list_tasks(ctx, show_completed: bool = False) -> list[Task]:
    """List all tasks.

    Args:
        ctx: Execution context
        show_completed: Include completed tasks in output

    Returns:
        List of tasks matching the filter
    """
    from sqlmodel import select

    statement = select(Task)
    if not show_completed:
        statement = statement.where(Task.completed == False)  # noqa: E712

    result = await ctx.db.exec(statement)
    return list(result.all())
```

## Run Your Application

Start the development server with hot reload:

```bash
hive dev
```

This generates a CLI from your decorated code. Use it directly:

```bash
# Add tasks
myapp add "Write documentation"
myapp add "Review pull request"

# List tasks
myapp list-tasks

# Complete a task
myapp complete 1

# List including completed
myapp list-tasks --show-completed
```

## JSON Output

Every Hive command supports machine-readable JSON output with the `--json` flag:

```bash
myapp list-tasks --json
```

```json
[
  {
    "id": 2,
    "title": "Review pull request",
    "completed": false,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

!!! info "CLI-First Design"
    The `--json` flag enables seamless integration with other tools:

    ```bash
    # Pipe to jq for filtering
    myapp list-tasks --json | jq '.[].title'

    # Use in scripts
    TASK_COUNT=$(myapp list-tasks --json | jq length)
    ```

## What's Next?

You've created a working Hive application with:

- **Entity**: `Task` - A database model with automatic migrations
- **Command**: `add`, `complete` - State-modifying operations
- **Query**: `list_tasks` - Read-only operation with filtering

Continue learning:

- [Core Concepts](concepts.md) - Understand Hive's architecture
- [Entities Guide](../guide/entities.md) - Advanced entity patterns
- [Commands](../guide/commands.md) - Command patterns and contracts
- [Screens](../guide/screens.md) - Build interactive terminal UIs
