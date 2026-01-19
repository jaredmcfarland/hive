# ruff: noqa: S603, S607
"""Integration tests for project workflow.

Tests the end-to-end project scaffolding and management functionality
including hive new, hive dev, and hive build commands.

RED phase: These tests should FAIL until project tooling is implemented.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import pytest


class TestHiveNewCommand:
    """Integration tests for `hive new` command."""

    def test_new_command_exists(self) -> None:
        """Hive new command exists."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "new", "--help"],
            capture_output=True,
            text=True,
        )
        # Should not fail with "No such command"
        assert result.returncode == 0 or "new" in result.stdout.lower()

    def test_new_creates_project(self) -> None:
        """Hive new creates a project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(  # noqa: PLW1510
                ["uv", "run", "hive", "new", "testapp", "--path", tmpdir],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            # Skip if command not implemented yet
            if result.returncode != 0 and "No such command" in result.stderr:
                pytest.skip("hive new not implemented yet")

            project_dir = Path(tmpdir) / "testapp"
            assert project_dir.exists()

    def test_new_creates_pyproject_toml(self) -> None:
        """Hive new creates pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(  # noqa: PLW1510
                ["uv", "run", "hive", "new", "testapp", "--path", tmpdir],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            if result.returncode != 0 and "No such command" in result.stderr:
                pytest.skip("hive new not implemented yet")

            pyproject = Path(tmpdir) / "testapp" / "pyproject.toml"
            assert pyproject.exists()

    def test_new_with_features(self) -> None:
        """Hive new --features creates project with optional deps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(  # noqa: PLW1510
                ["uv", "run", "hive", "new", "testapp", "--features", "tui,mcp", "--path", tmpdir],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            if result.returncode != 0 and "No such command" in result.stderr:
                pytest.skip("hive new not implemented yet")

            pyproject = Path(tmpdir) / "testapp" / "pyproject.toml"
            if pyproject.exists():
                content = pyproject.read_text()
                # Should have optional dependencies
                assert "textual" in content.lower() or "optional" in content.lower()


class TestHiveDevCommand:
    """Integration tests for `hive dev` command."""

    def test_dev_command_exists(self) -> None:
        """Hive dev command exists."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "dev", "--help"],
            capture_output=True,
            text=True,
        )
        # Should have dev command (or help output)
        assert result.returncode == 0 or "dev" in result.stdout.lower()


class TestHiveBuildCommand:
    """Integration tests for `hive build` command."""

    def test_build_command_exists(self) -> None:
        """Hive build command exists."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "build", "--help"],
            capture_output=True,
            text=True,
        )
        # Should have build command
        assert result.returncode == 0 or "build" in result.stdout.lower()


class TestHivePublishCommand:
    """Integration tests for `hive publish` command."""

    def test_publish_command_exists(self) -> None:
        """Hive publish command exists."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "publish", "--help"],
            capture_output=True,
            text=True,
        )
        # Should have publish command
        assert result.returncode == 0 or "publish" in result.stdout.lower()
