"""Unit tests for Python to JSON Schema type mapping.

Tests the type mapping utilities in src/hive/generators/schema.py
that convert Python types to JSON Schema types.

RED phase: These tests should FAIL until type mapping is implemented.
"""

from datetime import date, datetime
from uuid import UUID

import pytest


class TestBasicTypeMapping:
    """Tests for basic Python to JSON Schema type mapping."""

    def test_str_maps_to_string(self) -> None:
        """Python str maps to JSON Schema string."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(str)
        assert result["type"] == "string"

    def test_int_maps_to_integer(self) -> None:
        """Python int maps to JSON Schema integer."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(int)
        assert result["type"] == "integer"

    def test_float_maps_to_number(self) -> None:
        """Python float maps to JSON Schema number."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(float)
        assert result["type"] == "number"

    def test_bool_maps_to_boolean(self) -> None:
        """Python bool maps to JSON Schema boolean."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(bool)
        assert result["type"] == "boolean"

    def test_none_maps_to_null(self) -> None:
        """Python None maps to JSON Schema null."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(type(None))
        assert result["type"] == "null"


class TestDateTimeMapping:
    """Tests for date/time type mapping."""

    def test_datetime_maps_to_datetime_format(self) -> None:
        """Python datetime maps to string with date-time format."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(datetime)
        assert result["type"] == "string"
        assert result["format"] == "date-time"

    def test_date_maps_to_date_format(self) -> None:
        """Python date maps to string with date format."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(date)
        assert result["type"] == "string"
        assert result["format"] == "date"

    def test_uuid_maps_to_uuid_format(self) -> None:
        """Python UUID maps to string with uuid format."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(UUID)
        assert result["type"] == "string"
        assert result["format"] == "uuid"


class TestCollectionTypeMapping:
    """Tests for collection type mapping."""

    def test_list_maps_to_array(self) -> None:
        """Python list maps to JSON Schema array."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(list[str])
        assert result["type"] == "array"
        assert result["items"]["type"] == "string"

    def test_dict_maps_to_object(self) -> None:
        """Python dict maps to JSON Schema object."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(dict[str, int])
        assert result["type"] == "object"
        assert result["additionalProperties"]["type"] == "integer"


class TestRefinementTypeMapping:
    """Tests for Hive refinement type mapping to JSON Schema constraints."""

    def test_positive_int_has_minimum(self) -> None:
        """PositiveInt maps to integer with minimum: 1."""
        from hive.generators.schema import python_type_to_json_schema
        from hive.types import PositiveInt

        result = python_type_to_json_schema(PositiveInt)
        assert result["type"] == "integer"
        assert result["minimum"] == 1

    def test_percentage_has_range(self) -> None:
        """Percentage maps to number with minimum: 0, maximum: 100."""
        from hive.generators.schema import python_type_to_json_schema
        from hive.types import Percentage

        result = python_type_to_json_schema(Percentage)
        assert result["type"] == "number"
        assert result["minimum"] == 0
        assert result["maximum"] == 100

    def test_port_has_range(self) -> None:
        """Port maps to integer with minimum: 1, maximum: 65535."""
        from hive.generators.schema import python_type_to_json_schema
        from hive.types import Port

        result = python_type_to_json_schema(Port)
        assert result["type"] == "integer"
        assert result["minimum"] == 1
        assert result["maximum"] == 65535

    def test_non_empty_str_has_min_length(self) -> None:
        """NonEmptyStr maps to string with minLength: 1."""
        from hive.generators.schema import python_type_to_json_schema
        from hive.types import NonEmptyStr

        result = python_type_to_json_schema(NonEmptyStr)
        assert result["type"] == "string"
        assert result["minLength"] == 1

    def test_email_has_format(self) -> None:
        """Email maps to string with format: email."""
        from hive.generators.schema import python_type_to_json_schema
        from hive.types import Email

        result = python_type_to_json_schema(Email)
        assert result["type"] == "string"
        assert result["format"] == "email"

    def test_url_has_format(self) -> None:
        """Url maps to string with format: uri."""
        from hive.generators.schema import python_type_to_json_schema
        from hive.types import Url

        result = python_type_to_json_schema(Url)
        assert result["type"] == "string"
        assert result["format"] == "uri"


class TestOptionalTypeMapping:
    """Tests for Optional/Union type mapping."""

    def test_optional_allows_null(self) -> None:
        """Optional[str] creates anyOf with string and null."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(str | None)
        # Should be anyOf or type: [string, null]
        if "anyOf" in result:
            types = [s.get("type") for s in result["anyOf"]]
            assert "string" in types
            assert "null" in types
        elif isinstance(result.get("type"), list):
            assert "string" in result["type"]
            assert "null" in result["type"]
        else:
            pytest.fail("Optional type not correctly represented")

    def test_union_type_creates_any_of(self) -> None:
        """Union types create anyOf schema."""
        from hive.generators.schema import python_type_to_json_schema

        result = python_type_to_json_schema(str | int)
        assert "anyOf" in result or isinstance(result.get("type"), list)
