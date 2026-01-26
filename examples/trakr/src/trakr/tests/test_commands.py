"""Unit tests for Trakr commands.

Demonstrates TestClient usage for command testing.
"""

from __future__ import annotations

import pytest
from hive.testing import TestClient

from trakr.app import app
from trakr.entities import reset_stores


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset stores before each test."""
    reset_stores()
    yield
    reset_stores()


class TestClientCommands:
    """Tests for client management commands."""

    @pytest.mark.asyncio
    async def test_create_client_success(self):
        """Test creating a client with valid data."""
        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name="Acme Corp",
                email="contact@acme.com",
                hourly_rate=150.0,
            )

            assert result.id == 1
            assert result.name == "Acme Corp"
            assert result.email == "contact@acme.com"
            assert float(result.hourly_rate) == 150.0

    @pytest.mark.asyncio
    async def test_create_client_strips_whitespace(self):
        """Test that client names are trimmed."""
        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name="  Acme Corp  ",
            )

            assert result.name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_create_client_empty_name_fails(self):
        """Test that empty names are rejected."""
        async with TestClient(app) as client:
            with pytest.raises(Exception) as exc_info:
                await client.invoke(
                    "create_client",
                    name="   ",  # Only whitespace
                )

            assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_not_found(self):
        """Test updating non-existent client."""
        from hive.errors import CommandError

        async with TestClient(app) as client:
            with pytest.raises(CommandError) as exc_info:
                await client.invoke(
                    "update_client",
                    client_id=999,
                    name="New Name",
                )

            assert "not found" in str(exc_info.value).lower()


class TestTimeCommands:
    """Tests for time tracking commands."""

    @pytest.fixture
    async def setup_project(self):
        """Create a client and project for testing."""
        async with TestClient(app) as client:
            await client.invoke("create_client", name="Test Client")
            await client.invoke(
                "create_project",
                client_id=1,
                name="Test Project",
            )

    @pytest.mark.asyncio
    async def test_start_timer_creates_running_entry(self, setup_project):
        """Test starting a timer."""
        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start timer
            result = await client.invoke(
                "start_timer",
                project_id=1,
                description="Working on feature",
            )

            assert result.is_running
            assert result.description == "Working on feature"
            assert result.project_id == 1

    @pytest.mark.asyncio
    async def test_stop_timer_ends_running_entry(self, setup_project):
        """Test stopping a running timer."""
        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")
            await client.invoke(
                "start_timer",
                project_id=1,
                description="Working",
            )

            # Stop
            result = await client.invoke("stop_timer")

            assert result is not None
            assert not result.is_running
            assert result.ended_at is not None

    @pytest.mark.asyncio
    async def test_stop_timer_when_none_running(self):
        """Test stopping when no timer is running."""
        async with TestClient(app) as client:
            result = await client.invoke("stop_timer")

            assert result is None

    @pytest.mark.asyncio
    async def test_start_timer_stops_previous(self, setup_project):
        """Test that starting a new timer stops the previous one."""
        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start first timer
            first = await client.invoke(
                "start_timer",
                project_id=1,
                description="First task",
            )

            # Start second timer
            second = await client.invoke(
                "start_timer",
                project_id=1,
                description="Second task",
            )

            # Verify first is stopped
            from trakr.entities import get_store

            entries = get_store("time_entry")
            first_entry = entries[first.id]

            assert not first_entry.is_running
            assert second.is_running


class TestQueryCaching:
    """Tests for query caching behavior."""

    @pytest.mark.asyncio
    async def test_list_clients_cached(self):
        """Test that list_clients returns cached results."""
        async with TestClient(app) as client:
            # Create a client
            await client.invoke("create_client", name="Test")

            # Query twice
            first = await client.query("list_clients")
            second = await client.query("list_clients")

            # Both should return the same data
            assert len(first) == len(second)
            assert first[0].id == second[0].id
