"""Test string refinement types."""

import pytest
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation


class TestNonEmptyStr:
    """Tests for NonEmptyStr refinement type."""

    def test_accepts_non_empty_string(self) -> None:
        """NonEmptyStr accepts strings with content."""
        from hive.types import NonEmptyStr

        @beartype
        def fn(s: NonEmptyStr) -> str:
            return s

        assert fn("hello") == "hello"
        assert fn(" ") == " "  # whitespace is content

    def test_rejects_empty_string(self) -> None:
        """NonEmptyStr rejects empty string."""
        from hive.types import NonEmptyStr

        @beartype
        def fn(s: NonEmptyStr) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("")


class TestIdentifier:
    """Tests for Identifier (Python identifier) refinement type."""

    def test_accepts_valid_identifier(self) -> None:
        """Identifier accepts valid Python identifiers."""
        from hive.types import Identifier

        @beartype
        def fn(s: Identifier) -> str:
            return s

        assert fn("my_var") == "my_var"
        assert fn("_private") == "_private"
        assert fn("CamelCase") == "CamelCase"

    def test_rejects_starting_with_digit(self) -> None:
        """Identifier rejects strings starting with digit."""
        from hive.types import Identifier

        @beartype
        def fn(s: Identifier) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("123abc")

    def test_rejects_hyphenated(self) -> None:
        """Identifier rejects hyphenated strings."""
        from hive.types import Identifier

        @beartype
        def fn(s: Identifier) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("my-var")


class TestSlug:
    """Tests for Slug (URL-safe) refinement type."""

    def test_accepts_valid_slug(self) -> None:
        """Slug accepts lowercase alphanumeric with hyphens."""
        from hive.types import Slug

        @beartype
        def fn(s: Slug) -> str:
            return s

        assert fn("my-slug") == "my-slug"
        assert fn("post123") == "post123"
        assert fn("a") == "a"

    def test_rejects_uppercase(self) -> None:
        """Slug rejects uppercase letters."""
        from hive.types import Slug

        @beartype
        def fn(s: Slug) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("My-Slug")

    def test_rejects_underscores(self) -> None:
        """Slug rejects underscores."""
        from hive.types import Slug

        @beartype
        def fn(s: Slug) -> str:
            return s

        with pytest.raises(BeartypeCallHintParamViolation):
            fn("my_slug")
