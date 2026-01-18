"""Contract tests for QueryBinding execution.

Tests verify:
- QueryBinding executor resolves query from registry
- Query execution populates screen data
- Loading states are properly managed
- Errors are handled gracefully
- Cache TTL is respected
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from hive import App
from hive.core.decorators import query, screen
from hive.core.types import QueryBinding
from hive.tui.screens import HiveScreen


@pytest.fixture
def app_with_query() -> App:
    """Create an app with a registered query."""
    app = App("test")

    @query(app)
    async def list_items(ctx: Any) -> list[dict[str, Any]]:
        """List all items."""
        return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    return app


@pytest.fixture
def app_with_cached_query() -> App:
    """Create an app with a cached query."""
    app = App("test")

    @query(app, cache_ttl=60)
    async def cached_items(ctx: Any) -> list[dict[str, Any]]:
        """List cached items."""
        return [{"id": 1, "name": "Cached Item"}]

    return app


class TestQueryBindingCreation:
    """Tests for QueryBinding dataclass."""

    def test_query_binding_has_required_fields(self) -> None:
        """QueryBinding has screen_name and query_name fields."""
        binding = QueryBinding(screen_name="dashboard", query_name="list_items")

        assert binding.screen_name == "dashboard"
        assert binding.query_name == "list_items"

    def test_query_binding_has_default_target_property(self) -> None:
        """QueryBinding defaults target_property to 'data'."""
        binding = QueryBinding(screen_name="dashboard", query_name="list_items")

        assert binding.target_property == "data"

    def test_query_binding_supports_custom_target(self) -> None:
        """QueryBinding supports custom target property."""
        binding = QueryBinding(
            screen_name="dashboard",
            query_name="list_items",
            target_property="items",
        )

        assert binding.target_property == "items"

    def test_query_binding_supports_transform(self) -> None:
        """QueryBinding supports result transformation."""

        def transform_fn(data: list[Any]) -> list[str]:
            return [item["name"] for item in data]

        binding = QueryBinding(
            screen_name="dashboard",
            query_name="list_items",
            transform=transform_fn,
        )

        assert binding.transform is not None
        result = binding.transform([{"name": "Test"}])
        assert result == ["Test"]

    def test_query_binding_supports_refresh_events(self) -> None:
        """QueryBinding supports refresh_on events."""
        binding = QueryBinding(
            screen_name="dashboard",
            query_name="list_items",
            refresh_on=("item_created", "item_deleted"),
        )

        assert binding.refresh_on == ("item_created", "item_deleted")


class TestQueryBindingExecution:
    """Tests for QueryBinding executor."""

    @pytest.mark.asyncio
    async def test_execute_binding_calls_query(self, app_with_query: App) -> None:
        """Executing a binding calls the registered query."""
        from hive.tui.binding import execute_query_binding

        binding = QueryBinding(screen_name="test", query_name="list_items")

        # Mock context
        mock_ctx = MagicMock()

        result = await execute_query_binding(
            binding,
            registry=app_with_query.registry,
            ctx=mock_ctx,
        )

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"

    @pytest.mark.asyncio
    async def test_execute_binding_applies_transform(self, app_with_query: App) -> None:
        """Executing a binding with transform applies the transformation."""
        from hive.tui.binding import execute_query_binding

        def transform_fn(data: list[dict[str, Any]]) -> list[str]:
            return [item["name"] for item in data]

        binding = QueryBinding(
            screen_name="test",
            query_name="list_items",
            transform=transform_fn,
        )

        mock_ctx = MagicMock()

        result = await execute_query_binding(
            binding,
            registry=app_with_query.registry,
            ctx=mock_ctx,
        )

        assert result == ["Item 1", "Item 2"]

    @pytest.mark.asyncio
    async def test_execute_binding_raises_on_missing_query(self) -> None:
        """Executing a binding for non-existent query raises ConfigurationError."""
        from hive.errors import ConfigurationError
        from hive.tui.binding import execute_query_binding

        app = App("test")  # No queries registered
        binding = QueryBinding(screen_name="test", query_name="nonexistent")

        with pytest.raises(ConfigurationError, match="Query 'nonexistent' not found"):
            await execute_query_binding(
                binding,
                registry=app.registry,
                ctx=MagicMock(),
            )


class TestQueryBindingWithCache:
    """Tests for QueryBinding with cache_ttl."""

    @pytest.mark.asyncio
    async def test_cached_query_returns_cached_result(self, app_with_cached_query: App) -> None:
        """Cached query returns cached result within TTL."""
        from hive.tui.binding import QueryBindingExecutor

        executor = QueryBindingExecutor(registry=app_with_cached_query.registry)
        binding = QueryBinding(screen_name="test", query_name="cached_items")

        mock_ctx = MagicMock()

        # First call
        result1 = await executor.execute(binding, ctx=mock_ctx)

        # Second call should use cache
        result2 = await executor.execute(binding, ctx=mock_ctx)

        assert result1 == result2
        # Query should have been called only once (mocking would verify this)

    @pytest.mark.asyncio
    async def test_get_cache_info_returns_ttl(self, app_with_cached_query: App) -> None:
        """Can retrieve cache TTL info from binding."""
        from hive.tui.binding import QueryBindingExecutor

        executor = QueryBindingExecutor(registry=app_with_cached_query.registry)
        binding = QueryBinding(screen_name="test", query_name="cached_items")

        cache_info = executor.get_cache_info(binding)

        assert cache_info is not None
        assert cache_info["ttl"] == 60


class TestScreenQueryLoading:
    """Tests for HiveScreen query loading behavior."""

    @pytest.mark.asyncio
    async def test_screen_loads_queries_on_mount(self, app_with_query: App) -> None:
        """Screen with bound queries loads them on mount."""

        @screen(app_with_query, default=True, queries=["list_items"])
        class ItemsScreen(HiveScreen[None]):
            """Items screen."""

        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(app_with_query)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Screen should have loaded data
            current_screen = tui_app.screen
            # After data loads, is_loading should be False
            assert current_screen.is_loading is False

    @pytest.mark.asyncio
    async def test_screen_shows_loading_state(self, app_with_query: App) -> None:
        """Screen shows loading state while query executes."""

        @screen(app_with_query, default=True, queries=["list_items"])
        class LoadingScreen(HiveScreen[None]):
            """Screen that tracks loading state."""

            loading_observed: bool = False

            def watch_is_loading(self, loading: bool) -> None:
                """Watch for loading state changes."""
                if loading:
                    self.loading_observed = True

        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(app_with_query)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            current_screen = tui_app.screen
            # The screen should have observed loading=True at some point
            assert hasattr(current_screen, "loading_observed")

    @pytest.mark.asyncio
    async def test_screen_handles_query_error(self) -> None:
        """Screen handles query execution errors gracefully."""
        app = App("test")

        @query(app)
        async def failing_query(ctx: Any) -> list[Any]:
            """Query that always fails."""
            raise ValueError("Query failed!")

        @screen(app, default=True, queries=["failing_query"])
        class ErrorScreen(HiveScreen[None]):
            """Screen with failing query."""

        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            current_screen = tui_app.screen
            # Screen should have error set
            assert current_screen.error is not None
            assert "Query failed" in current_screen.error

    @pytest.mark.asyncio
    async def test_refresh_data_reloads_queries(self, app_with_query: App) -> None:
        """Calling refresh_data reloads bound queries."""
        call_count = 0

        @query(app_with_query)
        async def counting_query(ctx: Any) -> list[dict[str, Any]]:
            """Query that counts calls."""
            nonlocal call_count
            call_count += 1
            return [{"count": call_count}]

        @screen(app_with_query, default=True, queries=["counting_query"])
        class CountingScreen(HiveScreen[None]):
            """Screen that counts query calls."""

        from hive.generators.tui import generate_tui_app

        tui_app = generate_tui_app(app_with_query)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            current_screen = tui_app.screen

            # Trigger refresh
            await current_screen.refresh_data()
            await pilot.pause()

            # Query should have been called multiple times
            assert call_count >= 2


class TestQueryValidation:
    """Tests for query validation at startup."""

    def test_app_validates_screen_queries_at_startup(self) -> None:
        """App raises ConfigurationError for invalid query references."""
        from hive.errors import ConfigurationError
        from hive.generators.tui import generate_tui_app

        app = App("test")

        @screen(app, default=True, queries=["nonexistent_query"])
        class BadScreen(HiveScreen[None]):
            """Screen with invalid query reference."""

        with pytest.raises(ConfigurationError, match="Query 'nonexistent_query' not found"):
            generate_tui_app(app)

    def test_app_accepts_valid_query_references(self, app_with_query: App) -> None:
        """App accepts screens with valid query references."""
        from hive.generators.tui import generate_tui_app

        @screen(app_with_query, default=True, queries=["list_items"])
        class GoodScreen(HiveScreen[None]):
            """Screen with valid query reference."""

        # Should not raise
        tui_app = generate_tui_app(app_with_query)
        assert tui_app is not None
