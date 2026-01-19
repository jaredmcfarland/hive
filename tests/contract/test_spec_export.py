"""Contract tests for specification export functionality.

Tests build_specification() registry→Specification conversion and
JSON Schema output validation against Draft 2020-12.

RED phase: These tests should FAIL until export functionality is implemented.
"""


class TestBuildSpecification:
    """Contract tests for build_specification() function."""

    def test_build_specification_exists(self) -> None:
        """build_specification function exists and is importable."""
        from hive.spec.export import build_specification

        assert callable(build_specification)

    def test_build_specification_from_empty_registry(self) -> None:
        """build_specification returns Specification from empty registry."""
        from hive import App
        from hive.spec.export import build_specification
        from hive.spec.models import Specification

        app = App("empty_app")
        spec = build_specification(app)

        assert isinstance(spec, Specification)
        assert spec.metadata.name == "empty_app"
        assert len(spec.commands) == 0
        assert len(spec.queries) == 0

    def test_build_specification_includes_commands(self) -> None:
        """build_specification includes registered commands."""
        from hive import App, command
        from hive.spec.export import build_specification

        app = App("cmd_app")

        @command(app)
        async def create_task(ctx, title: str) -> dict:
            """Create a task."""
            return {"title": title}

        spec = build_specification(app)

        assert "create_task" in spec.commands
        cmd_schema = spec.commands["create_task"]
        assert cmd_schema.name == "create_task"
        assert cmd_schema.description == "Create a task."

    def test_build_specification_includes_parameters(self) -> None:
        """build_specification extracts command parameters."""
        from hive import App, command
        from hive.spec.export import build_specification

        app = App("param_app")

        @command(app)
        async def create_task(ctx, title: str, priority: int = 1) -> dict:
            """Create a task with priority."""
            return {"title": title, "priority": priority}

        spec = build_specification(app)
        cmd_schema = spec.commands["create_task"]

        # Should have 2 parameters (excluding ctx)
        assert len(cmd_schema.parameters) == 2

        # Find title parameter
        title_param = next(p for p in cmd_schema.parameters if p.name == "title")
        assert title_param.type == "string"
        assert title_param.required is True

        # Find priority parameter
        priority_param = next(p for p in cmd_schema.parameters if p.name == "priority")
        assert priority_param.type == "integer"
        assert priority_param.required is False
        assert priority_param.default == 1

    def test_build_specification_includes_refinement_constraints(self) -> None:
        """build_specification extracts refinement type constraints."""
        from hive import App, command
        from hive.spec.export import build_specification
        from hive.types import NonEmptyStr, PositiveInt

        app = App("constraint_app")

        @command(app)
        async def create_task(ctx, title: NonEmptyStr, priority: PositiveInt = 1) -> dict:
            """Create a task with constraints."""
            return {"title": title, "priority": priority}

        spec = build_specification(app)
        cmd_schema = spec.commands["create_task"]

        # Find title parameter - should have minLength constraint
        title_param = next(p for p in cmd_schema.parameters if p.name == "title")
        assert title_param.min_length == 1

        # Find priority parameter - should have minimum constraint
        priority_param = next(p for p in cmd_schema.parameters if p.name == "priority")
        assert priority_param.minimum == 1

    def test_build_specification_includes_queries(self) -> None:
        """build_specification includes registered queries."""
        from hive import App, query
        from hive.spec.export import build_specification

        app = App("query_app")

        @query(app)
        async def list_tasks(ctx, completed: bool = False) -> list:
            """List tasks."""
            return []

        spec = build_specification(app)

        assert "list_tasks" in spec.queries
        query_schema = spec.queries["list_tasks"]
        assert query_schema.name == "list_tasks"

    def test_build_specification_includes_entities(self) -> None:
        """build_specification includes registered entities."""
        from sqlmodel import Field, SQLModel

        from hive import App, entity
        from hive.spec.export import build_specification

        app = App("entity_app")

        @entity(app)
        class Task(SQLModel, table=True):
            """A task entity."""

            __tablename__ = "tasks"  # type: ignore[misc]

            id: int | None = Field(default=None, primary_key=True)
            title: str

        spec = build_specification(app)

        assert "Task" in spec.entities
        entity_schema = spec.entities["Task"]
        assert entity_schema.name == "Task"
        assert entity_schema.table_name == "tasks"


