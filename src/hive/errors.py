"""Hive framework error classes."""

from __future__ import annotations


class HiveError(Exception):
    """Base class for all Hive errors.

    All framework errors inherit from this class to allow catching
    any Hive-specific error with a single except clause.
    """

    exit_code: int = 1


class CommandError(HiveError):
    """Raised when a command fails due to user input or business logic.

    Use this error to signal expected failures that should be reported
    to the user with a helpful message.

    Example:
        @command(app)
        async def delete(ctx, task_id: int) -> None:
            task = await ctx.db.get(Task, task_id)
            if not task:
                raise CommandError(f"Task {task_id} not found")
    """

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class ConfigurationError(HiveError):
    """Raised when configuration is missing or invalid.

    Uses exit code 78 (EX_CONFIG) following BSD sysexits.h conventions.
    """

    exit_code = 78


class RegistrationError(HiveError):
    """Raised when decorator registration fails.

    This includes duplicate names, invalid targets, or other
    registration-time validation failures.
    """


class ValidationError(HiveError):
    """Raised when app.validate() detects issues.

    Contains details about what validation failed.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
