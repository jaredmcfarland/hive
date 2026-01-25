"""Service definitions for API Client example.

Demonstrates the @service decorator pattern for external API integration.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from api_client.credentials import get_api_key


class JSONPlaceholderClient:
    """Client for JSONPlaceholder API.

    A demonstration service client that wraps the JSONPlaceholder
    fake REST API for testing and prototyping.

    Attributes:
        base_url: API base URL.
        timeout: Request timeout in seconds.
        api_key: Optional API key (not used by JSONPlaceholder but demonstrates pattern).
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: API base URL (defaults to JSONPlaceholder).
            timeout: Request timeout in seconds.
            api_key: Optional API key for authentication.
        """
        self.base_url = base_url or os.environ.get(
            "API_CLIENT_BASE_URL",
            "https://jsonplaceholder.typicode.com",
        )
        self.timeout = timeout
        self.api_key = api_key or get_api_key()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including auth if available.

        Returns:
            Dictionary of HTTP headers.
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_user(self, user_id: int) -> dict[str, Any]:
        """Fetch a user by ID.

        Args:
            user_id: User ID to fetch.

        Returns:
            User data dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/users/{user_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def list_users(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List users with pagination.

        Args:
            limit: Maximum number of users to return.
            offset: Number of users to skip.

        Returns:
            List of user data dictionaries.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/users",
                headers=self._get_headers(),
                params={"_limit": limit, "_start": offset},
            )
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result

    async def search_users(self, query: str) -> list[dict[str, Any]]:
        """Search users by name.

        Note: JSONPlaceholder doesn't support search, so this fetches
        all users and filters client-side for demonstration.

        Args:
            query: Search query string.

        Returns:
            List of matching user data dictionaries.
        """
        users = await self.list_users(limit=100)
        query_lower = query.lower()
        return [
            u
            for u in users
            if query_lower in u.get("name", "").lower()
            or query_lower in u.get("username", "").lower()
        ]

    async def get_user_posts(self, user_id: int) -> list[dict[str, Any]]:
        """Fetch posts by a user.

        Args:
            user_id: User ID to fetch posts for.

        Returns:
            List of post data dictionaries.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/users/{user_id}/posts",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            result: list[dict[str, Any]] = response.json()
            return result


# Global client instance (lazy initialization)
_client: JSONPlaceholderClient | None = None


def get_client() -> JSONPlaceholderClient:
    """Get or create the global API client instance.

    Returns:
        JSONPlaceholderClient instance.
    """
    global _client  # noqa: PLW0603
    if _client is None:
        _client = JSONPlaceholderClient()
    return _client
