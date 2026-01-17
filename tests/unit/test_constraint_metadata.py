"""Test ConstraintMetadata dataclass in core types."""



class TestConstraintMetadata:
    """Tests for ConstraintMetadata dataclass."""

    def test_can_instantiate_with_defaults(self) -> None:
        """ConstraintMetadata can be instantiated with defaults."""
        from hive.core.types import ConstraintMetadata

        meta = ConstraintMetadata()

        assert meta.description == ""
        assert meta.min_value is None
        assert meta.max_value is None
        assert meta.pattern is None
        assert meta.min_length is None
        assert meta.max_length is None
        assert meta.validator is None

    def test_can_instantiate_with_values(self) -> None:
        """ConstraintMetadata accepts all constraint fields."""
        from hive.core.types import ConstraintMetadata

        def validator(x: int) -> bool:
            return x > 0

        meta = ConstraintMetadata(
            description="positive integer",
            min_value=1.0,
            max_value=100.0,
            pattern=None,
            min_length=None,
            max_length=None,
            validator=validator,
        )

        assert meta.description == "positive integer"
        assert meta.min_value == 1.0
        assert meta.max_value == 100.0
        assert meta.validator is validator


class TestParameterInfoWithConstraints:
    """Tests for ParameterInfo with constraints field."""

    def test_parameter_info_has_constraints_field(self) -> None:
        """ParameterInfo has optional constraints field."""
        from hive.core.types import ParameterInfo, ParameterKind

        param = ParameterInfo(
            name="age",
            type=int,
            default=None,
            has_default=False,
            kind=ParameterKind.KEYWORD,
        )

        assert param.constraints is None

    def test_parameter_info_accepts_constraints(self) -> None:
        """ParameterInfo accepts ConstraintMetadata."""
        from hive.core.types import ConstraintMetadata, ParameterInfo, ParameterKind

        meta = ConstraintMetadata(
            description="positive integer",
            min_value=1.0,
        )

        param = ParameterInfo(
            name="age",
            type=int,
            default=None,
            has_default=False,
            kind=ParameterKind.KEYWORD,
            constraints=meta,
        )

        assert param.constraints is not None
        assert param.constraints.description == "positive integer"
        assert param.constraints.min_value == 1.0
