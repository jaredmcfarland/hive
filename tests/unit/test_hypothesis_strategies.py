"""Test Hypothesis strategies for Hive refinement types."""

from hypothesis import given, settings


class TestStrategyForType:
    """Tests for strategy_for_type function."""

    @given(x=...)
    @settings(max_examples=50)
    def test_generates_valid_positive_int(self, x: int) -> None:
        """Strategy generates only positive integers for PositiveInt."""

        # Replace the ... with actual strategy

    def test_positive_int_strategy_generates_valid_values(self) -> None:
        """PositiveInt strategy only generates x > 0."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type
        from hive.types import PositiveInt

        strategy = strategy_for_type(PositiveInt)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: int) -> None:
            assert x > 0

        check()

    def test_port_strategy_generates_valid_values(self) -> None:
        """Port strategy generates 1-65535."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type
        from hive.types import Port

        strategy = strategy_for_type(Port)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: int) -> None:
            assert 1 <= x <= 65535

        check()

    def test_percentage_strategy_generates_valid_values(self) -> None:
        """Percentage strategy generates 0.0-100.0."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type
        from hive.types import Percentage

        strategy = strategy_for_type(Percentage)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: float) -> None:
            assert 0.0 <= x <= 100.0

        check()

    def test_plain_int_strategy(self) -> None:
        """Plain int generates any integer."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type

        strategy = strategy_for_type(int)

        @given(x=strategy)
        @settings(max_examples=20)
        def check(x: int) -> None:
            assert isinstance(x, int)

        check()

    def test_plain_str_strategy(self) -> None:
        """Plain str generates any string."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type

        strategy = strategy_for_type(str)

        @given(x=strategy)
        @settings(max_examples=20)
        def check(x: str) -> None:
            assert isinstance(x, str)

        check()

    def test_plain_bool_strategy(self) -> None:
        """Plain bool generates True or False."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type

        strategy = strategy_for_type(bool)

        @given(x=strategy)
        @settings(max_examples=20)
        def check(x: bool) -> None:
            assert isinstance(x, bool)

        check()

    def test_plain_bytes_strategy(self) -> None:
        """Plain bytes generates any bytes."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type

        strategy = strategy_for_type(bytes)

        @given(x=strategy)
        @settings(max_examples=20)
        def check(x: bytes) -> None:
            assert isinstance(x, bytes)

        check()

    def test_plain_float_strategy(self) -> None:
        """Plain float generates finite floats."""
        import math

        from hypothesis import given, settings

        from hive.testing import strategy_for_type

        strategy = strategy_for_type(float)

        @given(x=strategy)
        @settings(max_examples=20)
        def check(x: float) -> None:
            assert isinstance(x, float)
            assert not math.isnan(x)
            assert not math.isinf(x)

        check()

    def test_non_empty_str_strategy(self) -> None:
        """NonEmptyStr strategy generates non-empty strings."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type
        from hive.types import NonEmptyStr

        strategy = strategy_for_type(NonEmptyStr)

        @given(x=strategy)
        @settings(max_examples=50)
        def check(x: str) -> None:
            assert len(x) > 0

        check()

    def test_unit_interval_strategy(self) -> None:
        """UnitInterval strategy generates 0.0-1.0."""
        from hypothesis import given, settings

        from hive.testing import strategy_for_type
        from hive.types import UnitInterval

        strategy = strategy_for_type(UnitInterval)

        @given(x=strategy)
        @settings(max_examples=100)
        def check(x: float) -> None:
            assert 0.0 <= x <= 1.0

        check()
