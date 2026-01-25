"""Data entities for API Client example.

Defines the data models returned by the JSONPlaceholder API.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    """A user from the JSONPlaceholder API.

    Attributes:
        id: Unique user identifier.
        name: Full name of the user.
        username: Username handle.
        email: Email address.
        phone: Phone number (optional).
        website: Website URL (optional).
    """

    id: int
    name: str
    username: str
    email: str
    phone: str | None = None
    website: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> User:
        """Create a User from API response data.

        Args:
            data: Dictionary from API response.

        Returns:
            User instance.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            username=data["username"],
            email=data["email"],
            phone=data.get("phone"),
            website=data.get("website"),
        )


@dataclass
class Post:
    """A post from the JSONPlaceholder API.

    Attributes:
        id: Unique post identifier.
        user_id: ID of the user who created the post.
        title: Post title.
        body: Post content.
    """

    id: int
    user_id: int
    title: str
    body: str

    @classmethod
    def from_api(cls, data: dict) -> Post:
        """Create a Post from API response data.

        Args:
            data: Dictionary from API response.

        Returns:
            Post instance.
        """
        return cls(
            id=data["id"],
            user_id=data["userId"],
            title=data["title"],
            body=data["body"],
        )
