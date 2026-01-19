# ruff: noqa: S603, S607
"""Integration tests for specification export CLI workflow.

Tests the complete `hive spec export` and `hive spec diff` CLI commands.

RED phase: These tests should FAIL until CLI commands are implemented.
"""

from collections.abc import Generator
import json
from pathlib import Path
import subprocess
import tempfile

import pytest


class TestHiveSpecExportCLI:
    """Integration tests for `hive spec export` command."""

    def test_spec_export_help(self) -> None:
        """Hive spec export --help shows usage."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "export", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should complete without error
        assert result.returncode == 0
        assert "export" in result.stdout.lower()

    def test_spec_export_json_to_stdout(self) -> None:
        """Hive spec export --format json outputs to stdout."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "export", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

        # Output should be valid JSON
        output = json.loads(result.stdout)
        assert "$schema" in output
        assert "metadata" in output

    def test_spec_export_json_to_file(self) -> None:
        """Hive spec export --format json -o file.json writes to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = subprocess.run(  # noqa: PLW1510
                ["uv", "run", "hive", "spec", "export", "--format", "json", "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0
            assert output_path.exists()

            with output_path.open() as f:
                data = json.load(f)
            assert "$schema" in data
        finally:
            output_path.unlink(missing_ok=True)

    def test_spec_export_json_flag(self) -> None:
        """Hive spec export --json outputs machine-readable JSON."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "export", "--format", "json", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

        # Should be valid JSON (for --json flag output format)
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_spec_export_toml_to_stdout(self) -> None:
        """Hive spec export --format toml outputs to stdout."""
        import tomllib

        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "export", "--format", "toml"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

        # Output should be valid TOML
        output = tomllib.loads(result.stdout)
        assert "metadata" in output

    def test_spec_export_toml_to_file(self) -> None:
        """Hive spec export --format toml -o file.toml writes to file."""
        import tomllib

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = subprocess.run(  # noqa: PLW1510
                ["uv", "run", "hive", "spec", "export", "--format", "toml", "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0
            assert output_path.exists()

            with output_path.open("rb") as f:
                data = tomllib.load(f)
            assert "metadata" in data
        finally:
            output_path.unlink(missing_ok=True)


class TestHiveSpecDiffCLI:
    """Integration tests for `hive spec diff` command."""

    @pytest.fixture
    def spec_files(self) -> Generator[tuple[Path, Path], None, None]:
        """Create two spec files for diff testing."""
        spec1 = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "metadata": {"name": "app", "version": "1.0.0"},
            "commands": {
                "old_cmd": {"name": "old_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }
        spec2 = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "metadata": {"name": "app", "version": "2.0.0"},
            "commands": {
                "new_cmd": {"name": "new_cmd", "parameters": [], "return_type": {}},
            },
            "queries": {},
            "entities": {},
        }

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f1:
            json.dump(spec1, f1)
            path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f2:
            json.dump(spec2, f2)
            path2 = Path(f2.name)

        yield path1, path2

        path1.unlink(missing_ok=True)
        path2.unlink(missing_ok=True)

    def test_spec_diff_help(self) -> None:
        """Hive spec diff --help shows usage."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "diff", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "diff" in result.stdout.lower()

    def test_spec_diff_basic(self, spec_files: tuple[Path, Path]) -> None:
        """Hive spec diff v1.json v2.json shows differences."""
        path1, path2 = spec_files

        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "diff", str(path1), str(path2)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        # Should show some diff output
        assert len(result.stdout) > 0

    def test_spec_diff_json_format(self, spec_files: tuple[Path, Path]) -> None:
        """Hive spec diff --format json outputs JSON."""
        path1, path2 = spec_files

        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "diff", str(path1), str(path2), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

        # Output should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_spec_diff_fail_on_breaking(self, spec_files: tuple[Path, Path]) -> None:
        """Hive spec diff --fail-on-breaking returns non-zero on breaking changes."""
        path1, path2 = spec_files

        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "spec", "diff", str(path1), str(path2), "--fail-on-breaking"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should return non-zero exit code when there are breaking changes
        # (old_cmd was removed, which is breaking)
        assert result.returncode != 0
