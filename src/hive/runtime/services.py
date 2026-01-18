"""Service layer for external API clients with credential management.

This module provides lazy service instantiation and credential resolution
via keyring with environment variable fallback.

Public API:
    ServiceProxy: Lazy accessor for registered services
    resolve_credentials: Credential resolution chain
    parse_credential_spec: Parse credential specification string
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, Literal, cast

import keyring

from hive.core.types import CredentialSpec
from hive.errors import CredentialError

if TYPE_CHECKING:
    from hive.core.registry import ApplicationRegistry

__all__ = ["ServiceProxy", "parse_credential_spec", "resolve_credentials"]

logger = logging.getLogger(__name__)


def parse_credential_spec(spec: str) -> CredentialSpec:
    """Parse a credential specification string.

    Args:
        spec: Credential specification in format "source:key".
            Supported sources: "keyring", "env".

    Returns:
        Parsed CredentialSpec with source, key, and default settings.

    Raises:
        ValueError: If spec format is invalid or source is unknown.

    Example:
        >>> parse_credential_spec("keyring:github_token")
        CredentialSpec(source='keyring', key='github_token', ...)
    """
    if ":" not in spec:
        msg = f"Invalid credential specification '{spec}': expected 'source:key' format"
        raise ValueError(msg)

    source, key = spec.split(":", 1)

    if source not in ("keyring", "env"):
        msg = f"Unknown credential source '{source}': must be 'keyring' or 'env'"
        raise ValueError(msg)

    # source is validated to be "keyring" or "env" above, cast for Literal type
    typed_source = cast("Literal['keyring', 'env', 'prompt']", source)
    return CredentialSpec(
        source=typed_source,
        key=key,
        required=True,
        mask_in_logs=True,
    )


def _get_fallback_env_var(service_name: str) -> str:
    """Generate fallback environment variable name for a service.

    Args:
        service_name: Name of the service.

    Returns:
        Environment variable name in format HIVE_{SERVICE}_CREDENTIAL.
    """
    # Convert to uppercase and replace non-alphanumeric with underscore
    safe_name = "".join(c if c.isalnum() else "_" for c in service_name.upper())
    return f"HIVE_{safe_name}_CREDENTIAL"


def _resolve_from_keyring(key: str, service_name: str) -> str | None:
    """Attempt to resolve credentials from system keyring.

    Args:
        key: The keyring service key.
        service_name: Service name for keyring namespace.

    Returns:
        Credential value if found, None otherwise.
    """
    try:
        # Use hive.{key} as the service name in keyring
        keyring_service = f"hive.{key}"
        return keyring.get_password(keyring_service, "credentials")
    except (OSError, RuntimeError):
        # Keyring may fail (locked, unavailable, etc.)
        # Log at debug level - this is expected in CI/headless environments
        logger.debug(
            "Keyring lookup failed for service '%s', will try fallback",
            service_name,
            exc_info=True,
        )
        return None


def _resolve_from_env(var_name: str) -> str | None:
    """Attempt to resolve credentials from environment variable.

    Args:
        var_name: Environment variable name.

    Returns:
        Value if set, None otherwise.
    """
    return os.environ.get(var_name)


def resolve_credentials(
    credential_key: str | None,
    *,
    service_name: str,
) -> str:
    """Resolve credentials for a service.

    Resolution order:
    1. If credential_key is None, return empty string (no credentials needed)
    2. If credential_key starts with "env:", look up environment variable
    3. If credential_key starts with "keyring:", try keyring first
    4. Fall back to environment variable HIVE_{SERVICE}_CREDENTIAL

    Args:
        credential_key: Credential specification or None.
        service_name: Name of the service (for fallback env var and errors).

    Returns:
        Resolved credential string.

    Raises:
        CredentialError: If required credentials cannot be found.

    Security:
        Credential values are NEVER logged or included in error messages.
    """
    if credential_key is None:
        return ""

    spec = parse_credential_spec(credential_key)
    fallback_var = _get_fallback_env_var(service_name)

    if spec.source == "env":
        # Direct environment variable lookup
        value = _resolve_from_env(spec.key)
        if value is not None:
            return value
        # Try fallback
        value = _resolve_from_env(fallback_var)
        if value is not None:
            return value
        msg = f"Credential not found for service '{service_name}': environment variable '{spec.key}' not set"
        raise CredentialError(msg)

    if spec.source == "keyring":
        # Try keyring first
        value = _resolve_from_keyring(spec.key, service_name)
        if value is not None:
            return value

        # Fall back to environment variable
        value = _resolve_from_env(fallback_var)
        if value is not None:
            return value

        msg = f"Credential not found for service '{service_name}': not in keyring and '{fallback_var}' not set"
        raise CredentialError(msg)

    # Should not reach here due to parse_credential_spec validation
    msg = f"Credential not found for service '{service_name}'"
    raise CredentialError(msg)


class ServiceProxy:
    """Lazy accessor for registered services.

    Provides attribute-based access to services with lazy instantiation
    and per-proxy caching.

    Example:
        proxy = ServiceProxy(registry)
        client = proxy.github_client  # Instantiates on first access
        client2 = proxy.github_client  # Returns cached instance
    """

    def __init__(self, registry: ApplicationRegistry) -> None:
        """Initialize the service proxy.

        Args:
            registry: Application registry containing service registrations.
        """
        self._registry = registry
        self._cache: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Get a service instance by name.

        Args:
            name: Service name.

        Returns:
            Instantiated service (cached after first access).

        Raises:
            AttributeError: If no service with given name is registered.
            CredentialError: If credentials cannot be resolved.
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Look up registration
        registration = self._registry.get_service(name)
        if registration is None:
            msg = f"No service registered with name '{name}'"
            raise AttributeError(msg)

        # Resolve credentials
        credentials = resolve_credentials(
            registration.credential_key,
            service_name=name,
        )

        # Instantiate service
        instance = registration.factory(credentials)

        # Cache for reuse
        self._cache[name] = instance

        return instance

    def __dir__(self) -> list[str]:  # type: ignore[override]
        """List available service names.

        Returns:
            List of registered service names.
        """
        return list(self._registry.services.keys())

    def cleanup_services(self) -> None:
        """Clean up all instantiated services synchronously.

        Calls cleanup function for each cached service that has one.
        Errors in cleanup functions are logged but do not prevent
        other cleanups from running.

        Note:
            For services with async cleanup functions, use
            ``cleanup_services_async()`` instead to ensure cleanup
            completes. This method cannot guarantee async cleanup
            completion when called from within a running event loop.
        """
        for name, instance in list(self._cache.items()):
            registration = self._registry.get_service(name)
            if registration is None or registration.cleanup is None:
                continue

            try:
                result = registration.cleanup(instance)
                # Handle async cleanup functions synchronously
                if asyncio.iscoroutine(result):
                    # Create event loop if needed (for sync context)
                    try:
                        asyncio.get_running_loop()
                        # Already in async context - cannot await here
                        # Log warning and cancel the coroutine to avoid warning
                        logger.warning(
                            (
                                "Service '%s' has async cleanup but cleanup_services() "
                                "was called from async context. Use "
                                "cleanup_services_async() for guaranteed completion."
                            ),
                            name,
                        )
                        result.close()  # Prevent "coroutine never awaited" warning
                    except RuntimeError:
                        # No running loop - run synchronously
                        asyncio.run(result)
            except (OSError, RuntimeError, TypeError, ValueError):
                # Catch common cleanup errors without broad Exception
                logger.warning(
                    "Error during cleanup of service '%s'",
                    name,
                    exc_info=True,
                )

        self._cache.clear()

    async def cleanup_services_async(self) -> None:
        """Clean up all instantiated services asynchronously.

        Awaits async cleanup functions properly.
        """
        for name, instance in list(self._cache.items()):
            registration = self._registry.get_service(name)
            if registration is None or registration.cleanup is None:
                continue

            try:
                result = registration.cleanup(instance)
                if result is not None and asyncio.iscoroutine(result):
                    await result
            except (OSError, RuntimeError, TypeError, ValueError):
                # Catch common cleanup errors without broad Exception
                logger.warning(
                    "Error during cleanup of service '%s'",
                    name,
                    exc_info=True,
                )

        self._cache.clear()
