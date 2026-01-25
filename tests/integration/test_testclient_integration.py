"""Integration tests for TestClient.

Tests that TestClient works with real Hive applications and
integrates properly with the framework.
"""

import pytest


@pytest.mark.integration
class TestTestClientIntegration:
    """Integration tests for TestClient with real app scenarios."""

    @pytest.mark.asyncio
    async def test_full_crud_workflow(self) -> None:
        """TestClient supports full CRUD workflow."""
        from hive.app import App
        from hive.core.decorators import command, query
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("crud-app")
        items: dict[str, dict] = {}

        @command(app)
        async def create_item(ctx: ExecutionContext, name: str, value: int) -> dict:
            """Create an item."""
            item = {"id": len(items) + 1, "name": name, "value": value}
            items[name] = item
            return item

        @query(app)
        async def get_item(ctx: ExecutionContext, name: str) -> dict | None:
            """Get an item by name."""
            return items.get(name)

        @query(app)
        async def list_items(ctx: ExecutionContext) -> list[dict]:
            """List all items."""
            return list(items.values())

        @command(app)
        async def delete_item(ctx: ExecutionContext, name: str) -> bool:
            """Delete an item."""
            if name in items:
                del items[name]
                return True
            return False

        async with TestClient(app) as client:
            # Create items
            item1 = await client.invoke("create_item", name="apple", value=10)
            assert item1["id"] == 1
            assert item1["name"] == "apple"

            item2 = await client.invoke("create_item", name="banana", value=20)
            assert item2["id"] == 2

            # Query items
            apple = await client.query("get_item", name="apple")
            assert apple is not None
            assert apple["value"] == 10

            all_items = await client.query("list_items")
            assert len(all_items) == 2

            # Delete item
            deleted = await client.invoke("delete_item", name="apple")
            assert deleted is True

            remaining = await client.query("list_items")
            assert len(remaining) == 1

    @pytest.mark.asyncio
    async def test_command_with_refinement_types(self) -> None:
        """TestClient works with refinement type parameters."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient
        from hive.types import PositiveInt

        app = App("types-app")

        @command(app)
        async def set_priority(ctx: ExecutionContext, priority: PositiveInt) -> int:
            """Set priority (must be positive)."""
            return priority

        async with TestClient(app) as client:
            # Valid positive integer
            result = await client.invoke("set_priority", priority=5)
            assert result == 5

    @pytest.mark.asyncio
    async def test_multiple_queries_same_session(self) -> None:
        """Multiple queries in same session share context."""
        from hive.app import App
        from hive.core.decorators import query
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("multi-query-app")
        call_count = 0

        @query(app)
        async def increment_counter(ctx: ExecutionContext) -> int:
            """Increment and return counter."""
            nonlocal call_count
            call_count += 1
            return call_count

        async with TestClient(app) as client:
            r1 = await client.query("increment_counter")
            r2 = await client.query("increment_counter")
            r3 = await client.query("increment_counter")

            assert r1 == 1
            assert r2 == 2
            assert r3 == 3
            assert client.invocation_count == 3

    @pytest.mark.asyncio
    async def test_command_aliases(self) -> None:
        """TestClient supports command aliases."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("alias-app")

        @command(app, aliases=["hi", "hey"])
        async def hello(ctx: ExecutionContext, name: str = "World") -> str:
            """Say hello."""
            return f"Hello, {name}!"

        async with TestClient(app) as client:
            # All should work
            r1 = await client.invoke("hello", name="Alice")
            r2 = await client.invoke("hi", name="Bob")
            r3 = await client.invoke("hey", name="Charlie")

            assert r1 == "Hello, Alice!"
            assert r2 == "Hello, Bob!"
            assert r3 == "Hello, Charlie!"

    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        """TestClient propagates errors from commands."""
        from hive.app import App
        from hive.core.decorators import command
        from hive.runtime.context import ExecutionContext
        from hive.testing import TestClient

        app = App("error-app")

        @command(app)
        async def fail_always(ctx: ExecutionContext) -> None:
            """Always fails."""
            msg = "Intentional failure"
            raise ValueError(msg)

        async with TestClient(app) as client:
            with pytest.raises(ValueError, match="Intentional failure"):
                await client.invoke("fail_always")
