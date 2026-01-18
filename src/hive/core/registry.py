"""Application registry for storing decorated items.

The registry is the central store for all decorated functions and classes.
Generators read from the registry to produce CLI, TUI, and other artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping

import deal

from hive.core.types import (
    CommandRegistration,
    EntityRegistration,
    QueryRegistration,
    ScreenRegistration,
)
from hive.errors import RegistrationError


class ApplicationRegistry:
    """Central registry for all decorated application components.

    This class stores registrations for commands, queries, entities,
    and screens. It enforces uniqueness constraints and provides
    query methods for generators.
    """

    def __init__(self) -> None:
        self._commands: dict[str, CommandRegistration] = {}
        self._queries: dict[str, QueryRegistration] = {}
        self._entities: dict[str, EntityRegistration] = {}
        self._screens: dict[str, ScreenRegistration] = {}
        self._all_names: set[str] = set()  # Track all registered names

    @property
    def commands(self) -> Mapping[str, CommandRegistration]:
        """Read-only mapping of command names to registrations."""
        return self._commands

    @property
    def queries(self) -> Mapping[str, QueryRegistration]:
        """Read-only mapping of query names to registrations."""
        return self._queries

    @property
    def entities(self) -> Mapping[str, EntityRegistration]:
        """Read-only mapping of entity names to registrations."""
        return self._entities

    @property
    def screens(self) -> Mapping[str, ScreenRegistration]:
        """Read-only mapping of screen names to registrations."""
        return self._screens

    def _check_name_collision(self, name: str, kind: str) -> None:
        """Check if a name is already registered.

        Args:
            name: The name to check.
            kind: The kind of registration (for error message).

        Raises:
            RegistrationError: If name is already registered.
        """
        if name in self._all_names:
            raise RegistrationError(f"Cannot register {kind} '{name}': name already registered")

    @deal.pre(
        lambda _self, registration: registration.name and len(registration.name) > 0,
        message="Command name required",
    )
    @deal.pre(
        lambda _self, registration: registration.func is not None,
        message="Command function required",
    )
    def register_command(self, registration: CommandRegistration) -> None:
        """Register a command.

        Args:
            registration: The command registration.

        Raises:
            RegistrationError: If command name or any alias is already registered.
        """
        # Check main name
        self._check_name_collision(registration.name, "command")

        # Check aliases
        for alias in registration.aliases:
            self._check_name_collision(alias, f"alias '{alias}' for command")

        # Register
        self._commands[registration.name] = registration
        self._all_names.add(registration.name)
        for alias in registration.aliases:
            self._all_names.add(alias)

    def register_query(self, registration: QueryRegistration) -> None:
        """Register a query.

        Args:
            registration: The query registration.

        Raises:
            RegistrationError: If query name is already registered.
        """
        self._check_name_collision(registration.name, "query")
        self._queries[registration.name] = registration
        self._all_names.add(registration.name)

    def register_entity(self, registration: EntityRegistration) -> None:
        """Register an entity.

        Args:
            registration: The entity registration.

        Raises:
            RegistrationError: If entity name is already registered.
        """
        if registration.name in self._entities:
            raise RegistrationError(
                f"Cannot register entity '{registration.name}': name already registered"
            )
        self._entities[registration.name] = registration

    def register_screen(self, registration: ScreenRegistration) -> None:
        """Register a screen.

        Args:
            registration: The screen registration.

        Raises:
            RegistrationError: If screen name, default flag, or keybinding conflicts.
        """
        if registration.name in self._screens:
            raise RegistrationError(
                f"Cannot register screen '{registration.name}': name already registered"
            )

        # Check for duplicate default
        if registration.default:
            for existing in self._screens.values():
                if existing.default:
                    msg = (
                        f"Cannot register screen '{registration.name}' as default: "
                        f"'{existing.name}' is already the default screen"
                    )
                    raise RegistrationError(msg)

        # Check for duplicate keybinding
        if registration.keybinding:
            for existing in self._screens.values():
                if existing.keybinding == registration.keybinding:
                    msg = (
                        f"Cannot register screen '{registration.name}' with keybinding "
                        f"'{registration.keybinding}': already used by '{existing.name}'"
                    )
                    raise RegistrationError(msg)

        self._screens[registration.name] = registration

    def get_command(self, name: str) -> CommandRegistration | None:
        """Get a command registration by name.

        Args:
            name: The command name.

        Returns:
            The registration if found, None otherwise.
        """
        return self._commands.get(name)

    def list_commands(self) -> list[CommandRegistration]:
        """Get all registered commands.

        Returns:
            List of all command registrations.
        """
        return list(self._commands.values())

    def get_query(self, name: str) -> QueryRegistration | None:
        """Get a query registration by name.

        Args:
            name: The query name.

        Returns:
            The registration if found, None otherwise.
        """
        return self._queries.get(name)

    def list_queries(self) -> list[QueryRegistration]:
        """Get all registered queries.

        Returns:
            List of all query registrations.
        """
        return list(self._queries.values())

    def get_entity(self, name: str) -> EntityRegistration | None:
        """Get an entity registration by name.

        Args:
            name: The entity name.

        Returns:
            The registration if found, None otherwise.
        """
        return self._entities.get(name)

    def list_entities(self) -> list[EntityRegistration]:
        """Get all registered entities.

        Returns:
            List of all entity registrations.
        """
        return list(self._entities.values())

    def get_screen(self, name: str) -> ScreenRegistration | None:
        """Get a screen registration by name.

        Args:
            name: The screen name.

        Returns:
            The registration if found, None otherwise.
        """
        return self._screens.get(name)

    def list_screens(self) -> list[ScreenRegistration]:
        """Get all registered screens.

        Returns:
            List of all screen registrations.
        """
        return list(self._screens.values())
