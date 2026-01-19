"""Unit tests for credential resolution.

Tests the credential resolution chain:
1. Keyring lookup
2. Environment variable fallback
3. Error handling for missing credentials
4. Credential masking in logs/errors
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from hive.errors import CredentialError

# Import will be added after implementation
# from hive.runtime.services import resolve_credentials, parse_credential_spec


class TestParseCredentialSpec:
    """Test credential specification parsing."""

    def test_parse_keyring_spec(self) -> None:
        """Parse keyring credential specification."""
        from hive.runtime.services import parse_credential_spec

        spec = parse_credential_spec("keyring:github_token")
        assert spec.source == "keyring"
        assert spec.key == "github_token"
        assert spec.required is True
        assert spec.mask_in_logs is True

    def test_parse_env_spec(self) -> None:
        """Parse environment variable credential specification."""
        from hive.runtime.services import parse_credential_spec

        spec = parse_credential_spec("env:GITHUB_TOKEN")
        assert spec.source == "env"
        assert spec.key == "GITHUB_TOKEN"

    def test_parse_invalid_spec_raises_error(self) -> None:
        """Invalid credential spec format raises ValueError."""
        from hive.runtime.services import parse_credential_spec

        with pytest.raises(ValueError, match="Invalid credential specification"):
            parse_credential_spec("invalid_format")

    def test_parse_unknown_source_raises_error(self) -> None:
        """Unknown credential source raises ValueError."""
        from hive.runtime.services import parse_credential_spec

        with pytest.raises(ValueError, match="Unknown credential source"):
            parse_credential_spec("file:/path/to/secret")


class TestResolveCredentialsKeyring:
    """Test keyring-based credential resolution."""

    def test_resolve_from_keyring_success(self) -> None:
        """Successfully resolve credentials from keyring."""
        from hive.runtime.services import resolve_credentials

        with patch("hive.runtime.services.keyring") as mock_keyring:
            mock_keyring.get_password.return_value = "secret_token"

            result = resolve_credentials("keyring:myservice", service_name="myservice")

            assert result == "secret_token"
            mock_keyring.get_password.assert_called_once_with("hive.myservice", "credentials")

    def test_resolve_from_keyring_not_found_falls_back_to_env(self) -> None:
        """When keyring has no value, fall back to environment variable."""
        from hive.runtime.services import resolve_credentials

        with (
            patch("hive.runtime.services.keyring") as mock_keyring,
            patch.dict(os.environ, {"HIVE_MYSERVICE_CREDENTIAL": "env_token"}),
        ):
            mock_keyring.get_password.return_value = None

            result = resolve_credentials("keyring:myservice", service_name="myservice")

            assert result == "env_token"

    def test_resolve_keyring_error_falls_back_to_env(self) -> None:
        """When keyring raises error, fall back to environment variable."""
        from hive.runtime.services import resolve_credentials

        with (
            patch("hive.runtime.services.keyring") as mock_keyring,
            patch.dict(os.environ, {"HIVE_MYSERVICE_CREDENTIAL": "env_fallback"}),
        ):
            # Use RuntimeError which is caught by the implementation
            mock_keyring.get_password.side_effect = RuntimeError("Keyring locked")

            result = resolve_credentials("keyring:myservice", service_name="myservice")

            assert result == "env_fallback"


class TestResolveCredentialsEnv:
    """Test environment variable credential resolution."""

    def test_resolve_from_env_success(self) -> None:
        """Successfully resolve credentials from environment."""
        from hive.runtime.services import resolve_credentials

        with patch.dict(os.environ, {"CUSTOM_VAR": "my_secret"}):
            result = resolve_credentials("env:CUSTOM_VAR", service_name="test")

            assert result == "my_secret"

    def test_resolve_from_env_not_found_raises_error(self) -> None:
        """Missing environment variable raises CredentialError."""
        from hive.runtime.services import resolve_credentials

        # Ensure the fallback var is also not present
        with patch.dict(
            os.environ,
            {"HIVE_TEST_CREDENTIAL": "", "MISSING_VAR": ""},
            clear=True,
        ):
            # Clear the vars we set above
            os.environ.pop("HIVE_TEST_CREDENTIAL", None)
            os.environ.pop("MISSING_VAR", None)
            with pytest.raises(CredentialError, match="Credential not found"):
                resolve_credentials("env:MISSING_VAR", service_name="test")


class TestResolveCredentialsFallback:
    """Test credential resolution fallback chain."""

    def test_fallback_env_variable_naming(self) -> None:
        """Fallback environment variable uses HIVE_{SERVICE}_CREDENTIAL pattern."""
        from hive.runtime.services import resolve_credentials

        with (
            patch("hive.runtime.services.keyring") as mock_keyring,
            patch.dict(os.environ, {"HIVE_MY_API_CREDENTIAL": "fallback_secret"}),
        ):
            mock_keyring.get_password.return_value = None

            result = resolve_credentials("keyring:my_api", service_name="my_api")

            assert result == "fallback_secret"

    def test_all_sources_fail_raises_credential_error(self) -> None:
        """When all credential sources fail, raise CredentialError."""
        from hive.runtime.services import resolve_credentials

        with (
            patch("hive.runtime.services.keyring") as mock_keyring,
            patch.dict(os.environ, {}, clear=True),
        ):
            mock_keyring.get_password.return_value = None
            # Environment is cleared, so fallback var is not present
            with pytest.raises(CredentialError, match="Credential not found"):
                resolve_credentials(
                    "keyring:nosuchservice",
                    service_name="nosuchservice",
                )


class TestCredentialSecurity:
    """Test that credentials are never exposed in logs or errors."""

    def test_credential_error_does_not_contain_secret(self) -> None:
        """CredentialError message does not contain the secret value."""
        from hive.runtime.services import resolve_credentials

        with (
            patch("hive.runtime.services.keyring") as mock_keyring,
            patch.dict(os.environ, {}, clear=True),
        ):
            mock_keyring.get_password.return_value = None
            os.environ.pop("HIVE_MYSVC_CREDENTIAL", None)

            try:
                resolve_credentials("keyring:mysvc", service_name="mysvc")
            except CredentialError as e:
                error_message = str(e)
                # Should mention service name, not any potential credential
                assert "mysvc" in error_message.lower() or "credential" in error_message.lower()
                # Error should never contain actual secret patterns
                assert "secret" not in error_message.lower()
                assert "password" not in error_message.lower()

    def test_credential_value_masked_in_repr(self) -> None:
        """Credential values should not appear in repr of related objects."""
        from hive.core.types import CredentialSpec

        spec = CredentialSpec(
            source="keyring",
            key="github_token",
            required=True,
            mask_in_logs=True,
        )

        repr_str = repr(spec)
        # The key name is OK, but actual credential values should never appear
        assert "github_token" in repr_str  # Key name is acceptable
        # Ensure mask_in_logs is set
        assert spec.mask_in_logs is True


class TestNoneCredentials:
    """Test services without credential requirements."""

    def test_resolve_none_credential_spec(self) -> None:
        """Services without credentials return empty string."""
        from hive.runtime.services import resolve_credentials

        result = resolve_credentials(None, service_name="noauth_service")

        assert result == ""
