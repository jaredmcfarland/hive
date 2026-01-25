"""Commands for API Client example.

Demonstrates commands that use external services for data fetching.
"""

from __future__ import annotations

from hive.contracts import requires
from hive.core.decorators import command
from hive.runtime.context import ExecutionContext

from api_client.app import app
from api_client.credentials import (
    delete_api_key,
    get_api_key,
    mask_api_key,
    store_api_key,
)
from api_client.entities import Post, User
from api_client.services import get_client

# --- Configuration Commands ---


@command(app)
async def set_key(ctx: ExecutionContext, api_key: str) -> str:  # noqa: ARG001
    """Store API key in system keyring.

    Args:
        ctx: Execution context.
        api_key: The API key to store securely.

    Returns:
        Success message.

    Example:
        $ api-client set-key sk-abc123xyz
        API key stored successfully
    """
    store_api_key(api_key)
    return "API key stored successfully"


@command(app)
async def show_key(ctx: ExecutionContext) -> str:  # noqa: ARG001
    """Display stored API key (masked).

    Args:
        ctx: Execution context.

    Returns:
        Masked API key string.

    Example:
        $ api-client show-key
        sk-a...xyz
    """
    api_key = get_api_key()
    return f"API key: {mask_api_key(api_key)}"


@command(app)
async def clear_key(ctx: ExecutionContext) -> str:  # noqa: ARG001
    """Remove stored API key from keyring.

    Args:
        ctx: Execution context.

    Returns:
        Success message.

    Example:
        $ api-client clear-key
        API key removed
    """
    delete_api_key()
    return "API key removed"


# --- User Commands ---


@command(app)
@requires(lambda _ctx, user_id, **_kw: user_id > 0, "User ID must be positive")
async def get_user(ctx: ExecutionContext, user_id: int) -> User:  # noqa: ARG001
    """Fetch a user by ID from the API.

    Args:
        ctx: Execution context.
        user_id: ID of the user to fetch.

    Returns:
        User entity with fetched data.

    Example:
        $ api-client get-user 1
        User(id=1, name='Leanne Graham', ...)
    """
    client = get_client()
    data = await client.get_user(user_id)
    return User.from_api(data)


@command(app)
@requires(lambda _ctx, limit=10, **_kw: limit > 0, "Limit must be positive")
@requires(lambda _ctx, _limit, offset=0, **_kw: offset >= 0, "Offset must be non-negative")
async def list_users(
    ctx: ExecutionContext,  # noqa: ARG001
    limit: int = 10,
    offset: int = 0,
) -> list[User]:
    """List users with pagination.

    Args:
        ctx: Execution context.
        limit: Maximum number of users to return.
        offset: Number of users to skip.

    Returns:
        List of User entities.

    Example:
        $ api-client list-users --limit 5
        [User(id=1, ...), User(id=2, ...), ...]
    """
    client = get_client()
    data = await client.list_users(limit=limit, offset=offset)
    return [User.from_api(u) for u in data]


@command(app)
@requires(lambda _ctx, query, **_kw: len(query.strip()) > 0, "Query cannot be empty")
async def search_users(ctx: ExecutionContext, query: str) -> list[User]:  # noqa: ARG001
    """Search users by name or username.

    Args:
        ctx: Execution context.
        query: Search string to match against name/username.

    Returns:
        List of matching User entities.

    Example:
        $ api-client search-users "leanne"
        [User(id=1, name='Leanne Graham', ...)]
    """
    client = get_client()
    data = await client.search_users(query)
    return [User.from_api(u) for u in data]


# --- Post Commands ---


@command(app)
@requires(lambda _ctx, user_id, **_kw: user_id > 0, "User ID must be positive")
async def get_posts(ctx: ExecutionContext, user_id: int) -> list[Post]:  # noqa: ARG001
    """Fetch posts by a user.

    Args:
        ctx: Execution context.
        user_id: ID of the user whose posts to fetch.

    Returns:
        List of Post entities.

    Example:
        $ api-client get-posts 1
        [Post(id=1, title='...', ...), ...]
    """
    client = get_client()
    data = await client.get_user_posts(user_id)
    return [Post.from_api(p) for p in data]
