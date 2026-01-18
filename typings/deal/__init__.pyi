"""Type stubs for deal library."""

from collections.abc import Callable
from typing import TypeVar

_C = TypeVar("_C", bound=Callable[..., object])
_T = TypeVar("_T")

def pre(
    validator: Callable[..., bool],
    *,
    message: str | None = None,
    exception: type[Exception] | Exception | None = None,
) -> Callable[[_C], _C]: ...
def post(
    validator: Callable[..., bool],
    *,
    message: str | None = None,
    exception: type[Exception] | Exception | None = None,
) -> Callable[[_C], _C]: ...
def ensure(
    validator: Callable[..., bool],
    *,
    message: str | None = None,
    exception: type[Exception] | Exception | None = None,
) -> Callable[[_C], _C]: ...
def inv(
    validator: Callable[[_T], bool],
    *,
    message: str | None = None,
    exception: type[Exception] | Exception | None = None,
) -> Callable[[type[_T]], type[_T]]: ...
def raises(
    *exceptions: type[Exception],
) -> Callable[[_C], _C]: ...
def reason(
    event: type[Exception],
    validator: Callable[..., bool],
    *,
    message: str | None = None,
) -> Callable[[_C], _C]: ...
