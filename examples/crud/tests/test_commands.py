"""Tests for CRUD commands.

Demonstrates testing commands with contracts using TestClient.
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


class TestCreateTask:
    """Tests for create_task command."""

    @pytest.mark.asyncio
    async def test_create_task_success(self) -> None:
        """Create a task with valid inputs."""
        async with TestClient(app) as client:
            task = await client.invoke("create_task", title="Test Task", priority=1)
            assert task.title == "Test Task"
            assert task.priority == 1
            assert task.completed is False
            assert task.id is not None

    @pytest.mark.asyncio
    async def test_create_task_default_priority(self) -> None:
        """Create a task with default priority."""
        async with TestClient(app) as client:
            task = await client.invoke("create_task", title="Test Task")
            assert task.priority == 1

    @pytest.mark.asyncio
    async def test_create_task_strips_whitespace(self) -> None:
        """Title whitespace is stripped."""
        async with TestClient(app) as client:
            task = await client.invoke("create_task", title="  Test Task  ")
            assert task.title == "Test Task"

    @pytest.mark.asyncio
    async def test_create_task_empty_title_fails(self) -> None:
        """Empty title raises CommandError."""
        async with TestClient(app) as client:
            with pytest.raises(CommandError):
                await client.invoke("create_task", title="")

    @pytest.mark.asyncio
    async def test_create_task_zero_priority_fails(self) -> None:
        """Zero priority raises CommandError."""
        async with TestClient(app) as client:
            with pytest.raises(CommandError):
                await client.invoke("create_task", title="Test", priority=0)


class TestCompleteTask:
    """Tests for complete_task command."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self) -> None:
        """Complete an existing task."""
        async with TestClient(app) as client:
            task = await client.invoke("create_task", title="Test Task")
            completed = await client.invoke("complete_task", task_id=task.id)
            assert completed.completed is True
            assert completed.id == task.id

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task_fails(self) -> None:
        """Completing nonexistent task raises CommandError."""
        async with TestClient(app) as client:
            with pytest.raises(CommandError, match="not found"):
                await client.invoke("complete_task", task_id=999)

    @pytest.mark.asyncio
    async def test_complete_zero_id_fails(self) -> None:
        """Zero task_id raises CommandError."""
        async with TestClient(app) as client:
            with pytest.raises(CommandError):
                await client.invoke("complete_task", task_id=0)


class TestDeleteTask:
    """Tests for delete_task command."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self) -> None:
        """Delete an existing task."""
        async with TestClient(app) as client:
            task = await client.invoke("create_task", title="Test Task")
            deleted = await client.invoke("delete_task", task_id=task.id)
            assert deleted is True

            # Verify it's gone
            found = await client.query("get_task", task_id=task.id)
            assert found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(self) -> None:
        """Deleting nonexistent task returns False."""
        async with TestClient(app) as client:
            deleted = await client.invoke("delete_task", task_id=999)
            assert deleted is False

    @pytest.mark.asyncio
    async def test_delete_zero_id_fails(self) -> None:
        """Zero task_id raises CommandError."""
        async with TestClient(app) as client:
            with pytest.raises(CommandError):
                await client.invoke("delete_task", task_id=0)
