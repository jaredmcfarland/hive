"""CRUD commands for task management.

Demonstrates command definition with contracts and proper error handling.
Uses in-memory storage for simplicity.
"""

from __future__ import annotations

from hive.contracts import ensures, requires
from hive.core.decorators import command
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext

from crud.app import app
from crud.entities import Task, generate_task_id, get_task_store


@command(app)
@requires(lambda _ctx, title, **_kw: len(title.strip()) > 0, "Title cannot be empty")
@requires(lambda _ctx, _title, priority=1, **_kw: priority > 0, "Priority must be positive")
@ensures(
    lambda _ctx, title, result, **_kw: result.title == title.strip(),
    "Result title must match input",
)
async def create_task(
    ctx: ExecutionContext,  # noqa: ARG001
    title: str,
    priority: int = 1,
) -> Task:
    """Create a new task.

    Args:
        ctx: Execution context (unused for in-memory storage).
        title: Task title (cannot be empty).
        priority: Priority level (default 1, must be positive).

    Returns:
        The created Task with assigned ID.

    Raises:
        CommandError: If title is empty or priority is not positive.

    Example:
        >>> task = await create_task(ctx, title="Buy groceries", priority=2)
        >>> print(task.id)
        1
    """
    task_id = generate_task_id()
    task = Task(id=task_id, title=title.strip(), priority=priority)
    tasks = get_task_store()
    tasks[task_id] = task
    return task


@command(app)
@requires(lambda _ctx, task_id, **_kw: task_id > 0, "Task ID must be positive")
async def complete_task(ctx: ExecutionContext, task_id: int) -> Task:  # noqa: ARG001
    """Mark a task as completed.

    Args:
        ctx: Execution context (unused for in-memory storage).
        task_id: ID of the task to complete.

    Returns:
        The updated Task.

    Raises:
        CommandError: If task not found or ID is not positive.

    Example:
        >>> task = await complete_task(ctx, task_id=1)
        >>> print(task.completed)
        True
    """
    tasks = get_task_store()
    task = tasks.get(task_id)

    if task is None:
        raise CommandError(f"Task {task_id} not found", exit_code=1)

    task.completed = True
    return task


@command(app)
@requires(lambda _ctx, task_id, **_kw: task_id > 0, "Task ID must be positive")
async def delete_task(ctx: ExecutionContext, task_id: int) -> bool:  # noqa: ARG001
    """Delete a task.

    Args:
        ctx: Execution context (unused for in-memory storage).
        task_id: ID of the task to delete.

    Returns:
        True if task was deleted, False if not found.

    Example:
        >>> deleted = await delete_task(ctx, task_id=1)
        >>> print(deleted)
        True
    """
    tasks = get_task_store()

    if task_id not in tasks:
        return False

    del tasks[task_id]
    return True
