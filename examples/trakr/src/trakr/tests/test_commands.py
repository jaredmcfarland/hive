"""Integration tests for Trakr commands.

Tests commands against a real SQLite database.
"""

from __future__ import annotations

import pytest
from hive.errors import CommandError
from hive.runtime.config import AppSettings
from hive.runtime.context import ExecutionContext

from trakr.commands.clients import create_client, update_client
from trakr.commands.projects import create_project
from trakr.commands.time import start_timer, stop_timer
from trakr.queries import list_clients, list_time_entries


class TestClientCommands:
    """Tests for client management commands."""

    @pytest.mark.asyncio
    async def test_create_client_success(self, db_settings: AppSettings):
        """Test creating a client with valid data."""
        async with ExecutionContext(settings=db_settings) as ctx:
            result = await create_client(
                ctx,
                name="Acme Corp",
                email="contact@acme.com",
                hourly_rate=150.0,
            )

            assert result.id is not None
            assert result.id > 0
            assert result.name == "Acme Corp"
            assert result.email == "contact@acme.com"
            assert float(result.hourly_rate) == 150.0

    @pytest.mark.asyncio
    async def test_create_client_strips_whitespace(self, db_settings: AppSettings):
        """Test that client names are trimmed."""
        async with ExecutionContext(settings=db_settings) as ctx:
            result = await create_client(
                ctx,
                name="  Acme Corp  ",
            )

            assert result.name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_create_client_empty_name_fails(self, db_settings: AppSettings):
        """Test that empty names are rejected."""
        async with ExecutionContext(settings=db_settings) as ctx:
            with pytest.raises(Exception) as exc_info:
                await create_client(
                    ctx,
                    name="   ",  # Only whitespace
                )

            assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_not_found(self, db_settings: AppSettings):
        """Test updating non-existent client."""
        async with ExecutionContext(settings=db_settings) as ctx:
            with pytest.raises(CommandError) as exc_info:
                await update_client(
                    ctx,
                    client_id=999,
                    name="New Name",
                )

            assert "not found" in str(exc_info.value).lower()


class TestTimeCommands:
    """Tests for time tracking commands."""

    @pytest.mark.asyncio
    async def test_start_timer_creates_running_entry(self, db_settings: AppSettings):
        """Test starting a timer."""
        async with ExecutionContext(settings=db_settings) as ctx:
            # Setup
            await create_client(ctx, name="Test")
            await create_project(ctx, client_id=1, name="Proj")

            # Start timer
            result = await start_timer(
                ctx,
                project_id=1,
                description="Working on feature",
            )

            assert result.is_running
            assert result.description == "Working on feature"
            assert result.project_id == 1

    @pytest.mark.asyncio
    async def test_stop_timer_ends_running_entry(self, db_settings: AppSettings):
        """Test stopping a running timer."""
        async with ExecutionContext(settings=db_settings) as ctx:
            # Setup
            await create_client(ctx, name="Test")
            await create_project(ctx, client_id=1, name="Proj")
            await start_timer(
                ctx,
                project_id=1,
                description="Working",
            )

            # Stop
            result = await stop_timer(ctx)

            assert result is not None
            assert not result.is_running
            assert result.ended_at is not None

    @pytest.mark.asyncio
    async def test_stop_timer_when_none_running(self, db_settings: AppSettings):
        """Test stopping when no timer is running."""
        async with ExecutionContext(settings=db_settings) as ctx:
            result = await stop_timer(ctx)

            assert result is None

    @pytest.mark.asyncio
    async def test_start_timer_stops_previous(self, db_settings: AppSettings):
        """Test that starting a new timer stops the previous one."""
        async with ExecutionContext(settings=db_settings) as ctx:
            # Setup
            await create_client(ctx, name="Test")
            await create_project(ctx, client_id=1, name="Proj")

            # Start first timer
            first = await start_timer(
                ctx,
                project_id=1,
                description="First task",
            )
            first_id = first.id

            # Start second timer
            second = await start_timer(
                ctx,
                project_id=1,
                description="Second task",
            )

            # Verify first is stopped by querying time entries
            entries = await list_time_entries(ctx, days=1)
            first_entry = next((e for e in entries if e.id == first_id), None)

            assert first_entry is not None
            assert not first_entry.is_running
            assert second.is_running


class TestQueryCaching:
    """Tests for query behavior."""

    @pytest.mark.asyncio
    async def test_list_clients_returns_created_clients(self, db_settings: AppSettings):
        """Test that list_clients returns created clients."""
        async with ExecutionContext(settings=db_settings) as ctx:
            # Create a client
            await create_client(ctx, name="Test")

            # Query
            clients = await list_clients(ctx)

            assert len(clients) == 1
            assert clients[0].name == "Test"
            assert clients[0].id is not None
