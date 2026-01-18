"""Type stubs for beartype library."""

from collections.abc import Callable
from typing import TypeVar

_C = TypeVar("_C", bound=Callable[..., object])

def beartype[C: Callable[..., object]](func: _C) -> _C: ...
