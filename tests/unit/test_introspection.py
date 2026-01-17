"""Test constraint metadata extraction from refinement types."""




class TestExtractConstraints:
    """Tests for extract_constraints function."""

    def test_returns_none_for_plain_type(self) -> None:
        """extract_constraints returns None for plain types."""
        from hive.types.introspection import extract_constraints

        assert extract_constraints(int) is None
        assert extract_constraints(str) is None
        assert extract_constraints(float) is None

    def test_extracts_base_type_from_annotated(self) -> None:
        """extract_constraints extracts base type from Annotated."""
        from hive.types import PositiveInt
        from hive.types.introspection import extract_constraints

        info = extract_constraints(PositiveInt)

        assert info is not None
        assert info.base_type is int

    def test_extracts_min_value_from_positive_int(self) -> None:
        """extract_constraints extracts min_value from PositiveInt."""
        from hive.types import PositiveInt
        from hive.types.introspection import extract_constraints

        info = extract_constraints(PositiveInt)

        assert info is not None
        # PositiveInt is x > 0, so minimum is effectively 1 for integers
        # but we detect the constraint pattern

    def test_extracts_bounds_from_port(self) -> None:
        """extract_constraints extracts min/max from Port type."""
        from hive.types import Port
        from hive.types.introspection import extract_constraints

        info = extract_constraints(Port)

        assert info is not None
        assert info.base_type is int
        assert info.min_value == 1
        assert info.max_value == 65535

    def test_extracts_bounds_from_percentage(self) -> None:
        """extract_constraints extracts bounds from Percentage."""
        from hive.types import Percentage
        from hive.types.introspection import extract_constraints

        info = extract_constraints(Percentage)

        assert info is not None
        assert info.base_type is float
        assert info.min_value == 0.0
        assert info.max_value == 100.0

    def test_extracts_validator_function(self) -> None:
        """extract_constraints extracts the validator callable."""
        from hive.types import PositiveInt
        from hive.types.introspection import extract_constraints

        info = extract_constraints(PositiveInt)

        assert info is not None
        assert info.validator is not None
        assert info.validator(5) is True
        assert info.validator(0) is False
        assert info.validator(-1) is False


class TestConstraintInfoDataclass:
    """Tests for ConstraintInfo dataclass."""

    def test_has_expected_fields(self) -> None:
        """ConstraintInfo has all expected fields."""
        from hive.types.introspection import ConstraintInfo

        info = ConstraintInfo(
            base_type=int,
            description="test",
            validator=None,
            min_value=1,
            max_value=100,
        )

        assert info.base_type is int
        assert info.description == "test"
        assert info.min_value == 1
        assert info.max_value == 100
        assert info.pattern is None
        assert info.min_length is None
        assert info.max_length is None
