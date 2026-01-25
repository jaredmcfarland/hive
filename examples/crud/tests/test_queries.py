"""Tests for CRUD queries.

Demonstrates testing queries with TestClient.
"""

import pytest
from hive.errors import CommandError
from hive.testing import TestClient

from crud import app
from crud.entities import reset_task_store


@pytest.fixture(autouse=True)
def reset_storage() -> None:
    """Reset task storage before each test."""
    reset_task_store()


class TestListTasks:
    """Tests for list_tasks query."""

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self) -> None:
        """List returns empty list when no tasks."""
        async with TestClient(app) as client:
            tasks = await client.query("list_tasks")
            assert tasks == []

    @pytest.mark.asyncio
    async def test_list_tasks_multiple(self) -> None:
        """List returns all tasks."""
        async with TestClient(app) as client:
            await client.invoke("create_task", title="Task 1", priority=2)
            await client.invoke("create_task", title="Task 2", priority=1)

            tasks = await client.query("list_tasks")
            assert len(tasks) == 2
            # Ordered by priority
            assert tasks[0].title == "Task 2"
            assert tasks[1].title == "Task 1"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_completed(self) -> None:
        """List can filter by completion status."""
        async with TestClient(app) as client:
            task1 = await client.invoke("create_task", title="Task 1")
            await client.invoke("create_task", title="Task 2")
            await client.invoke("complete_task", task_id=task1.id)

            # Get only completed
            completed = await client.query("list_tasks", completed=True)
            assert len(completed) == 1
            assert completed[0].title == "Task 1"

            # Get only pending
            pending = await client.query("list_tasks", completed=False)
            assert len(pending) == 1
            assert pending[0].title == "Task 2"


class TestGetTask:
    """Tests for get_task query."""

    @pytest.mark.asyncio
    async def test_get_task_exists(self) -> None:
        """Get existing task by ID."""
        async with TestClient(app) as client:
            created = await client.invoke("create_task", title="Test Task")
            task = await client.query("get_task", task_id=created.id)
            assert task is not None
            assert task.title == "Test Task"
            assert task.id == created.id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self) -> None:
        """Get nonexistent task returns None."""
        async with TestClient(app) as client:
            task = await client.query("get_task", task_id=999)
            assert task is None

    @pytest.mark.asyncio
    async def test_get_task_zero_id_fails(self) -> None:
        """Zero task_id raises CommandError."""
        async with TestClient(app) as client:
            with pytest.raises(CommandError):
                await client.query("get_task", task_id=0)
