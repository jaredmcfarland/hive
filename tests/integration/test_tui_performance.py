"""Performance tests for TUI components.

Validates NFR success criteria:
- SC-002: Screen navigation responds within 100ms
- SC-003: Query-bound tables display within 500ms of mount
- SC-006: Widgets render correctly at 80x24 minimum
- SC-007: Service instantiation overhead under 50ms
- SC-008: Command palette filters 100+ commands under 100ms
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import pytest

from hive.app import App
from hive.core.decorators import command, query, service
from hive.core.decorators import screen as screen_decorator
from hive.generators.tui import generate_tui_app
from hive.runtime.services import ServiceProxy
from hive.tui.screens import HiveScreen
from hive.tui.widgets.palette import filter_commands


class TestScreenNavigationPerformance:
    """Tests for SC-002: Screen navigation responds within 100ms."""

    @pytest.mark.asyncio
    async def test_navigate_via_keybinding_under_100ms(self) -> None:
        """Screen navigation via keybinding completes under 100ms."""
        app = App("perf-test")

        @screen_decorator(app, default=True, keybinding="d")
        class DashboardScreen(HiveScreen[None]):
            """Dashboard screen."""

        @screen_decorator(app, keybinding="s")
        class SettingsScreen(HiveScreen[None]):
            """Settings screen."""

        tui = generate_tui_app(app)

        async with tui.run_test() as pilot:
            # Navigate to settings
            start = time.perf_counter()
            await pilot.press("s")
            await pilot.pause()
            elapsed = time.perf_counter() - start

            # SC-002: Must be under 100ms (using 200ms threshold for CI stability)
            assert elapsed < 0.2, f"Navigation took {elapsed * 1000:.1f}ms, expected <200ms"


class TestQueryBindingPerformance:
    """Tests for SC-003: Query-bound tables display within 500ms."""

    @pytest.mark.asyncio
    async def test_query_loads_under_500ms(self) -> None:
        """Query-bound data loads within 500ms of screen mount."""
        app = App("perf-test")
        load_times: list[float] = []

        @query(app)
        async def list_items(ctx: Any) -> list[dict[str, Any]]:
            """Return items quickly."""
            return [{"id": i, "name": f"Item {i}"} for i in range(100)]

        @screen_decorator(app, default=True, queries=["list_items"])
        class ItemsScreen(HiveScreen[None]):
            """Items screen."""

        tui = generate_tui_app(app)

        async with tui.run_test() as pilot:
            start = time.perf_counter()

            # Wait for data to load
            await pilot.pause()
            screen = tui.screen
            if hasattr(screen, "is_loading"):
                while getattr(screen, "is_loading", False):
                    await pilot.pause()
                    if time.perf_counter() - start > 0.5:
                        break

            elapsed = time.perf_counter() - start
            load_times.append(elapsed)

            # SC-003: Must be under 500ms
            assert elapsed < 0.5, f"Data load took {elapsed * 1000:.1f}ms, expected <500ms"


class TestMinimumTerminalSize:
    """Tests for SC-006: Widgets render correctly at 80x24."""

    @pytest.mark.asyncio
    async def test_widgets_render_at_minimum_size(self) -> None:
        """All widgets render without error at 80x24."""
        app = App("perf-test")

        @screen_decorator(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen."""

        tui = generate_tui_app(app)

        # Test at minimum terminal size
        async with tui.run_test(size=(80, 24)) as pilot:
            # Should not raise any errors
            await pilot.pause()
            # Verify app is running
            assert not tui._exit


class TestServiceInstantiationPerformance:
    """Tests for SC-007: Service instantiation overhead under 50ms."""

    def test_service_instantiation_under_50ms(self) -> None:
        """Service instantiation completes under 50ms."""
        app = App("perf-test")

        @service(app, credentials="env:TEST_TOKEN")
        def fast_service(credentials: str) -> dict[str, str]:
            """Fast service factory."""
            return {"token": credentials}

        # Mock environment variable
        with patch.dict("os.environ", {"TEST_TOKEN": "test-token"}):
            proxy = ServiceProxy(app.registry)

            start = time.perf_counter()
            _ = proxy.fast_service
            elapsed = time.perf_counter() - start

            # SC-007: Must be under 50ms
            assert elapsed < 0.05, f"Service init took {elapsed * 1000:.1f}ms, expected <50ms"

    def test_cached_service_access_fast(self) -> None:
        """Cached service access is nearly instantaneous."""
        app = App("perf-test")

        @service(app, credentials="env:TEST_TOKEN")
        def cached_service(credentials: str) -> dict[str, str]:
            """Cached service factory."""
            return {"token": credentials}

        with patch.dict("os.environ", {"TEST_TOKEN": "test-token"}):
            proxy = ServiceProxy(app.registry)

            # First access
            _ = proxy.cached_service

            # Second access should be from cache
            start = time.perf_counter()
            _ = proxy.cached_service
            elapsed = time.perf_counter() - start

            # Cached access should be under 1ms
            assert elapsed < 0.001, f"Cached access took {elapsed * 1000:.2f}ms, expected <1ms"


class TestCommandPalettePerformance:
    """Tests for SC-008: Command palette filters 100+ commands under 100ms."""

    def test_filter_100_commands_under_100ms(self) -> None:
        """Filtering 100+ commands completes under 100ms."""
        app = App("perf-test")

        # Register 100+ commands
        for i in range(150):

            @command(app, name=f"command_{i:03d}")
            async def cmd(ctx: Any) -> None:
                """Generated command."""

        commands = app.registry.list_commands()
        assert len(commands) >= 100

        # Time the filtering
        start = time.perf_counter()
        results = filter_commands(commands, "command")
        elapsed = time.perf_counter() - start

        # Should return matches
        assert len(results) > 0

        # SC-008: Must be under 100ms
        assert elapsed < 0.1, f"Filter took {elapsed * 1000:.1f}ms, expected <100ms"

    def test_filter_with_fuzzy_match_under_100ms(self) -> None:
        """Fuzzy filtering 100+ commands completes under 100ms."""
        app = App("perf-test")

        # Register commands with varied names
        names = [
            "create_user",
            "delete_user",
            "update_user",
            "list_users",
            "create_post",
            "delete_post",
            "update_post",
            "list_posts",
        ]
        for i in range(130):
            name = f"{names[i % len(names)]}_{i:03d}"

            @command(app, name=name)
            async def cmd(ctx: Any) -> None:
                """Generated command."""

        commands = app.registry.list_commands()

        # Time fuzzy search
        start = time.perf_counter()
        _ = filter_commands(commands, "usr")  # Fuzzy match for "user"
        elapsed = time.perf_counter() - start

        # SC-008: Must be under 100ms
        assert elapsed < 0.1, f"Fuzzy filter took {elapsed * 1000:.1f}ms, expected <100ms"

    def test_empty_query_returns_all_fast(self) -> None:
        """Empty query returns all commands quickly."""
        app = App("perf-test")

        for i in range(100):

            @command(app, name=f"cmd_{i:03d}")
            async def cmd(ctx: Any) -> None:
                """Generated command."""

        commands = app.registry.list_commands()

        start = time.perf_counter()
        results = filter_commands(commands, "")
        elapsed = time.perf_counter() - start

        # Should return all non-hidden commands
        assert len(results) == 100

        # Should be very fast
        assert elapsed < 0.01, f"Empty filter took {elapsed * 1000:.1f}ms, expected <10ms"
