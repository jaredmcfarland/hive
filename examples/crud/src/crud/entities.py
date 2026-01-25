"""Task entity for CRUD example.

Demonstrates entity definition with dataclasses and type validation.
Uses in-memory storage for simplicity (no database required).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Task:
    """A task in the task manager.

    Attributes:
        id: Unique task identifier (auto-generated).
        title: Task title (cannot be empty).
        description: Optional detailed description.
        priority: Priority level (1 = highest, must be positive).
        completed: Whether the task is done.
    """

    id: int
    title: str
    description: str | None = None
    priority: int = 1
    completed: bool = False


# In-memory task storage (for demo purposes)
_tasks: dict[int, Task] = {}
_next_id: int = 1


def get_task_store() -> dict[int, Task]:
    """Get the task storage dict."""
    return _tasks


def reset_task_store() -> None:
    """Reset task storage (for testing)."""
    global _tasks, _next_id  # noqa: PLW0603
    _tasks = {}
    _next_id = 1


def generate_task_id() -> int:
    """Generate the next task ID."""
    global _next_id  # noqa: PLW0603
    task_id = _next_id
    _next_id += 1
    return task_id
