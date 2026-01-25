"""CRUD queries for task management.

Demonstrates query definition with filtering and read-only operations.
Uses in-memory storage for simplicity.
"""

from __future__ import annotations

from hive.contracts import requires
from hive.core.decorators import query
from hive.runtime.context import ExecutionContext

from crud.app import app
from crud.entities import Task, get_task_store


@query(app, cache_ttl=60)
async def list_tasks(
    ctx: ExecutionContext,  # noqa: ARG001
    completed: bool | None = None,
) -> list[Task]:
    """List all tasks, optionally filtered by completion status.

    Args:
        ctx: Execution context (unused for in-memory storage).
        completed: Filter by completion status (None = all tasks).

    Returns:
        List of matching tasks, ordered by priority.

    Example:
        >>> tasks = await list_tasks(ctx)
        >>> pending = await list_tasks(ctx, completed=False)
    """
    tasks = list(get_task_store().values())

    if completed is not None:
        tasks = [t for t in tasks if t.completed == completed]

    # Sort by priority (lower = higher priority)
    tasks.sort(key=lambda t: t.priority)
    return tasks


@query(app)
@requires(lambda _ctx, task_id, **_kw: task_id > 0, "Task ID must be positive")
async def get_task(ctx: ExecutionContext, task_id: int) -> Task | None:  # noqa: ARG001
    """Get a task by ID.

    Args:
        ctx: Execution context (unused for in-memory storage).
        task_id: ID of the task to retrieve.

    Returns:
        The Task if found, None otherwise.

    Example:
        >>> task = await get_task(ctx, task_id=1)
        >>> if task:
        ...     print(task.title)
    """
    tasks = get_task_store()
    return tasks.get(task_id)
