"""Contract tests for project tooling.

Tests the project scaffolding and management functionality including
hive new, hive build, and template variable substitution.

RED phase: These tests should FAIL until project tooling is implemented.
"""

from __future__ import annotations

from pathlib import Path
import tempfile


class TestHiveNewProjectCreation:
    """Contract tests for `hive new` project creation."""

    def test_project_module_exists(self) -> None:
        """hive.cli.project module exists."""
        from hive.cli import project

        assert project is not None

    def test_create_project_function_exists(self) -> None:
        """create_project function exists."""
        from hive.cli.project import create_project

        assert callable(create_project)

    def test_create_project_creates_directory(self) -> None:
        """create_project creates project directory."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
            )
            assert Path(project_path).exists()
            assert Path(project_path).is_dir()

    def test_create_project_creates_pyproject_toml(self) -> None:
        """create_project creates pyproject.toml."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
            )
            pyproject = Path(project_path) / "pyproject.toml"
            assert pyproject.exists()
            content = pyproject.read_text()
            assert "myapp" in content

    def test_create_project_creates_src_structure(self) -> None:
        """create_project creates src/ directory structure."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
            )
            src_dir = Path(project_path) / "src" / "myapp"
            assert src_dir.exists()
            assert (src_dir / "__init__.py").exists()
            assert (src_dir / "app.py").exists()

    def test_create_project_creates_tests_structure(self) -> None:
        """create_project creates tests/ directory structure."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
            )
            tests_dir = Path(project_path) / "tests"
            assert tests_dir.exists()
            assert (tests_dir / "__init__.py").exists()

    def test_create_project_with_features(self) -> None:
        """create_project can include optional features."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
                features=["tui", "mcp"],
            )
            pyproject = Path(project_path) / "pyproject.toml"
            content = pyproject.read_text()
            # Should include optional dependencies
            assert "textual" in content or "tui" in content

    def test_create_project_force_overwrites(self) -> None:
        """create_project with force=True overwrites existing."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project twice
            create_project(name="myapp", path=tmpdir)
            # Should not raise with force=True
            project_path = create_project(
                name="myapp",
                path=tmpdir,
                force=True,
            )
            assert Path(project_path).exists()


class TestTemplateVariableSubstitution:
    """Contract tests for template variable substitution."""

    def test_name_variable_substituted(self) -> None:
        """{{name}} variable is substituted in templates."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="testproject",
                path=tmpdir,
            )
            app_py = Path(project_path) / "src" / "testproject" / "app.py"
            content = app_py.read_text()
            assert "testproject" in content
            assert "{{name}}" not in content

    def test_author_variable_substituted(self) -> None:
        """{{author}} variable is substituted in templates."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
                author="Test Author",
            )
            pyproject = Path(project_path) / "pyproject.toml"
            content = pyproject.read_text()
            assert "Test Author" in content
            assert "{{author}}" not in content

    def test_description_variable_substituted(self) -> None:
        """{{description}} variable is substituted in templates."""
        from hive.cli.project import create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(
                name="myapp",
                path=tmpdir,
                description="My awesome app",
            )
            pyproject = Path(project_path) / "pyproject.toml"
            content = pyproject.read_text()
            assert "My awesome app" in content


class TestHiveBuildArtifactCreation:
    """Contract tests for `hive build` artifact creation."""

    def test_build_function_exists(self) -> None:
        """build_project function exists."""
        from hive.cli.project import build_project

        assert callable(build_project)

    def test_build_returns_artifacts(self) -> None:
        """build_project returns list of created artifacts."""
        from hive.cli.project import build_project, create_project

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = create_project(name="myapp", path=tmpdir)
            result = build_project(project_path)
            assert "artifacts" in result
            assert isinstance(result["artifacts"], list)
