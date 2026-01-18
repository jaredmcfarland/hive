"""Test refinement types validate correctly at runtime."""

from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation
import pytest


class TestPositiveInt:
    """Tests for PositiveInt refinement type."""

    def test_accepts_positive_integer(self) -> None:
        """PositiveInt accepts integers > 0."""
        from hive.types import PositiveInt

        @beartype
        def fn(x: PositiveInt) -> int:
            return x

        assert fn(1) == 1
        assert fn(100) == 100

    def test_rejects_zero(self) -> None:
        """PositiveInt rejects zero."""
        from hive.types import PositiveInt

        @beartype
        def fn(x: PositiveInt) -> int:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(0)

    def test_rejects_negative(self) -> None:
        """PositiveInt rejects negative integers."""
        from hive.types import PositiveInt

        @beartype
        def fn(x: PositiveInt) -> int:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(-1)


class TestNonNegativeInt:
    """Tests for NonNegativeInt refinement type."""

    def test_accepts_zero(self) -> None:
        """NonNegativeInt accepts zero."""
        from hive.types import NonNegativeInt

        @beartype
        def fn(x: NonNegativeInt) -> int:
            return x

        assert fn(0) == 0

    def test_accepts_positive(self) -> None:
        """NonNegativeInt accepts positive integers."""
        from hive.types import NonNegativeInt

        @beartype
        def fn(x: NonNegativeInt) -> int:
            return x

        assert fn(42) == 42

    def test_rejects_negative(self) -> None:
        """NonNegativeInt rejects negative integers."""
        from hive.types import NonNegativeInt

        @beartype
        def fn(x: NonNegativeInt) -> int:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(-1)


class TestUnitInterval:
    """Tests for UnitInterval (0.0-1.0) refinement type."""

    def test_accepts_zero(self) -> None:
        """UnitInterval accepts 0.0."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        assert fn(0.0) == 0.0

    def test_accepts_one(self) -> None:
        """UnitInterval accepts 1.0."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        assert fn(1.0) == 1.0

    def test_accepts_middle_value(self) -> None:
        """UnitInterval accepts values between 0 and 1."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        assert fn(0.5) == 0.5

    def test_rejects_negative(self) -> None:
        """UnitInterval rejects negative values."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(-0.1)

    def test_rejects_above_one(self) -> None:
        """UnitInterval rejects values > 1."""
        from hive.types import UnitInterval

        @beartype
        def fn(x: UnitInterval) -> float:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(1.1)


class TestPercentage:
    """Tests for Percentage (0.0-100.0) refinement type."""

    def test_accepts_valid_percentage(self) -> None:
        """Percentage accepts 0-100."""
        from hive.types import Percentage

        @beartype
        def fn(x: Percentage) -> float:
            return x

        assert fn(0.0) == 0.0
        assert fn(50.0) == 50.0
        assert fn(100.0) == 100.0

    def test_rejects_over_100(self) -> None:
        """Percentage rejects values > 100."""
        from hive.types import Percentage

        @beartype
        def fn(x: Percentage) -> float:
            return x

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(101.0)
