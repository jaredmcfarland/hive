"""Contract tests for Specification model validation.

Tests the Specification container and component models defined in
src/hive/spec/models.py per the data-model.md specification.

RED phase: These tests should FAIL until models are implemented.
"""

from datetime import UTC, datetime

import pytest


class TestSpecificationMetadata:
    """Contract tests for SpecificationMetadata model."""

    def test_metadata_requires_name(self) -> None:
        """Metadata must have a name field."""
        from hive.spec.models import SpecificationMetadata

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            SpecificationMetadata(
                version="0.1.0",
                generated_at=datetime.now(tz=UTC),
                hive_version="0.1.0",
            )

    def test_metadata_requires_version(self) -> None:
        """Metadata must have a version field."""
        from hive.spec.models import SpecificationMetadata

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            SpecificationMetadata(
                name="myapp",
                generated_at=datetime.now(tz=UTC),
                hive_version="0.1.0",
            )

    def test_metadata_valid_creation(self) -> None:
        """Metadata can be created with all required fields."""
        from hive.spec.models import SpecificationMetadata

        metadata = SpecificationMetadata(
            name="myapp",
            version="0.1.0",
            generated_at=datetime.now(tz=UTC),
            hive_version="0.1.0",
        )
        assert metadata.name == "myapp"
        assert metadata.version == "0.1.0"

    def test_metadata_has_schema_dialect(self) -> None:
        """Metadata includes JSON Schema dialect."""
        from hive.spec.models import SpecificationMetadata

        metadata = SpecificationMetadata(
            name="myapp",
            version="0.1.0",
            generated_at=datetime.now(tz=UTC),
            hive_version="0.1.0",
        )
        assert metadata.schema_dialect == "https://json-schema.org/draft/2020-12/schema"


class TestParameterSchema:
    """Contract tests for ParameterSchema model."""

    def test_parameter_requires_name(self) -> None:
        """Parameter must have a name."""
        from hive.spec.models import ParameterSchema

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            ParameterSchema(type="string")

    def test_parameter_requires_type(self) -> None:
        """Parameter must have a type."""
        from hive.spec.models import ParameterSchema

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            ParameterSchema(name="title")

    def test_parameter_with_constraints(self) -> None:
        """Parameter can include JSON Schema constraints."""
        from hive.spec.models import ParameterSchema

        param = ParameterSchema(
            name="priority",
            type="integer",
            required=False,
            default=1,
            minimum=1,
            maximum=5,
        )
        assert param.minimum == 1
        assert param.maximum == 5
        assert param.default == 1

    def test_parameter_with_format(self) -> None:
        """Parameter can include format constraint."""
        from hive.spec.models import ParameterSchema

        param = ParameterSchema(
            name="email",
            type="string",
            format="email",
        )
        assert param.format == "email"


class TestCommandSchema:
    """Contract tests for CommandSchema model."""

    def test_command_requires_name(self) -> None:
        """Command must have a name."""
        from hive.spec.models import CommandSchema

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            CommandSchema(
                parameters=[],
                return_type={"type": "object"},
            )

    def test_command_valid_creation(self) -> None:
        """Command can be created with required fields."""
        from hive.spec.models import CommandSchema, ParameterSchema

        cmd = CommandSchema(
            name="create_task",
            description="Create a new task.",
            parameters=[
                ParameterSchema(name="title", type="string", required=True),
            ],
            return_type={"$ref": "#/$defs/Task"},
        )
        assert cmd.name == "create_task"
        assert len(cmd.parameters) == 1

    def test_command_has_entities_list(self) -> None:
        """Command tracks associated entities."""
        from hive.spec.models import CommandSchema

        cmd = CommandSchema(
            name="create_task",
            parameters=[],
            return_type={"type": "object"},
            entities=["Task"],
        )
        assert "Task" in cmd.entities


class TestQuerySchema:
    """Contract tests for QuerySchema model."""

    def test_query_valid_creation(self) -> None:
        """Query can be created with cache_ttl."""
        from hive.spec.models import QuerySchema

        query = QuerySchema(
            name="list_tasks",
            parameters=[],
            return_type={"type": "array"},
            cache_ttl=60,
        )
        assert query.name == "list_tasks"
        assert query.cache_ttl == 60


