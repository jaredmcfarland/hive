"""Unit tests for constraint extraction utilities.

Tests that refinement types like PositiveInt, Email, etc. are correctly
converted to JSON Schema constraints.

RED phase: These tests should FAIL until constraint extraction is implemented.
"""


class TestConstraintExtraction:
    """Unit tests for constraint extraction from refinement types."""

    def test_extract_constraints_from_positive_int(self) -> None:
        """PositiveInt extracts minimum: 1 constraint."""
        from hive.spec.constraints import extract_json_schema_constraints
        from hive.types import PositiveInt

        constraints = extract_json_schema_constraints(PositiveInt)

        assert constraints.get("minimum") == 1
        assert constraints.get("type") == "integer"

    def test_extract_constraints_from_percentage(self) -> None:
        """Percentage extracts minimum: 0, maximum: 100 constraints."""
        from hive.spec.constraints import extract_json_schema_constraints
        from hive.types import Percentage

        constraints = extract_json_schema_constraints(Percentage)

        assert constraints.get("minimum") == 0
        assert constraints.get("maximum") == 100
        assert constraints.get("type") == "number"

    def test_extract_constraints_from_port(self) -> None:
        """Port extracts minimum: 1, maximum: 65535 constraints."""
        from hive.spec.constraints import extract_json_schema_constraints
        from hive.types import Port

        constraints = extract_json_schema_constraints(Port)

        assert constraints.get("minimum") == 1
        assert constraints.get("maximum") == 65535

    def test_extract_constraints_from_non_empty_str(self) -> None:
        """NonEmptyStr extracts minLength: 1 constraint."""
        from hive.spec.constraints import extract_json_schema_constraints
        from hive.types import NonEmptyStr

        constraints = extract_json_schema_constraints(NonEmptyStr)

        assert constraints.get("minLength") == 1
        assert constraints.get("type") == "string"

    def test_extract_constraints_from_email(self) -> None:
        """Email extracts format: email constraint."""
        from hive.spec.constraints import extract_json_schema_constraints
        from hive.types import Email

        constraints = extract_json_schema_constraints(Email)

        assert constraints.get("format") == "email"
        assert constraints.get("type") == "string"

    def test_extract_constraints_from_url(self) -> None:
        """Url extracts format: uri constraint."""
        from hive.spec.constraints import extract_json_schema_constraints
        from hive.types import Url

        constraints = extract_json_schema_constraints(Url)

        assert constraints.get("format") == "uri"
        assert constraints.get("type") == "string"

    def test_extract_constraints_from_basic_type(self) -> None:
        """Basic types return type only, no constraints."""
        from hive.spec.constraints import extract_json_schema_constraints

        constraints = extract_json_schema_constraints(str)
        assert constraints == {"type": "string"}

        constraints = extract_json_schema_constraints(int)
        assert constraints == {"type": "integer"}

        constraints = extract_json_schema_constraints(float)
        assert constraints == {"type": "number"}

        constraints = extract_json_schema_constraints(bool)
        assert constraints == {"type": "boolean"}


class TestParameterToJsonSchema:
    """Tests for converting command parameters to JSON Schema."""

    def test_parameter_info_to_schema(self) -> None:
        """ParameterInfo converts to JSON Schema dict."""
        from hive.core.types import ConstraintMetadata, ParameterInfo
        from hive.spec.constraints import parameter_to_json_schema

        param = ParameterInfo(
            name="priority",
            type=int,
            default=1,
            has_default=True,
            constraints=ConstraintMetadata(min_value=1, max_value=5),
        )

        schema = parameter_to_json_schema(param)

        assert schema["name"] == "priority"
        assert schema["type"] == "integer"
        assert schema["default"] == 1
        assert schema["required"] is False  # Has default
        assert schema.get("minimum") == 1
        assert schema.get("maximum") == 5

    def test_required_parameter_to_schema(self) -> None:
        """Required parameter has required: true."""
        from hive.core.types import ParameterInfo
        from hive.spec.constraints import parameter_to_json_schema

        param = ParameterInfo(
            name="title",
            type=str,
            has_default=False,
        )

        schema = parameter_to_json_schema(param)

        assert schema["name"] == "title"
        assert schema["required"] is True

    def test_optional_parameter_to_schema(self) -> None:
        """Optional parameter has required: false."""
        from hive.core.types import ParameterInfo
        from hive.spec.constraints import parameter_to_json_schema

        param = ParameterInfo(
            name="description",
            type=str,
            default=None,
            has_default=True,
        )

        schema = parameter_to_json_schema(param)

        assert schema["name"] == "description"
        assert schema["required"] is False
