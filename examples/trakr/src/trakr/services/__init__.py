"""External service integrations for Trakr.

Demonstrates the @service decorator pattern.
"""

from __future__ import annotations

from typing import Any

import httpx
from hive.core.decorators import service

from trakr.app import app


@service(app, credentials="env:GITHUB_TOKEN")
def github_client(credentials: str | None) -> GitHubClient:
    """GitHub API client for syncing issues.

    Credentials are loaded from the GITHUB_TOKEN environment variable.

    Args:
        credentials: GitHub personal access token.

    Returns:
        Configured GitHubClient instance.

    Example:
        >>> # In a command:
        >>> issues = await ctx.services.github_client.list_issues("owner", "repo")
    """
    return GitHubClient(token=credentials)


class GitHubClient:
    """Client for GitHub API operations.

    Provides methods to sync GitHub issues with Trakr projects.
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ) -> None:
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token.
            base_url: API base URL.
            timeout: Request timeout.
        """
        self.token = token
        self.base_url = base_url
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Trakr/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List issues from a GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state filter (open, closed, all).
            labels: Filter by labels.

        Returns:
            List of issue dictionaries.
        """
        params: dict[str, Any] = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict[str, Any]:
        """Get a single issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.

        Returns:
            Issue dictionary.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def create_time_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        hours: float,
        description: str,
    ) -> dict[str, Any]:
        """Add a time tracking comment to an issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.
            hours: Hours worked.
            description: Work description.

        Returns:
            Created comment dictionary.
        """
        body = f"**Time Logged:** {hours:.2f} hours\n\n{description}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                headers=self._headers(),
                json={"body": body},
            )
            response.raise_for_status()
            return response.json()
