# Quickstart: Core Framework

**Feature**: 001-core-framework
**Date**: 2026-01-11

## Prerequisites

- Python 3.11+
- pip or uv package manager

## Installation

```bash
# From PyPI (when published)
pip install hive-framework

# From source (development)
git clone https://github.com/yourusername/hive.git
cd hive
pip install -e ".[dev]"
```

## Create Your First Hive Application

### 1. Create Application File

Create `app.py`:

```python
from hive import App, command, query, entity
from hive.types import Argument, Option
from sqlmodel import Field, SQLModel
from typing import Annotated
from pydantic import BaseModel

# Define the application
app = App(
    name="todo",
    version="0.1.0",
    description="A simple todo application",
    cli_command="todo",
)

# Define an entity (data model)
@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False

# Define result models
class TaskResult(BaseModel):
    task: Task
    message: str

class TaskListResult(BaseModel):
    tasks: list[Task]
    total: int

# Define a command
@command(app, entities=[Task])
async def add(
    ctx,
    title: Annotated[str, Argument(help="Task title")],
) -> TaskResult:
    """Add a new task to the list."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    await ctx.db.refresh(task)
    return TaskResult(task=task, message=f"Created task #{task.id}")

# Define a query
@query(app, entities=[Task])
async def list(
    ctx,
    all: Annotated[bool, Option("--all", "-a", help="Include completed")] = False,
) -> TaskListResult:
    """List all tasks."""
    from sqlmodel import select
    stmt = select(Task)
    if not all:
        stmt = stmt.where(Task.completed == False)
    tasks = await ctx.db.exec(stmt)
    return TaskListResult(tasks=list(tasks), total=len(tasks))

# Define another command
@command(app, entities=[Task])
async def complete(
    ctx,
    task_id: Annotated[int, Argument(help="Task ID")],
) -> TaskResult:
    """Mark a task as completed."""
    from hive import CommandError

    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task #{task_id} not found")

    task.completed = True
    await ctx.db.commit()
    return TaskResult(task=task, message=f"Completed task #{task_id}")
```

### 2. Run the CLI

```bash
# Show help
python -m todo --help

# Add a task
python -m todo add "Buy groceries"

# List tasks
python -m todo list

# List with JSON output
python -m todo list --json

# Complete a task
python -m todo complete 1

# List including completed
python -m todo list --all
```

### 3. Expected Output

```bash
$ python -m todo add "Buy groceries"
Created task #1

$ python -m todo list
┏━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Title         ┃ Status   ┃
┡━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│  1 │ Buy groceries │ pending  │
└────┴───────────────┴──────────┘

$ python -m todo list --json
{"tasks": [{"id": 1, "title": "Buy groceries", "completed": false}], "total": 1}

$ python -m todo complete 1
Completed task #1
```

## Verify Installation

Run the following to verify the framework is working:

```bash
# Check version
python -c "import hive; print(hive.__version__)"

# Verify decorators register correctly
python -c "
from app import app
print(f'Commands: {list(app.registry.commands.keys())}')
print(f'Queries: {list(app.registry.queries.keys())}')
print(f'Entities: {list(app.registry.entities.keys())}')
"
```

Expected output:
```
0.1.0
Commands: ['add', 'complete']
Queries: ['list']
Entities: ['Task']
```

## Common Issues

### Import Errors

If you see `ModuleNotFoundError: No module named 'hive'`:
- Ensure you've installed the package: `pip install hive-framework`
- If developing locally, ensure you've run `pip install -e .` from the repo root

### Database Errors

If you see database-related errors:
- The default database is SQLite at `~/.todo/data.db`
- Ensure the directory exists: `mkdir -p ~/.todo`
- To reset: `rm ~/.todo/data.db`

### Type Errors

If you see type-related errors in decorators:
- Ensure Python 3.11+ is being used
- Check that all function parameters have type annotations
- Return types should be Pydantic models or primitives

## Next Steps

1. Add more commands and queries
2. Define additional entities with relationships
3. Add a TUI with `@screen` decorator (Phase 2)
4. Enable MCP server for AI agent integration (Phase 3)

See the full documentation at [hive.dev/docs](https://hive.dev/docs).
