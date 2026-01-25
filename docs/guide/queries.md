# Queries

Queries are read-only operations that retrieve data without modifying state. They form the read side of Hive's command-query separation pattern and support optional caching.

## Basic Usage

Use the `@query` decorator to register an async function:

```python
from hive import App, query

app = App("tasks")

@query(app)
async def list_tasks(ctx) -> list[Task]:
    """List all tasks."""
    result = await ctx.db.execute(select(Task))
    return result.scalars().all()
```

## The ExecutionContext

Like commands, queries receive an `ExecutionContext` as their first parameter:

```python
from sqlmodel import select

@query(app, entities=[Task])
async def search(ctx, keyword: str) -> list[Task]:
    """Search tasks by keyword."""
    stmt = select(Task).where(Task.title.contains(keyword))
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

!!! warning "Read-Only Operations"
    Queries should never modify data. They have read-only access to the database.
    Use commands for any state-modifying operations.

## Decorator Parameters

### entities

Specify related entity classes for cache invalidation:

```python
@query(app, entities=[Task, Project])
async def tasks_by_project(ctx, project_id: int) -> list[Task]:
    """Get all tasks for a project."""
    stmt = select(Task).where(Task.project_id == project_id)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

When a command modifies these entities, Hive automatically invalidates this query's cache.

### cache_ttl

Enable caching with a time-to-live in seconds:

```python
@query(app, entities=[Task], cache_ttl=300)  # Cache for 5 minutes
async def list_tasks(ctx, completed: bool = False) -> list[Task]:
    """List tasks with caching."""
    stmt = select(Task).where(Task.completed == completed)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

!!! info "Cache Behavior"
    - Cache key is generated from query name and parameter values
    - Cache is automatically invalidated when related entities are modified
    - Set `cache_ttl=None` (default) to disable caching

### name

Override the query name (defaults to function name):

```python
@query(app, name="all")
async def list_all_tasks(ctx) -> list[Task]:
    """This becomes 'all' in the CLI."""
    ...
```

## Caching Strategies

### Simple Caching

Cache results for a fixed duration:

```python
@query(app, entities=[Task], cache_ttl=60)  # 1 minute
async def active_tasks(ctx) -> list[Task]:
    """Get active tasks (cached for 1 minute)."""
    stmt = select(Task).where(Task.completed == False)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

### Parameter-Based Caching

Different parameter values create separate cache entries:

```python
@query(app, entities=[Task], cache_ttl=300)
async def tasks_by_status(ctx, status: str) -> list[Task]:
    """Get tasks by status (each status cached separately)."""
    stmt = select(Task).where(Task.status == status)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

Calling `tasks_by_status(ctx, "pending")` and `tasks_by_status(ctx, "done")` creates two independent cache entries.

### Automatic Invalidation

When a command modifies entities, related query caches are invalidated:

```python
@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False

# This query's cache is linked to Task
@query(app, entities=[Task], cache_ttl=300)
async def count_tasks(ctx) -> int:
    """Count total tasks."""
    result = await ctx.db.execute(select(func.count(Task.id)))
    return result.scalar_one()

# This command invalidates the count_tasks cache
@command(app, entities=[Task])
async def add(ctx, title: str) -> Task:
    """Add a task (invalidates count_tasks cache)."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    return task
```

## Parameter Types

Use refinement types for automatic validation:

```python
from hive.types import PositiveInt, NonEmptyStr

@query(app, entities=[Task])
async def get_task(ctx, task_id: PositiveInt) -> Task | None:
    """Get a task by ID (ID must be positive)."""
    return await ctx.db.get(Task, task_id)

@query(app, entities=[Task])
async def search(ctx, keyword: NonEmptyStr, limit: PositiveInt = 10) -> list[Task]:
    """Search tasks (keyword required, limit positive)."""
    stmt = select(Task).where(Task.title.contains(keyword)).limit(limit)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

## Common Patterns

### Pagination

```python
from hive.types import PositiveInt, NonNegativeInt

@query(app, entities=[Task])
async def list_tasks(
    ctx,
    offset: NonNegativeInt = 0,
    limit: PositiveInt = 20,
) -> list[Task]:
    """List tasks with pagination."""
    stmt = select(Task).offset(offset).limit(limit)
    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

### Filtering

```python
@query(app, entities=[Task])
async def filter_tasks(
    ctx,
    completed: bool | None = None,
    priority: int | None = None,
    project_id: int | None = None,
) -> list[Task]:
    """Filter tasks with optional criteria."""
    stmt = select(Task)

    if completed is not None:
        stmt = stmt.where(Task.completed == completed)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)

    result = await ctx.db.execute(stmt)
    return result.scalars().all()
```

### Aggregation

```python
from sqlmodel import func

@query(app, entities=[Task], cache_ttl=60)
async def task_stats(ctx) -> dict:
    """Get task statistics."""
    total = await ctx.db.execute(select(func.count(Task.id)))
    completed = await ctx.db.execute(
        select(func.count(Task.id)).where(Task.completed.is_(True))
    )

    return {
        "total": total.scalar_one(),
        "completed": completed.scalar_one(),
        "pending": total.scalar_one() - completed.scalar_one(),
    }
```

## Testing Queries

Use `MockExecutionContext` for testing:

```python
from hive.testing import MockExecutionContext

async def test_list_tasks():
    async with MockExecutionContext() as ctx:
        # Setup mock data
        ctx.db.execute.return_value.scalars.return_value.all.return_value = [
            Task(id=1, title="Test"),
        ]

        # Execute the query
        tasks = await list_tasks(ctx)

        # Verify results
        assert len(tasks) == 1
        assert tasks[0].title == "Test"
```

## Best Practices

!!! success "Do"
    - Keep queries focused on data retrieval
    - Use appropriate cache TTL values
    - Specify related entities for cache invalidation
    - Return typed data structures
    - Use pagination for large result sets

!!! failure "Don't"
    - Modify data in queries
    - Use excessively long cache TTLs for frequently changing data
    - Return raw database rows (use models)
    - Ignore performance for large datasets
