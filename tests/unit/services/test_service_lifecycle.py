"""Unit tests for service lifecycle management.

Tests:
- Lazy instantiation of services
- Service caching (singleton per context)
- Cleanup on context exit
- ServiceProxy behavior
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from hive.app import App
from hive.core.decorators import service
from hive.errors import CredentialError


class TestServiceProxy:
    """Test ServiceProxy lazy access behavior."""

    def test_service_proxy_getattr_returns_service(self) -> None:
        """Accessing service via attribute returns instantiated service."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")

        @service(app)
        def my_api(credentials: str) -> dict[str, str]:
            return {"client": "initialized", "creds": credentials}

        proxy = ServiceProxy(app.registry)

        with patch("hive.runtime.services.resolve_credentials", return_value="test_cred"):
            client = proxy.my_api

        assert client["client"] == "initialized"
        assert client["creds"] == "test_cred"

    def test_service_proxy_unknown_service_raises_attribute_error(self) -> None:
        """Accessing unregistered service raises AttributeError."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        proxy = ServiceProxy(app.registry)

        with pytest.raises(AttributeError, match="No service registered with name"):
            _ = proxy.unknown_service

    def test_service_proxy_dir_lists_services(self) -> None:
        """dir(proxy) lists registered service names."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")

        @service(app)
        def api_one(credentials: str) -> str:
            return credentials

        @service(app)
        def api_two(credentials: str) -> str:
            return credentials

        proxy = ServiceProxy(app.registry)

        service_names = dir(proxy)
        assert "api_one" in service_names
        assert "api_two" in service_names


class TestServiceCaching:
    """Test service instance caching within a context."""

    def test_service_cached_after_first_access(self) -> None:
        """Second access returns same instance (no re-instantiation)."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        call_count = 0

        @service(app)
        def cached_service(credentials: str) -> dict[str, int]:
            nonlocal call_count
            call_count += 1
            return {"call": call_count}

        proxy = ServiceProxy(app.registry)

        with patch("hive.runtime.services.resolve_credentials", return_value="cred"):
            first = proxy.cached_service
            second = proxy.cached_service

        assert first is second  # Same instance
        assert call_count == 1  # Factory called only once

    def test_new_proxy_gets_fresh_instance(self) -> None:
        """Different ServiceProxy instances have independent caches."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        call_count = 0

        @service(app)
        def fresh_service(credentials: str) -> dict[str, int]:
            nonlocal call_count
            call_count += 1
            return {"call": call_count}

        proxy1 = ServiceProxy(app.registry)
        proxy2 = ServiceProxy(app.registry)

        with patch("hive.runtime.services.resolve_credentials", return_value="cred"):
            instance1 = proxy1.fresh_service
            instance2 = proxy2.fresh_service

        assert instance1 is not instance2
        assert call_count == 2


