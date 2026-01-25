"""Credential management utilities for API Client example.

Provides secure storage and retrieval of API keys using the system keyring.
"""

from __future__ import annotations

SERVICE_NAME = "api-client-example"
KEY_NAME = "api_key"


def store_api_key(api_key: str) -> None:
    """Store API key in system keyring.

    Args:
        api_key: The API key to store.
    """
    import keyring

    keyring.set_password(SERVICE_NAME, KEY_NAME, api_key)


def get_api_key() -> str | None:
    """Retrieve API key from system keyring.

    Returns:
        The stored API key, or None if not set.
    """
    import keyring

    return keyring.get_password(SERVICE_NAME, KEY_NAME)


def delete_api_key() -> None:
    """Delete API key from system keyring."""
    import contextlib

    import keyring

    with contextlib.suppress(keyring.errors.PasswordDeleteError):
        keyring.delete_password(SERVICE_NAME, KEY_NAME)


def mask_api_key(api_key: str | None) -> str:
    """Mask an API key for display.

    Args:
        api_key: The API key to mask.

    Returns:
        Masked version showing only first and last 4 characters.
    """
    if api_key is None:
        return "(not set)"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"
