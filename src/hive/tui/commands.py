"""Command palette integration using Textual's built-in command system.

Provides a Provider that exposes Hive registry commands through
Textual's native command palette (Ctrl+P).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from hive.core.registry import ApplicationRegistry
    from hive.core.types import CommandRegistration


class HiveCommandProvider(Provider):
    """Command provider that exposes Hive registry commands.

    Integrates with Textual's built-in command palette to provide
    fuzzy-searchable access to all registered Hive commands.

    Example:
        class MyApp(App):
            COMMANDS = {HiveCommandProvider}

            def __init__(self, registry: ApplicationRegistry):
                super().__init__()
                self._hive_registry = registry
    """

    @property
    def _registry(self) -> ApplicationRegistry | None:
        """Get the Hive registry from the app.

        Returns:
            The application registry, or None if not available.
        """
        # Access the registry from the app - HiveApp stores it as _hive_registry
        app = self.app
        return getattr(app, "_hive_registry", None)

    @override
    async def discover(self) -> Hits:
        """Discover all available commands when palette opens with empty input.

        Yields:
            DiscoveryHit for each visible command.
        """
        registry = self._registry
        if registry is None:
            return

        commands = registry.list_commands()
        for cmd in commands:
            if cmd.hidden:
                continue

            yield DiscoveryHit(
                display=cmd.name,
                command=self._create_command_callback(cmd),
                help=cmd.docstring or "",
            )

    @override
    async def search(self, query: str) -> Hits:
        """Search commands matching the query.

        Uses Textual's built-in matcher for fuzzy matching.

        Args:
            query: Search query string.

        Yields:
            Hit for each matching command.
        """
        registry = self._registry
        if registry is None:
            return

        matcher = self.matcher(query)
        commands = registry.list_commands()

        for cmd in commands:
            if cmd.hidden:
                continue

            # Match against command name
            match = matcher.match(cmd.name)
            if match:
                yield Hit(
                    score=match,
                    match_display=matcher.highlight(cmd.name),
                    command=self._create_command_callback(cmd),
                    help=cmd.docstring or "",
                )
            # Also try matching against docstring
            elif cmd.docstring:
                doc_match = matcher.match(cmd.docstring)
                if doc_match:
                    yield Hit(
                        score=doc_match * 0.5,  # Lower priority for doc matches
                        match_display=cmd.name,
                        command=self._create_command_callback(cmd),
                        help=cmd.docstring,  # Use plain text for help
                    )

    def _create_command_callback(self, cmd: CommandRegistration) -> Any:
        """Create a callback function for executing a command.

        Args:
            cmd: Command registration.

        Returns:
            Callback that shows the parameter modal when invoked.
        """

        async def execute_command() -> None:
            """Execute the command via parameter modal."""
            # Import here to avoid circular dependency
            from hive.tui.widgets.modal import ParameterModal  # noqa: PLC0415

            app = self.app
            modal = ParameterModal(cmd)
            await app.push_screen(modal)

        return execute_command
