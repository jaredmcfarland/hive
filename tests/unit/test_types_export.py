"""Test that types are properly exported from hive package."""


def test_types_importable_from_hive_types() -> None:
    """Common types importable from hive.types."""
    from hive.types import (
        Port,
        PositiveInt,
    )

    # Just verify they're importable (actual behavior tested elsewhere)
    assert PositiveInt is not None
    assert Port is not None


def test_types_module_has_all_exports() -> None:
    """hive.types.__all__ contains expected types."""
    from hive import types

    expected = [
        "PositiveInt",
        "NonNegativeInt",
        "Percentage",
        "Port",
        "NonEmptyStr",
        "Email",
    ]

    for name in expected:
        assert name in types.__all__, f"{name} missing from hive.types.__all__"
