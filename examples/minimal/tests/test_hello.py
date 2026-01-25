"""Tests for the hello command.

Demonstrates using TestClient for simple command testing.
"""

import pytest
from hive.testing import TestClient

from minimal import app


class TestHelloCommand:
    """Tests for the hello command."""

    @pytest.mark.asyncio
    async def test_hello_default_name(self) -> None:
        """Hello command uses default name when not provided."""
        async with TestClient(app) as client:
            result = await client.invoke("hello")
            assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_hello_custom_name(self) -> None:
        """Hello command uses provided name."""
        async with TestClient(app) as client:
            result = await client.invoke("hello", name="Alice")
            assert result == "Hello, Alice!"

    @pytest.mark.asyncio
    async def test_hello_empty_name(self) -> None:
        """Hello command works with empty string name."""
        async with TestClient(app) as client:
            result = await client.invoke("hello", name="")
            assert result == "Hello, !"

    @pytest.mark.asyncio
    async def test_multiple_invocations(self) -> None:
        """Multiple invocations work in the same session."""
        async with TestClient(app) as client:
            r1 = await client.invoke("hello", name="Alice")
            r2 = await client.invoke("hello", name="Bob")
            r3 = await client.invoke("hello")

            assert r1 == "Hello, Alice!"
            assert r2 == "Hello, Bob!"
            assert r3 == "Hello, World!"
            assert client.invocation_count == 3
