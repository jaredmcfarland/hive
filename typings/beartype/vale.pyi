"""Type stubs for beartype.vale module."""

from collections.abc import Callable
from typing import Any

class _IsFactory:
    """Factory for Is[] type constraints."""

    def __getitem__(self, validator: Callable[[Any], bool]) -> Any: ...

Is: _IsFactory