class TestJsonSchemaExport:
    """Contract tests for JSON Schema export validation."""

    def test_export_specification_json_format(self) -> None:
        """export_specification returns valid JSON string."""
        import json

        from hive import App
        from hive.spec.export import export_specification

        app = App("json_app")
        json_str = export_specification(app, format="json")

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_export_json_includes_schema_dialect(self) -> None:
        """Exported JSON includes $schema Draft 2020-12 URI."""
        import json

        from hive import App
        from hive.spec.export import export_specification

        app = App("schema_app")
        json_str = export_specification(app, format="json")
        parsed = json.loads(json_str)

        assert "$schema" in parsed
        assert parsed["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_export_json_includes_metadata(self) -> None:
        """Exported JSON includes metadata section."""
        import json

        from hive import App
        from hive.spec.export import export_specification

        app = App("metadata_app")
        json_str = export_specification(app, format="json")
        parsed = json.loads(json_str)

        assert "metadata" in parsed
        assert parsed["metadata"]["name"] == "metadata_app"
        assert "version" in parsed["metadata"]
        assert "generated_at" in parsed["metadata"]

    def test_export_json_commands_section(self) -> None:
        """Exported JSON includes commands section with parameters."""
        import json

        from hive import App, command
        from hive.spec.export import export_specification

        app = App("export_app")

        @command(app)
        async def test_cmd(ctx, name: str, count: int = 1) -> dict:
            """Test command."""
            return {}

        json_str = export_specification(app, format="json")
        parsed = json.loads(json_str)

        assert "commands" in parsed
        assert "test_cmd" in parsed["commands"]
        cmd = parsed["commands"]["test_cmd"]
        assert "parameters" in cmd

    def test_export_json_to_file(self) -> None:
        """export_specification can write to file."""
        import json
        from pathlib import Path
        import tempfile

        from hive import App
        from hive.spec.export import export_specification

        app = App("file_app")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            export_specification(app, format="json", output=str(output_path))
            assert output_path.exists()

            with output_path.open() as f:
                parsed = json.load(f)
            assert parsed["metadata"]["name"] == "file_app"
        finally:
            output_path.unlink(missing_ok=True)


class TestTomlExport:
    """Contract tests for TOML specification export."""

    def test_export_specification_toml_format(self) -> None:
        """export_specification returns valid TOML string."""
        import tomllib

        from hive import App
        from hive.spec.export import export_specification

        app = App("toml_app")
        toml_str = export_specification(app, format="toml")

        # Should be valid TOML
        parsed = tomllib.loads(toml_str)
        assert isinstance(parsed, dict)

    def test_export_toml_includes_metadata(self) -> None:
        """Exported TOML includes metadata section."""
        import tomllib

        from hive import App
        from hive.spec.export import export_specification

        app = App("toml_metadata_app")
        toml_str = export_specification(app, format="toml")
        parsed = tomllib.loads(toml_str)

        assert "metadata" in parsed
        assert parsed["metadata"]["name"] == "toml_metadata_app"
        assert "version" in parsed["metadata"]
        assert "generated_at" in parsed["metadata"]

    def test_export_toml_includes_commands(self) -> None:
        """Exported TOML includes commands section."""
        import tomllib

        from hive import App, command
        from hive.spec.export import export_specification

        app = App("toml_cmd_app")

        @command(app)
        async def test_cmd(ctx, name: str, count: int = 1) -> dict:
            """Test command."""
            return {}

        toml_str = export_specification(app, format="toml")
        parsed = tomllib.loads(toml_str)

        assert "commands" in parsed
        assert "test_cmd" in parsed["commands"]

    def test_toml_json_equivalence(self) -> None:
        """TOML and JSON exports contain equivalent data."""
        import json
        import tomllib

        from hive import App, command, query
        from hive.spec.export import export_specification

        app = App("equiv_app")

        @command(app)
        async def create_task(ctx, title: str, priority: int = 1) -> dict:
            """Create a task."""
            return {"title": title}

        @query(app)
        async def list_tasks(ctx, completed: bool = False) -> list:
            """List tasks."""
            return []

        json_str = export_specification(app, format="json")
        toml_str = export_specification(app, format="toml")

        json_data = json.loads(json_str)
        toml_data = tomllib.loads(toml_str)

        # Metadata should match (name and version at least)
        assert json_data["metadata"]["name"] == toml_data["metadata"]["name"]
        assert json_data["metadata"]["version"] == toml_data["metadata"]["version"]

        # Commands should match
        assert set(json_data["commands"].keys()) == set(toml_data["commands"].keys())
        assert (
            json_data["commands"]["create_task"]["name"]
            == toml_data["commands"]["create_task"]["name"]
        )

        # Queries should match
        assert set(json_data["queries"].keys()) == set(toml_data["queries"].keys())

    def test_export_toml_to_file(self) -> None:
        """export_specification can write TOML to file."""
        from pathlib import Path
        import tempfile
        import tomllib

        from hive import App
        from hive.spec.export import export_specification

        app = App("toml_file_app")

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            output_path = Path(f.name)

        try:
            export_specification(app, format="toml", output=str(output_path))
            assert output_path.exists()

            with output_path.open("rb") as f:
                parsed = tomllib.load(f)
            assert parsed["metadata"]["name"] == "toml_file_app"
        finally:
            output_path.unlink(missing_ok=True)
