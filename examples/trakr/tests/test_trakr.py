"""Tests for trakr basic commands.

Tests the hello and status commands defined in trakr.app.
"""

from __future__ import annotations

import pytest
from hive.runtime.context import ExecutionContext

from trakr.app import app, hello, status


class TestHelloCommand:
    """Tests for the hello command."""

    @pytest.mark.asyncio
    async def test_hello_default_name(self) -> None:
        """Test hello with default name."""
        async with ExecutionContext(registry=app._registry) as ctx:
            result = await hello(ctx)

            assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_hello_custom_name(self) -> None:
        """Test hello with custom name."""
        async with ExecutionContext(registry=app._registry) as ctx:
            result = await hello(ctx, name="Alice")

            assert result == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_hello_empty_name(self) -> None:
        """Test hello with empty name."""
        async with ExecutionContext(registry=app._registry) as ctx:
            result = await hello(ctx, name="")

            assert result == "Hello, !"


class TestStatusQuery:
    """Tests for the status query."""

    @pytest.mark.asyncio
    async def test_status_returns_ok(self) -> None:
        """Test status returns expected structure."""
        async with ExecutionContext(registry=app._registry) as ctx:
            result = await status(ctx)

            assert isinstance(result, dict)
            assert result["status"] == "ok"
            assert result["app"] == "trakr"

    @pytest.mark.asyncio
    async def test_status_keys(self) -> None:
        """Test status returns expected keys."""
        async with ExecutionContext(registry=app._registry) as ctx:
            result = await status(ctx)

            assert "status" in result
            assert "app" in result
            assert len(result) == 2