class TestServiceCleanup:
    """Test service cleanup on context exit."""

    def test_cleanup_called_on_context_exit(self) -> None:
        """Cleanup function called when cleanup_services is invoked."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        cleanup_called = []

        def cleanup_fn(client: dict[str, str]) -> None:
            cleanup_called.append(client)

        @service(app, cleanup=cleanup_fn)
        def cleanable_service(credentials: str) -> dict[str, str]:
            return {"status": "active"}

        proxy = ServiceProxy(app.registry)

        with patch("hive.runtime.services.resolve_credentials", return_value="cred"):
            client = proxy.cleanable_service

        # Cleanup services
        proxy.cleanup_services()

        assert len(cleanup_called) == 1
        assert cleanup_called[0] is client

    def test_cleanup_not_called_for_unused_services(self) -> None:
        """Cleanup only called for services that were actually instantiated."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        cleanup_called = []

        def cleanup_fn(client: dict[str, str]) -> None:
            cleanup_called.append(client)

        @service(app, cleanup=cleanup_fn)
        def unused_service(credentials: str) -> dict[str, str]:
            return {"status": "active"}

        proxy = ServiceProxy(app.registry)

        # Don't access the service, just cleanup
        proxy.cleanup_services()

        assert len(cleanup_called) == 0

    def test_cleanup_handles_errors_gracefully(self) -> None:
        """Cleanup errors don't prevent other cleanups from running."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        cleanup_order = []

        def failing_cleanup(client: str) -> None:
            cleanup_order.append("failing")
            raise RuntimeError("Cleanup failed")

        def success_cleanup(client: str) -> None:
            cleanup_order.append("success")

        @service(app, name="service_a", cleanup=failing_cleanup)
        def service_a(credentials: str) -> str:
            return "a"

        @service(app, name="service_b", cleanup=success_cleanup)
        def service_b(credentials: str) -> str:
            return "b"

        proxy = ServiceProxy(app.registry)

        with patch("hive.runtime.services.resolve_credentials", return_value="cred"):
            _ = proxy.service_a
            _ = proxy.service_b

        # Should not raise, but log errors
        proxy.cleanup_services()

        # Both cleanups should have been attempted
        assert "failing" in cleanup_order
        assert "success" in cleanup_order

    @pytest.mark.asyncio
    async def test_async_cleanup_supported(self) -> None:
        """Async cleanup functions are properly awaited."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")
        cleanup_called = False

        async def async_cleanup(client: str) -> None:
            nonlocal cleanup_called
            cleanup_called = True

        @service(app, cleanup=async_cleanup)
        def async_cleanable(credentials: str) -> str:
            return "client"

        proxy = ServiceProxy(app.registry)

        with patch("hive.runtime.services.resolve_credentials", return_value="cred"):
            _ = proxy.async_cleanable

        await proxy.cleanup_services_async()

        assert cleanup_called is True


class TestServiceWithContext:
    """Test service integration with ExecutionContext."""

    @pytest.mark.asyncio
    async def test_context_provides_services_proxy(self) -> None:
        """ExecutionContext.services returns a ServiceProxy."""
        from hive.runtime.context import ExecutionContext
        from hive.runtime.services import ServiceProxy

        app = App("test-app")

        @service(app)
        def test_service(credentials: str) -> str:
            return credentials

        async with ExecutionContext(registry=app.registry) as ctx:
            assert hasattr(ctx, "services")
            assert isinstance(ctx.services, ServiceProxy)

    @pytest.mark.asyncio
    async def test_services_cleaned_up_on_context_exit(self) -> None:
        """Services are cleaned up when context exits."""
        from hive.runtime.context import ExecutionContext

        app = App("test-app")
        cleanup_called = False

        def cleanup(client: str) -> None:
            nonlocal cleanup_called
            cleanup_called = True

        @service(app, cleanup=cleanup)
        def ctx_service(credentials: str) -> str:
            return "client"

        with patch("hive.runtime.services.resolve_credentials", return_value="cred"):
            async with ExecutionContext(registry=app.registry) as ctx:
                _ = ctx.services.ctx_service

        assert cleanup_called is True


class TestServiceInstantiationErrors:
    """Test error handling during service instantiation."""

    def test_factory_error_propagates(self) -> None:
        """Errors in factory function propagate to caller."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")

        @service(app)
        def failing_service(credentials: str) -> str:
            raise RuntimeError("Factory failed")

        proxy = ServiceProxy(app.registry)

        with (
            patch("hive.runtime.services.resolve_credentials", return_value="cred"),
            pytest.raises(RuntimeError, match="Factory failed"),
        ):
            _ = proxy.failing_service

    def test_credential_error_propagates(self) -> None:
        """CredentialError from resolution propagates to caller."""
        from hive.runtime.services import ServiceProxy

        app = App("test-app")

        @service(app, credentials="keyring:missing")
        def cred_service(credentials: str) -> str:
            return credentials

        proxy = ServiceProxy(app.registry)

        with (
            patch(
                "hive.runtime.services.resolve_credentials",
                side_effect=CredentialError("Credential not found for service 'cred_service'"),
            ),
            pytest.raises(CredentialError),
        ):
            _ = proxy.cred_service
