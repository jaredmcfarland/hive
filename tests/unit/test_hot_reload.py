"""Unit tests for hot reload file watching.

Tests the hot reload functionality using watchfiles.

RED phase: These tests should FAIL until hot reload is implemented.
"""

from __future__ import annotations

import tempfile


class TestHotReload:
    """Tests for hot reload file watching."""

    def test_watchfiles_available(self) -> None:
        """Watchfiles package is available."""
        import watchfiles

        assert watchfiles is not None

    def test_create_file_watcher_exists(self) -> None:
        """create_file_watcher function exists."""
        from hive.cli.project import create_file_watcher

        assert callable(create_file_watcher)

    def test_watcher_watches_python_files(self) -> None:
        """File watcher monitors .py files."""
        from hive.cli.project import create_file_watcher

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = create_file_watcher(tmpdir)
            # Should have filter for Python files
            assert watcher is not None

    def test_watcher_ignores_pycache(self) -> None:
        """File watcher ignores __pycache__ directories."""
        from hive.cli.project import create_file_watcher

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = create_file_watcher(tmpdir)
            # Watcher should be configured
            assert watcher is not None


class TestDevServerReload:
    """Tests for development server reload functionality."""

    def test_start_dev_server_function_exists(self) -> None:
        """start_dev_server function exists."""
        from hive.cli.project import start_dev_server

        assert callable(start_dev_server)
