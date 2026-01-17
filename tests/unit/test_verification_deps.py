"""Test that verification dependencies are available."""

import pytest


def test_beartype_importable() -> None:
    """Verify beartype is installed and importable."""
    from beartype import beartype
    from beartype.vale import Is
    from beartype.roar import BeartypeCallHintParamViolation

    assert callable(beartype)


def test_deal_importable() -> None:
    """Verify deal is installed and importable."""
    import deal

    assert hasattr(deal, 'pre')
    assert hasattr(deal, 'post')
    assert hasattr(deal, 'ensure')
    assert hasattr(deal, 'inv')


def test_hypothesis_importable() -> None:
    """Verify hypothesis is installed and importable."""
    from hypothesis import given, strategies as st

    assert callable(given)
    assert hasattr(st, 'integers')
