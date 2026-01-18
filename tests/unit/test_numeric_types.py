"""Test domain-specific numeric refinement types."""

from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation
import pytest


class TestPort:
    """Tests for Port (1-65535) refinement type."""

    def test_accepts_valid_port(self) -> None:
        """Port accepts valid port numbers."""
        from hive.types import Port

        @beartype
        def fn(p: Port) -> int:
            return p

        assert fn(1) == 1
        assert fn(80) == 80
        assert fn(8080) == 8080
        assert fn(65535) == 65535

    def test_rejects_zero(self) -> None:
        """Port rejects 0."""
        from hive.types import Port

        @beartype
        def fn(p: Port) -> int:
            return p

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(0)

    def test_rejects_above_65535(self) -> None:
        """Port rejects values > 65535."""
        from hive.types import Port

        @beartype
        def fn(p: Port) -> int:
            return p

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(65536)


class TestHttpStatusCode:
    """Tests for HttpStatusCode (100-599) refinement type."""

    def test_accepts_valid_status_codes(self) -> None:
        """HttpStatusCode accepts valid HTTP status codes."""
        from hive.types import HttpStatusCode

        @beartype
        def fn(code: HttpStatusCode) -> int:
            return code

        assert fn(200) == 200
        assert fn(404) == 404
        assert fn(500) == 500

    def test_rejects_below_100(self) -> None:
        """HttpStatusCode rejects values < 100."""
        from hive.types import HttpStatusCode

        @beartype
        def fn(code: HttpStatusCode) -> int:
            return code

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(99)


class TestMonth:
    """Tests for Month (1-12) refinement type."""

    def test_accepts_valid_months(self) -> None:
        """Month accepts 1-12."""
        from hive.types import Month

        @beartype
        def fn(m: Month) -> int:
            return m

        assert fn(1) == 1
        assert fn(12) == 12

    def test_rejects_zero(self) -> None:
        """Month rejects 0."""
        from hive.types import Month

        @beartype
        def fn(m: Month) -> int:
            return m

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(0)

    def test_rejects_13(self) -> None:
        """Month rejects 13."""
        from hive.types import Month

        @beartype
        def fn(m: Month) -> int:
            return m

        with pytest.raises(BeartypeCallHintParamViolation):
            fn(13)
