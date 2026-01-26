"""Property-based tests for Trakr.

Demonstrates Hypothesis integration for thorough testing with real database.
"""

from __future__ import annotations

import pytest
from hive.runtime.context import ExecutionContext
from hive.testing import strategy_for_type
from hive.types import NonEmptyStr, NonNegativeFloat
from hypothesis import given, settings
from hypothesis import strategies as st

from trakr.commands.clients import create_client
from trakr.commands.projects import create_project
from trakr.commands.time import start_timer
from trakr.queries import list_time_entries

from .conftest import create_fresh_db


class TestClientProperties:
    """Property-based tests for client commands."""

    @given(
        name=strategy_for_type(NonEmptyStr),
        rate=strategy_for_type(NonNegativeFloat),
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_create_client_always_strips_name(
        self,
        name: str,
        rate: float,
    ):
        """Property: Created client name has no leading/trailing whitespace."""
        db_settings = await create_fresh_db()

        async with ExecutionContext(settings=db_settings) as ctx:
            result = await create_client(
                ctx,
                name=name,
                hourly_rate=rate,
            )

            # Property: name is trimmed
            assert result.name == result.name.strip()
            # Property: name equals trimmed input
            assert result.name == name.strip()

    @given(
        name=strategy_for_type(NonEmptyStr),
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_created_client_has_positive_id(self, name: str):
        """Property: Created clients always have positive IDs."""
        db_settings = await create_fresh_db()

        async with ExecutionContext(settings=db_settings) as ctx:
            result = await create_client(ctx, name=name)

            assert result.id is not None
            assert result.id > 0


class TestTimeEntryProperties:
    """Property-based tests for time entries."""

    @given(
        description=strategy_for_type(NonEmptyStr),
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_started_timer_is_always_running(
        self,
        description: str,
    ):
        """Property: A just-started timer is always in running state."""
        db_settings = await create_fresh_db()

        async with ExecutionContext(settings=db_settings) as ctx:
            # Setup
            await create_client(ctx, name="Test")
            await create_project(ctx, client_id=1, name="Proj")

            # Start timer
            result = await start_timer(
                ctx,
                project_id=1,
                description=description,
            )

            # Property: timer is running
            assert result.is_running
            assert result.ended_at is None

    @given(
        count=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=5)
    @pytest.mark.asyncio
    async def test_only_one_timer_runs_at_a_time(self, count: int):
        """Property: At most one timer can be running at any time."""
        db_settings = await create_fresh_db()

        async with ExecutionContext(settings=db_settings) as ctx:
            # Setup
            await create_client(ctx, name="Test")
            await create_project(ctx, client_id=1, name="Proj")

            # Start multiple timers
            for i in range(count):
                await start_timer(
                    ctx,
                    project_id=1,
                    description=f"Task {i}",
                )

            # Count running timers
            entries = await list_time_entries(ctx, days=1)
            running = [e for e in entries if e.is_running]

            # Property: at most one running
            assert len(running) <= 1


class TestInvariantProperties:
    """Tests for data invariants."""

    @given(
        rate=strategy_for_type(NonNegativeFloat),
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_client_rate_never_negative(self, rate: float):
        """Property: Client hourly rate is never negative."""
        db_settings = await create_fresh_db()

        async with ExecutionContext(settings=db_settings) as ctx:
            result = await create_client(
                ctx,
                name="Test",
                hourly_rate=rate,
            )

            assert float(result.hourly_rate) >= 0
