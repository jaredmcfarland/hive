# Commands

Commands are state-modifying operations that create, update, or delete data. They form the write side of Hive's command-query separation pattern.

## Basic Usage

Use the `@command` decorator to register an async function:

```python
from hive import App, command

app = App("tasks")

@command(app)
async def add(ctx, title: str) -> Task:
    """Add a new task."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    return task
```

## The ExecutionContext

Every command receives an `ExecutionContext` as its first parameter (`ctx`). This provides access to:

| Property | Description |
|----------|-------------|
| `ctx.db` | Async SQLModel database session |
| `ctx.services` | Lazy-loaded service clients |
| `ctx.config` | Application configuration (Pydantic settings) |
| `ctx.output` | Format-aware output (respects `--json` flag) |

```python
@command(app, entities=[Task])
async def complete(ctx, task_id: int) -> Task:
    """Mark a task as complete."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task {task_id} not found")

    task.completed = True
    task.completed_at = datetime.now(UTC)
    await ctx.db.commit()

    ctx.output.success(f"Task '{task.title}' completed")
    return task
```

## Decorator Parameters

### entities

Specify related entity classes for documentation and cache invalidation:

```python
@command(app, entities=[Task, Project])
async def move_task(ctx, task_id: int, project_id: int) -> Task:
    """Move a task to a different project."""
    ...
```

When a command modifies entities, Hive automatically invalidates cached queries for those entities.

### name

Override the command name (defaults to function name):

```python
@command(app, name="create")
async def add_task(ctx, title: str) -> Task:
    """This becomes 'create' in the CLI."""
    ...
```

### aliases

Provide alternative names for the command:

```python
@command(app, aliases=["new", "n"])
async def add(ctx, title: str) -> Task:
    """Available as 'add', 'new', or 'n'."""
    ...
```

### hidden

Hide the command from help text:

```python
@command(app, hidden=True)
async def debug_dump(ctx) -> dict:
    """Internal debugging command."""
    ...
```

## Error Handling

Use `CommandError` for expected failures that should be reported to users:

```python
from hive.errors import CommandError

@command(app, entities=[Task])
async def delete(ctx, task_id: int) -> None:
    """Delete a task."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task {task_id} not found")

    if task.protected:
        raise CommandError(
            f"Task '{task.title}' is protected and cannot be deleted",
            exit_code=2
        )

    await ctx.db.delete(task)
    await ctx.db.commit()
```

!!! info "Exit Codes"
    `CommandError` accepts an optional `exit_code` parameter. The default is 1.
    Use specific exit codes to enable scripting and automation.

## Parameter Types

Hive extracts type information from function signatures for CLI argument parsing:

```python
from datetime import date
from hive.types import PositiveInt, NonEmptyStr, Percentage

@command(app, entities=[Task])
async def create(
    ctx,
    title: NonEmptyStr,                    # Required, non-empty string
    priority: PositiveInt = 1,             # Optional, must be > 0
    due_date: date | None = None,          # Optional date
    progress: Percentage = 0.0,            # 0.0-100.0
) -> Task:
    """Create a task with validated parameters."""
    ...
```

### Using Annotated for CLI Metadata

Provide additional CLI metadata with `Annotated`:

```python
from typing import Annotated
from hive.core.types import Argument, Option

@command(app, entities=[Task])
async def add(
    ctx,
    title: Annotated[str, Argument(help="Task title to create")],
    priority: Annotated[int, Option("--priority", "-p", help="Task priority")] = 1,
    tags: Annotated[list[str], Option("--tag", "-t", help="Add tags")] = [],
) -> Task:
    """Add a new task."""
    ...
```

This generates CLI help like:

```
Usage: myapp add [OPTIONS] TITLE

  Add a new task.

Arguments:
  TITLE  Task title to create [required]

Options:
  -p, --priority INTEGER  Task priority [default: 1]
  -t, --tag TEXT          Add tags
  --help                  Show this message and exit.
```

## Contracts

Add preconditions and postconditions for validation:

```python
from hive.contracts import requires, ensures

@command(app, entities=[Task])
@requires(lambda ctx, task_id: task_id > 0, "Task ID must be positive")
@ensures(lambda ctx, task_id, result: result is None or result.id == task_id)
async def get_task(ctx, task_id: int) -> Task | None:
    """Get a task by ID."""
    return await ctx.db.get(Task, task_id)
```

!!! tip "Contract Violations"
    Contract violations raise `CommandError` with a descriptive message,
    making them user-friendly error reports rather than stack traces.

## Testing Commands

Use `MockExecutionContext` for testing:

```python
from hive.testing import MockExecutionContext

async def test_add_task():
    async with MockExecutionContext() as ctx:
        # Execute the command
        task = await add(ctx, title="Test task")

        # Verify database interactions
        assert ctx.db.add.called
        assert ctx.db.commit.called

        # Verify return value
        assert task.title == "Test task"
```

## Best Practices

!!! success "Do"
    - Keep commands focused on a single operation
    - Use `CommandError` for user-facing errors
    - Validate inputs with refinement types and contracts
    - Return meaningful data for `--json` output
    - Document parameters and return values

!!! failure "Don't"
    - Perform read-only operations in commands (use queries)
    - Swallow exceptions silently
    - Print directly to stdout (use `ctx.output`)
    - Access global state outside the context