class TestEntitySchema:
    """Contract tests for EntitySchema model."""

    def test_entity_requires_name(self) -> None:
        """Entity must have a name."""
        from hive.spec.models import EntitySchema

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            EntitySchema(table_name="tasks", fields=[])

    def test_entity_requires_table_name(self) -> None:
        """Entity must have a table_name."""
        from hive.spec.models import EntitySchema

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            EntitySchema(name="Task", fields=[])

    def test_entity_with_fields(self) -> None:
        """Entity can include field definitions."""
        from hive.spec.models import EntitySchema, FieldSchema

        entity = EntitySchema(
            name="Task",
            table_name="tasks",
            fields=[
                FieldSchema(name="id", type="integer", primary_key=True),
                FieldSchema(name="title", type="string"),
            ],
        )
        assert len(entity.fields) == 2
        assert entity.fields[0].primary_key is True


class TestSpecification:
    """Contract tests for Specification container model."""

    def test_specification_requires_metadata(self) -> None:
        """Specification must have metadata."""
        from hive.spec.models import Specification

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            Specification(commands={}, queries={}, entities={})

    def test_specification_valid_creation(self) -> None:
        """Specification can be created with all components."""
        from hive.spec.models import Specification, SpecificationMetadata

        spec = Specification(
            metadata=SpecificationMetadata(
                name="myapp",
                version="0.1.0",
                generated_at=datetime.now(tz=UTC),
                hive_version="0.1.0",
            ),
            commands={},
            queries={},
            entities={},
        )
        assert spec.metadata.name == "myapp"

    def test_specification_is_immutable(self) -> None:
        """Specification should be frozen after creation."""
        from hive.spec.models import Specification, SpecificationMetadata

        spec = Specification(
            metadata=SpecificationMetadata(
                name="myapp",
                version="0.1.0",
                generated_at=datetime.now(tz=UTC),
                hive_version="0.1.0",
            ),
            commands={},
            queries={},
            entities={},
        )
        # Frozen models should raise on attribute assignment
        with pytest.raises(Exception):  # noqa: B017 - ValidationError or AttributeError
            spec.commands = {"new": {}}  # type: ignore[misc]


class TestDiffModels:
    """Contract tests for DiffItem and SpecificationDiff models."""

    def test_diff_item_requires_path(self) -> None:
        """DiffItem must have a path."""
        from hive.spec.models import DiffItem

        with pytest.raises(Exception):  # noqa: B017 - ValidationError
            DiffItem(change_type="added")

    def test_diff_item_valid_types(self) -> None:
        """DiffItem change_type must be valid."""
        from hive.spec.models import DiffItem

        item = DiffItem(
            path="commands.create_task",
            change_type="added",
            new_value={"name": "create_task"},
        )
        assert item.change_type == "added"
        assert item.breaking is False  # default

    def test_specification_diff_creation(self) -> None:
        """SpecificationDiff can be created with changes."""
        from hive.spec.models import DiffItem, SpecificationDiff

        diff = SpecificationDiff(
            v1_version="0.1.0",
            v2_version="0.2.0",
            compared_at=datetime.now(tz=UTC),
            changes=[
                DiffItem(path="commands.new_cmd", change_type="added"),
            ],
            breaking_changes=[],
        )
        assert diff.v1_version == "0.1.0"
        assert len(diff.changes) == 1

    def test_specification_diff_has_breaking_changes_property(self) -> None:
        """SpecificationDiff has has_breaking_changes property."""
        from hive.spec.models import DiffItem, SpecificationDiff

        diff = SpecificationDiff(
            v1_version="0.1.0",
            v2_version="0.2.0",
            compared_at=datetime.now(tz=UTC),
            changes=[],
            breaking_changes=[
                DiffItem(path="commands.old_cmd", change_type="removed", breaking=True),
            ],
        )
        assert diff.has_breaking_changes is True
