"""Contract tests for @service decorator.

Tests the service registration functionality including:
- Basic registration with factory function
- Credential specification parsing
- Cleanup function registration
- Registry integration
"""

from __future__ import annotations

import pytest

from hive.app import App
from hive.core.decorators import service
from hive.core.types import ServiceRegistration
from hive.errors import RegistrationError


class TestServiceDecoratorBasic:
    """Test basic @service decorator functionality."""

    def test_service_decorator_registers_service(self) -> None:
        """Service decorated with @service is registered in the app registry."""
        app = App("test-app")

        @service(app)
        def github_client(credentials: str) -> dict[str, str]:
            """GitHub API client."""
            return {"token": credentials}

        # Verify service is registered
        reg = app.registry.get_service("github_client")
        assert reg is not None
        assert reg.name == "github_client"
        assert reg.factory is github_client
        assert reg.docstring == "GitHub API client."

    def test_service_decorator_with_custom_name(self) -> None:
        """Service can be registered with a custom name."""
        app = App("test-app")

        @service(app, name="my_github")
        def github_client(credentials: str) -> dict[str, str]:
            return {"token": credentials}

        reg = app.registry.get_service("my_github")
        assert reg is not None
        assert reg.name == "my_github"

    def test_service_decorator_returns_function_unchanged(self) -> None:
        """Decorator returns the original function unchanged."""
        app = App("test-app")

        def original_factory(credentials: str) -> str:
            return f"client:{credentials}"

        decorated = service(app)(original_factory)
        assert decorated is original_factory


class TestServiceDecoratorCredentials:
    """Test credential specification in @service decorator."""

    def test_service_with_keyring_credentials(self) -> None:
        """Service with keyring credential specification."""
        app = App("test-app")

        @service(app, credentials="keyring:github_token")
        def github_client(credentials: str) -> dict[str, str]:
            return {"token": credentials}

        reg = app.registry.get_service("github_client")
        assert reg is not None
        assert reg.credential_key == "keyring:github_token"

    def test_service_with_env_credentials(self) -> None:
        """Service with environment variable credential specification."""
        app = App("test-app")

        @service(app, credentials="env:GITHUB_TOKEN")
        def github_client(credentials: str) -> dict[str, str]:
            return {"token": credentials}

        reg = app.registry.get_service("github_client")
        assert reg is not None
        assert reg.credential_key == "env:GITHUB_TOKEN"

    def test_service_without_credentials(self) -> None:
        """Service without credentials has None credential_key."""
        app = App("test-app")

        @service(app)
        def simple_service(credentials: str) -> dict[str, str]:
            return {}

        reg = app.registry.get_service("simple_service")
        assert reg is not None
        assert reg.credential_key is None


class TestServiceDecoratorCleanup:
    """Test cleanup function registration."""

    def test_service_with_cleanup_function(self) -> None:
        """Service with explicit cleanup function."""
        app = App("test-app")

        def close_client(client: dict[str, str]) -> None:
            client.clear()

        @service(app, cleanup=close_client)
        def http_client(credentials: str) -> dict[str, str]:
            return {"session": "active"}

        reg = app.registry.get_service("http_client")
        assert reg is not None
        assert reg.cleanup is close_client

    def test_service_without_cleanup(self) -> None:
        """Service without cleanup function."""
        app = App("test-app")

        @service(app)
        def simple_client(credentials: str) -> str:
            return credentials

        reg = app.registry.get_service("simple_client")
        assert reg is not None
        assert reg.cleanup is None


class TestServiceDecoratorErrors:
    """Test error handling in @service decorator."""

    def test_duplicate_service_name_raises_error(self) -> None:
        """Registering two services with same name raises RegistrationError."""
        app = App("test-app")

        @service(app)
        def my_service(credentials: str) -> str:
            return credentials

        with pytest.raises(RegistrationError, match="name already registered"):

            @service(app)
            def my_service(credentials: str) -> str:
                return credentials


class TestServiceRegistration:
    """Test ServiceRegistration dataclass properties."""

    def test_service_registration_is_immutable(self) -> None:
        """ServiceRegistration is frozen (immutable)."""

        def factory(creds: str) -> str:
            return creds

        reg = ServiceRegistration(
            name="test",
            factory=factory,
            credential_key="keyring:test",
        )

        with pytest.raises(AttributeError):
            reg.name = "changed"  # type: ignore[misc]

    def test_service_registration_defaults(self) -> None:
        """ServiceRegistration has sensible defaults."""

        def factory(creds: str) -> str:
            return creds

        reg = ServiceRegistration(
            name="minimal",
            factory=factory,
        )

        assert reg.credential_key is None
        assert reg.cleanup is None
        assert reg.docstring is None
