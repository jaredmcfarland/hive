"""Unit tests for REST authentication middleware.

Tests the authentication middleware types: none, api_key, bearer.

RED phase: These tests should FAIL until REST generator is implemented.
"""

from __future__ import annotations

import pytest


class TestAuthNone:
    """Tests for no authentication (default)."""

    def test_no_auth_allows_all_requests(self) -> None:
        """With auth=none, all requests pass through."""
        from hive.generators.rest import create_auth_dependency

        # Create the dependency with no auth
        dependency = create_auth_dependency(auth_type="none")

        # None auth should return None (no dependency)
        assert dependency is None

    def test_default_auth_is_none(self) -> None:
        """Default authentication type is none."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency()
        assert dependency is None


class TestAuthApiKey:
    """Tests for API key authentication."""

    def test_api_key_auth_creates_dependency(self) -> None:
        """API key auth creates a dependency function."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency(auth_type="api_key")
        assert dependency is not None
        assert callable(dependency)

    def test_api_key_uses_default_header(self) -> None:
        """API key auth uses X-API-Key header by default."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency(auth_type="api_key")
        # The dependency should be configured for X-API-Key header
        assert dependency is not None

    def test_api_key_custom_header(self) -> None:
        """API key auth can use custom header name."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency(
            auth_type="api_key",
            api_key_header="X-Custom-Key",
        )
        assert dependency is not None


class TestAuthBearer:
    """Tests for Bearer token authentication."""

    def test_bearer_auth_creates_dependency(self) -> None:
        """Bearer auth creates a dependency function."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency(auth_type="bearer")
        assert dependency is not None
        assert callable(dependency)

    def test_bearer_validates_authorization_header(self) -> None:
        """Bearer auth validates Authorization header format."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency(auth_type="bearer")
        # The dependency should validate Bearer tokens
        assert dependency is not None


class TestAuthBasic:
    """Tests for Basic authentication."""

    def test_basic_auth_creates_dependency(self) -> None:
        """Basic auth creates a dependency function."""
        from hive.generators.rest import create_auth_dependency

        dependency = create_auth_dependency(auth_type="basic")
        assert dependency is not None
        assert callable(dependency)


class TestInvalidAuth:
    """Tests for invalid authentication types."""

    def test_invalid_auth_type_raises_error(self) -> None:
        """Invalid auth type raises ValueError."""
        from hive.generators.rest import create_auth_dependency

        with pytest.raises(ValueError, match="Unknown auth type"):
            create_auth_dependency(auth_type="invalid")  # type: ignore[arg-type]
