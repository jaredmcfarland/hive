"""Execution context for commands."""

from types import TracebackType
from typing import Self

import deal
from sqlalchemy.ext.asyncio import AsyncSession

from hive.runtime.config import AppSettings
from hive.runtime.database import create_session_factory
from hive.runtime.output import OutputFormat, OutputFormatter


class ExecutionContext:
    """Runtime context provided to commands.

    Manages the database session, configuration, and output formatting.
    Implements async context manager protocol for automatic transaction
    management.

    Example:
        async with ExecutionContext(settings=settings) as ctx:
            result = await ctx.db.exec(select(Task))
            ctx.output.result(result)
    """

    def __init__(
        self,
        settings: AppSettings | None = None,
        output_format: OutputFormat = OutputFormat.TABLE,
        command_name: str = "",
        quiet: bool = False,
        yes: bool = False,
    ) -> None:
        """Initialize the execution context.

        Args:
            settings: Application settings (uses defaults if not provided).
            output_format: Output format for this command.
            command_name: Name of the executing command.
            quiet: Suppress non-essential output.
            yes: Bypass confirmation prompts.
        """
        self._settings = settings or AppSettings()
        self._output_format = output_format
        self._command_name = command_name
        self._quiet = quiet
        self._yes = yes

        self._session_factory = create_session_factory(
            self._settings.database_url,
            echo=self._settings.debug,
        )
        self._session: AsyncSession | None = None
        self._output = OutputFormatter(format=output_format, quiet=quiet)

        # State tracking for invariants
        self._closed = False
        self._committed = False
        self._rolled_back = False

    @property
    @deal.pre(lambda self: not self._closed, message="Context is closed")
    def db(self) -> AsyncSession:
        """Database session for operations."""
        if self._session is None:
            raise RuntimeError("Context not entered. Use 'async with' statement.")
        return self._session

    @property
    def config(self) -> AppSettings:
        """Application configuration."""
        return self._settings

    @property
    def output(self) -> OutputFormatter:
        """Format-aware output handler."""
        return self._output

    @property
    def command_name(self) -> str:
        """Name of the executing command."""
        return self._command_name

    @property
    def output_format(self) -> OutputFormat:
        """Requested output format."""
        return self._output_format

    @property
    def interactive(self) -> bool:
        """True if TTY is attached."""
        import sys

        return sys.stdin.isatty() and sys.stdout.isatty()

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.pre(lambda self: not self._committed, message="Already committed")
    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session:
            await self._session.commit()
        self._committed = True

    @deal.pre(lambda self: not self._closed, message="Context is closed")
    @deal.pre(lambda self: not self._rolled_back, message="Already rolled back")
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()
        self._rolled_back = True

    async def __aenter__(self) -> Self:
        """Enter the context, creating a database session."""
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit the context, committing or rolling back as appropriate.

        Returns:
            False to re-raise any exception.
        """
        if self._session is None:
            self._closed = True
            return False

        try:
            if exc_type is None and not self._committed and not self._rolled_back:
                # Success - commit the transaction
                await self._session.commit()
                self._committed = True
            elif exc_type is not None and not self._rolled_back:
                # Exception occurred - rollback
                await self._session.rollback()
                self._rolled_back = True
        finally:
            await self._session.close()
            self._session = None
            self._closed = True

        return False  # Re-raise any exception
