"""Tests for API Client commands with service mocking.

Demonstrates how to test commands that depend on external services.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api_client.commands import get_posts, get_user, list_users, search_users
from api_client.credentials import mask_api_key
from api_client.entities import Post, User


class TestCredentialUtils:
    """Tests for credential management utilities."""

    def test_mask_api_key_none(self) -> None:
        """mask_api_key returns '(not set)' for None."""
        assert mask_api_key(None) == "(not set)"

    def test_mask_api_key_short(self) -> None:
        """mask_api_key masks short keys entirely."""
        assert mask_api_key("abc") == "***"
        assert mask_api_key("12345678") == "********"

    def test_mask_api_key_long(self) -> None:
        """mask_api_key shows first and last 4 chars."""
        result = mask_api_key("sk-abcdefghijklmnop")
        assert result == "sk-a...mnop"


class TestUserEntity:
    """Tests for User entity."""

    def test_from_api(self) -> None:
        """User.from_api creates user from API response."""
        data: dict[str, Any] = {
            "id": 1,
            "name": "John Doe",
            "username": "johnd",
            "email": "john@example.com",
            "phone": "555-1234",
            "website": "johndoe.com",
        }
        user = User.from_api(data)

        assert user.id == 1
        assert user.name == "John Doe"
        assert user.username == "johnd"
        assert user.email == "john@example.com"
        assert user.phone == "555-1234"
        assert user.website == "johndoe.com"

    def test_from_api_optional_fields(self) -> None:
        """User.from_api handles missing optional fields."""
        data: dict[str, Any] = {
            "id": 2,
            "name": "Jane Doe",
            "username": "janed",
            "email": "jane@example.com",
        }
        user = User.from_api(data)

        assert user.phone is None
        assert user.website is None


class TestPostEntity:
    """Tests for Post entity."""

    def test_from_api(self) -> None:
        """Post.from_api creates post from API response."""
        data: dict[str, Any] = {
            "id": 1,
            "userId": 5,
            "title": "Test Post",
            "body": "Post content here",
        }
        post = Post.from_api(data)

        assert post.id == 1
        assert post.user_id == 5
        assert post.title == "Test Post"
        assert post.body == "Post content here"


class TestUserCommands:
    """Tests for user commands with mocked service."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock API client."""
        client = MagicMock()
        client.get_user = AsyncMock()
        client.list_users = AsyncMock()
        client.search_users = AsyncMock()
        client.get_user_posts = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_get_user(self, mock_client: MagicMock) -> None:
        """get_user fetches user from API."""
        mock_client.get_user.return_value = {
            "id": 1,
            "name": "Leanne Graham",
            "username": "Bret",
            "email": "leanne@example.com",
        }

        with patch("api_client.commands.get_client", return_value=mock_client):
            user = await get_user(MagicMock(), user_id=1)

        assert user.id == 1
        assert user.name == "Leanne Graham"
        mock_client.get_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_users(self, mock_client: MagicMock) -> None:
        """list_users returns paginated users."""
        mock_client.list_users.return_value = [
            {"id": 1, "name": "User 1", "username": "u1", "email": "u1@test.com"},
            {"id": 2, "name": "User 2", "username": "u2", "email": "u2@test.com"},
        ]

        with patch("api_client.commands.get_client", return_value=mock_client):
            users = await list_users(MagicMock(), limit=10, offset=0)

        assert len(users) == 2
        assert users[0].name == "User 1"
        mock_client.list_users.assert_called_once_with(limit=10, offset=0)

    @pytest.mark.asyncio
    async def test_search_users(self, mock_client: MagicMock) -> None:
        """search_users filters by query."""
        mock_client.search_users.return_value = [
            {"id": 1, "name": "Leanne Graham", "username": "Bret", "email": "l@test.com"},
        ]

        with patch("api_client.commands.get_client", return_value=mock_client):
            users = await search_users(MagicMock(), query="leanne")

        assert len(users) == 1
        assert users[0].name == "Leanne Graham"
        mock_client.search_users.assert_called_once_with("leanne")

    @pytest.mark.asyncio
    async def test_get_posts(self, mock_client: MagicMock) -> None:
        """get_posts fetches user's posts."""
        mock_client.get_user_posts.return_value = [
            {"id": 1, "userId": 1, "title": "Post 1", "body": "Content 1"},
            {"id": 2, "userId": 1, "title": "Post 2", "body": "Content 2"},
        ]

        with patch("api_client.commands.get_client", return_value=mock_client):
            posts = await get_posts(MagicMock(), user_id=1)

        assert len(posts) == 2
        assert posts[0].title == "Post 1"
        mock_client.get_user_posts.assert_called_once_with(1)
