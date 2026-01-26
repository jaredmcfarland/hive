"""Property-based tests for Trakr.

Demonstrates Hypothesis integration for thorough testing.
"""

from __future__ import annotations

import pytest
from hive.testing import TestClient, strategy_for_type
from hive.types import NonEmptyStr, NonNegativeFloat
from hypothesis import given, settings
from hypothesis import strategies as st

from trakr.app import app
from trakr.entities import reset_stores


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset stores before each test."""
    reset_stores()
    yield


class TestClientProperties:
    """Property-based tests for client commands."""

    @given(
        name=strategy_for_type(NonEmptyStr),
        rate=strategy_for_type(NonNegativeFloat),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_create_client_always_strips_name(
        self,
        name: str,
        rate: float,
    ):
        """Property: Created client name has no leading/trailing whitespace."""
        reset_stores()  # Reset between examples

        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
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
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_created_client_has_positive_id(self, name: str):
        """Property: Created clients always have positive IDs."""
        reset_stores()

        async with TestClient(app) as client:
            result = await client.invoke("create_client", name=name)

            assert result.id > 0


class TestTimeEntryProperties:
    """Property-based tests for time entries."""

    @given(
        description=strategy_for_type(NonEmptyStr),
        tags=st.lists(st.text(min_size=1, max_size=20), max_size=5),
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_started_timer_is_always_running(
        self,
        description: str,
        tags: list[str],
    ):
        """Property: A just-started timer is always in running state."""
        reset_stores()

        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start timer
            result = await client.invoke(
                "start_timer",
                project_id=1,
                description=description,
                tags=tags,
            )

            # Property: timer is running
            assert result.is_running
            assert result.ended_at is None

    @given(
        count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_only_one_timer_runs_at_a_time(self, count: int):
        """Property: At most one timer can be running at any time."""
        reset_stores()

        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start multiple timers
            for i in range(count):
                await client.invoke(
                    "start_timer",
                    project_id=1,
                    description=f"Task {i}",
                )

            # Count running timers
            entries = await client.query("list_time_entries", days=1)
            running = [e for e in entries if e.is_running]

            # Property: at most one running
            assert len(running) <= 1


class TestInvariantProperties:
    """Tests for data invariants."""

    @given(
        rate=strategy_for_type(NonNegativeFloat),
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_client_rate_never_negative(self, rate: float):
        """Property: Client hourly rate is never negative."""
        reset_stores()

        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name="Test",
                hourly_rate=rate,
            )

            assert float(result.hourly_rate) >= 0
