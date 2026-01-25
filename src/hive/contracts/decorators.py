"""Hive-specific contract decorators wrapping deal."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import deal

from hive.errors import CommandError

F = TypeVar("F", bound=Callable[..., Any])


def requires(condition: Callable[..., bool], message: str = "") -> Callable[[F], F]:
    """
    Precondition decorator for Hive commands.

    Like deal.pre but raises CommandError instead of PreContractError,
    ensuring proper CLI exit codes and user-friendly messages.

    Args:
        condition: Lambda that returns True if precondition is met.
                   Receives same arguments as decorated function.
        message: Error message if precondition fails.

    Example:
        @command(app)
        @requires(lambda ctx, user_id: user_id > 0, "User ID must be positive")
        async def get_user(ctx, user_id: int) -> User:
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not condition(*args, **kwargs):
                raise CommandError(message or "Precondition failed", exit_code=1)
            return await func(*args, **kwargs)

        # Store contract metadata for introspection
        existing_requires: list[dict[str, Any]] = getattr(func, "__hive_requires__", [])
        wrapper.__hive_requires__ = [  # type: ignore[attr-defined]
            *existing_requires,
            {"condition": condition, "message": message},
        ]

        return wrapper  # type: ignore[return-value]

    return decorator


def ensures(condition: Callable[..., bool], message: str = "") -> Callable[[F], F]:
    """
    Postcondition decorator for Hive commands.

    Like deal.ensure but raises CommandError for Hive integration.

    Args:
        condition: Lambda that returns True if postcondition is met.
                   Receives original arguments plus 'result' keyword.
        message: Error message if postcondition fails.

    Example:
        @command(app)
        @ensures(lambda ctx, task_id, result: result.id == task_id)
        async def get_task(ctx, task_id: int) -> Task:
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            if not condition(*args, result=result, **kwargs):
                raise CommandError(message or "Postcondition failed", exit_code=70)
            return result

        # Store contract metadata for introspection
        existing_ensures: list[dict[str, Any]] = getattr(func, "__hive_ensures__", [])
        wrapper.__hive_ensures__ = [  # type: ignore[attr-defined]
            *existing_ensures,
            {"condition": condition, "message": message},
        ]

        return wrapper  # type: ignore[return-value]

    return decorator


def invariant(condition: Callable[[Any], bool], message: str = "") -> Callable[[type], type]:
    """
    Class invariant decorator for Hive entities.

    Wraps deal.inv with Hive-specific error handling.

    Example:
        @entity(app)
        @invariant(lambda self: self.balance >= 0, "Balance cannot be negative")
        class Account(SQLModel, table=True):
            balance: float = 0.0
    """
    return deal.inv(condition, message=message)
