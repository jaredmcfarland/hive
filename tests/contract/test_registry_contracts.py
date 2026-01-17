"""Test ApplicationRegistry contracts enforced by deal."""

import pytest


class TestRegistryContracts:
    """Tests for ApplicationRegistry deal contracts."""

    def test_cannot_register_empty_name(self) -> None:
        """Registering command with empty name raises error."""
        from hive.core.registry import ApplicationRegistry
        from hive.core.types import CommandRegistration

        registry = ApplicationRegistry()

        reg = CommandRegistration(
            name="",  # Empty name
            func=lambda ctx: None,
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        with pytest.raises(Exception):  # deal.PreContractError
            registry.register_command(reg)

    def test_cannot_register_none_func(self) -> None:
        """Registering command with None func raises error."""
        from hive.core.registry import ApplicationRegistry
        from hive.core.types import CommandRegistration

        registry = ApplicationRegistry()

        reg = CommandRegistration(
            name="test",
            func=None,  # type: ignore  # None func
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        with pytest.raises(Exception):  # deal.PreContractError
            registry.register_command(reg)

    def test_cannot_register_duplicate_name(self) -> None:
        """Registering command with duplicate name raises error."""
        from hive.core.registry import ApplicationRegistry
        from hive.core.types import CommandRegistration

        registry = ApplicationRegistry()

        async def cmd1(ctx):
            pass

        async def cmd2(ctx):
            pass

        reg1 = CommandRegistration(
            name="duplicate",
            func=cmd1,
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        reg2 = CommandRegistration(
            name="duplicate",
            func=cmd2,
            parameters=[],
            return_type=None,
            docstring=None,
            entities=[],
            aliases=[],
            hidden=False,
        )

        registry.register_command(reg1)

        with pytest.raises(Exception):  # RegistrationError or deal.PreContractError
            registry.register_command(reg2)
