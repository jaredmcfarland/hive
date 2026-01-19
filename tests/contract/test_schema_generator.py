"""Contract tests for HiveSchemaGenerator.

Tests the JSON Schema generation from Pydantic models and registry types
as defined in src/hive/generators/schema.py.

RED phase: These tests should FAIL until schema generator is implemented.
"""

from typing import Annotated

from pydantic import BaseModel, Field


class TestHiveSchemaGenerator:
    """Contract tests for HiveSchemaGenerator class."""

    def test_generator_exists(self) -> None:
        """HiveSchemaGenerator class exists and can be instantiated."""
        from hive.generators.schema import HiveSchemaGenerator

        generator = HiveSchemaGenerator()
        assert generator is not None

    def test_generator_produces_draft_2020_12(self) -> None:
        """Generated schema includes Draft 2020-12 dialect."""
        from hive.generators.schema import HiveSchemaGenerator

        class SimpleModel(BaseModel):
            name: str

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(SimpleModel)
        assert "$schema" in schema
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_generator_handles_basic_types(self) -> None:
        """Generator correctly maps basic Python types to JSON Schema."""
        from hive.generators.schema import HiveSchemaGenerator

        class BasicModel(BaseModel):
            name: str
            count: int
            ratio: float
            active: bool

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(BasicModel)

        props = schema.get("properties", {})
        assert props["name"]["type"] == "string"
        assert props["count"]["type"] == "integer"
        assert props["ratio"]["type"] == "number"
        assert props["active"]["type"] == "boolean"

    def test_generator_handles_optional_fields(self) -> None:
        """Generator correctly marks optional fields."""
        from hive.generators.schema import HiveSchemaGenerator

        class OptionalModel(BaseModel):
            required_field: str
            optional_field: str | None = None

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(OptionalModel)

        required = schema.get("required", [])
        assert "required_field" in required
        # Optional fields may or may not be in required depending on None default

    def test_generator_handles_default_values(self) -> None:
        """Generator includes default values in schema."""
        from hive.generators.schema import HiveSchemaGenerator

        class DefaultModel(BaseModel):
            priority: int = 1
            name: str = "default"

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(DefaultModel)

        props = schema.get("properties", {})
        assert props["priority"].get("default") == 1
        assert props["name"].get("default") == "default"

    def test_generator_preserves_descriptions(self) -> None:
        """Generator includes Field descriptions."""
        from hive.generators.schema import HiveSchemaGenerator

        class DescribedModel(BaseModel):
            task_id: int = Field(description="Unique task identifier")

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(DescribedModel)

        props = schema.get("properties", {})
        assert props["task_id"].get("description") == "Unique task identifier"

    def test_generator_handles_nested_models(self) -> None:
        """Generator creates $defs for nested models."""
        from hive.generators.schema import HiveSchemaGenerator

        class Inner(BaseModel):
            value: str

        class Outer(BaseModel):
            inner: Inner

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(Outer)

        # Nested models should be in $defs
        assert "$defs" in schema or "definitions" in schema
        defs = schema.get("$defs", schema.get("definitions", {}))
        assert "Inner" in defs

    def test_generator_handles_list_types(self) -> None:
        """Generator correctly maps list types."""
        from hive.generators.schema import HiveSchemaGenerator

        class ListModel(BaseModel):
            tags: list[str]
            items: list[int]

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(ListModel)

        props = schema.get("properties", {})
        assert props["tags"]["type"] == "array"
        assert props["tags"]["items"]["type"] == "string"

    def test_generator_handles_dict_types(self) -> None:
        """Generator correctly maps dict types."""
        from hive.generators.schema import HiveSchemaGenerator

        class DictModel(BaseModel):
            metadata: dict[str, str]

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(DictModel)

        props = schema.get("properties", {})
        assert props["metadata"]["type"] == "object"
        assert props["metadata"].get("additionalProperties", {}).get("type") == "string"


class TestSchemaConstraintMapping:
    """Test that Pydantic constraints map to JSON Schema."""

    def test_string_min_max_length(self) -> None:
        """String min/max length constraints are preserved."""
        from hive.generators.schema import HiveSchemaGenerator

        class ConstrainedModel(BaseModel):
            name: Annotated[str, Field(min_length=1, max_length=100)]

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(ConstrainedModel)

        props = schema.get("properties", {})
        assert props["name"].get("minLength") == 1
        assert props["name"].get("maxLength") == 100

    def test_numeric_min_max(self) -> None:
        """Numeric min/max constraints are preserved."""
        from hive.generators.schema import HiveSchemaGenerator

        class ConstrainedModel(BaseModel):
            priority: Annotated[int, Field(ge=1, le=5)]

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(ConstrainedModel)

        props = schema.get("properties", {})
        assert props["priority"].get("minimum") == 1
        assert props["priority"].get("maximum") == 5

    def test_pattern_constraint(self) -> None:
        """String pattern constraint is preserved."""
        from hive.generators.schema import HiveSchemaGenerator

        class ConstrainedModel(BaseModel):
            slug: Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]

        generator = HiveSchemaGenerator()
        schema = generator.generate_schema(ConstrainedModel)

        props = schema.get("properties", {})
        assert props["slug"].get("pattern") == "^[a-z0-9-]+$"
