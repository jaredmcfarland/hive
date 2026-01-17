"""Test Hypothesis strategies for Hive refinement types."""

from hypothesis import given, settings


class TestStrategyForType:
    """Tests for strategy_for_type function."""

    @given(x=...)
    @settings(max_examples=50)
    def test_generates_valid_positive_int(self, x: int) -> None:
        """Strategy generates only positive integers for PositiveInt."""

        # Replace the ... with actual strategy
        pass

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
