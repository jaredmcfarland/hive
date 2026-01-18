"""Query binding execution for TUI screens.

Provides utilities for executing queries bound to screens and
managing query result caching.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Any

from hive.errors import ConfigurationError

if TYPE_CHECKING:
    from hive.core.registry import ApplicationRegistry
    from hive.core.types import QueryBinding


@dataclass
class CacheEntry:
    """Cached query result with expiration."""

    data: Any
    """The cached data."""

    expires_at: float
    """Timestamp when cache expires."""

    query_name: str
    """Name of the cached query."""


class QueryBindingExecutor:
    """Executes query bindings with caching support.

    Manages query execution and result caching based on
    query TTL settings.
    """

    def __init__(self, registry: ApplicationRegistry) -> None:
        """Initialize the executor.

        Args:
            registry: Application registry containing queries.
        """
        self._registry = registry
        self._cache: dict[str, CacheEntry] = {}

    async def execute(
        self,
        binding: QueryBinding,
        *,
        ctx: Any,
        force_refresh: bool = False,
    ) -> Any:
        """Execute a query binding.

        Args:
            binding: The query binding to execute.
            ctx: Execution context for the query.
            force_refresh: If True, bypass cache.

        Returns:
            Query result, possibly transformed.

        Raises:
            ConfigurationError: If query not found.
        """
        # Check cache first
        if not force_refresh:
            cached = self._get_cached(binding.query_name)
            if cached is not None:
                result = cached
                if binding.transform:
                    result = binding.transform(result)
                return result

        # Get query registration
        query_reg = self._registry.get_query(binding.query_name)
        if query_reg is None:
            raise ConfigurationError(f"Query '{binding.query_name}' not found in registry")

        # Execute query
        result = await query_reg.func(ctx)

        # Cache if TTL specified
        if query_reg.cache_ttl is not None:
            self._set_cached(
                binding.query_name,
                result,
                ttl=query_reg.cache_ttl,
            )

        # Apply transform
        if binding.transform:
            result = binding.transform(result)

        return result

    def _get_cached(self, query_name: str) -> Any | None:
        """Get cached result if valid.

        Args:
            query_name: The query name.

        Returns:
            Cached data or None if expired/missing.
        """
        entry = self._cache.get(query_name)
        if entry is None:
            return None

        if time.time() > entry.expires_at:
            del self._cache[query_name]
            return None

        return entry.data

    def _set_cached(self, query_name: str, data: Any, *, ttl: int) -> None:
        """Store result in cache.

        Args:
            query_name: The query name.
            data: Data to cache.
            ttl: Time-to-live in seconds.
        """
        self._cache[query_name] = CacheEntry(
            data=data,
            expires_at=time.time() + ttl,
            query_name=query_name,
        )

    def get_cache_info(self, binding: QueryBinding) -> dict[str, Any] | None:
        """Get cache information for a binding.

        Args:
            binding: The query binding.

        Returns:
            Cache info dict or None if query not found/not cached.
        """
        query_reg = self._registry.get_query(binding.query_name)
        if query_reg is None:
            return None

        if query_reg.cache_ttl is None:
            return None

        entry = self._cache.get(binding.query_name)
        return {
            "ttl": query_reg.cache_ttl,
            "cached": entry is not None,
            "expires_at": entry.expires_at if entry else None,
        }

    def invalidate(self, query_name: str) -> None:
        """Invalidate cache for a query.

        Args:
            query_name: The query to invalidate.
        """
        self._cache.pop(query_name, None)

    def invalidate_all(self) -> None:
        """Invalidate all cached queries."""
        self._cache.clear()


async def execute_query_binding(
    binding: QueryBinding,
    *,
    registry: ApplicationRegistry,
    ctx: Any,
    force_refresh: bool = False,
) -> Any:
    """Execute a single query binding.

    Convenience function for one-off query execution.

    Args:
        binding: The query binding to execute.
        registry: Application registry.
        ctx: Execution context.
        force_refresh: If True, bypass cache.

    Returns:
        Query result, possibly transformed.

    Raises:
        ConfigurationError: If query not found.
    """
    executor = QueryBindingExecutor(registry)
    return await executor.execute(binding, ctx=ctx, force_refresh=force_refresh)
