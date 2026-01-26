"""GitHub sync commands.

Demonstrates using external services in commands.
"""

from __future__ import annotations

from hive.core.decorators import command
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, PositiveInt
from sqlmodel import select

from trakr.app import app
from trakr.entities import TimeEntry


@command(app)
async def sync_issue(
    ctx: ExecutionContext,
    owner: NonEmptyStr,
    repo: NonEmptyStr,
    issue_number: PositiveInt,
    entry_id: PositiveInt,
) -> str:
    """Sync a time entry to a GitHub issue.

    Posts a comment with time tracking info to the issue.

    Args:
        ctx: Execution context with services.
        owner: GitHub repository owner.
        repo: Repository name.
        issue_number: Issue number.
        entry_id: Time entry to sync.

    Returns:
        URL of the created comment.

    Raises:
        CommandError: If entry not found or GitHub API fails.

    Example:
        $ trakr sync-issue acme website-redesign 42 --entry-id 5
        Synced 2.5 hours to acme/website-redesign#42
        Comment: https://github.com/acme/website-redesign/issues/42#issuecomment-123
    """
    result = await ctx.db.execute(select(TimeEntry).where(TimeEntry.id == entry_id))
    entry = result.scalar_one_or_none()

    if entry is None:
        raise CommandError(f"Entry {entry_id} not found", exit_code=1)

    if entry.is_running:
        raise CommandError("Cannot sync running entry", exit_code=1)

    # Use the GitHub service
    github = ctx.services.github_client

    try:
        comment = await github.create_time_comment(
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            hours=entry.duration_hours,
            description=entry.description,
        )
        return comment.get("html_url", "Comment created")
    except Exception as e:
        raise CommandError(f"GitHub API error: {e}", exit_code=1) from e


@command(app)
async def list_github_issues(
    ctx: ExecutionContext,
    owner: NonEmptyStr,
    repo: NonEmptyStr,
    labels: str | None = None,
) -> list[dict[str, str]]:
    """List open issues from a GitHub repository.

    Args:
        ctx: Execution context with services.
        owner: Repository owner.
        repo: Repository name.
        labels: Comma-separated label filter.

    Returns:
        List of issue summaries (number, title, url).

    Example:
        $ trakr list-github-issues acme website-redesign --labels "in-progress"
        #42 Implement login page
        #43 Fix mobile navigation
    """
    github = ctx.services.github_client

    label_list = labels.split(",") if labels else None

    try:
        issues = await github.list_issues(
            owner=owner,
            repo=repo,
            labels=label_list,
        )

        return [
            {
                "number": str(issue["number"]),
                "title": issue["title"],
                "url": issue["html_url"],
            }
            for issue in issues
        ]
    except Exception as e:
        raise CommandError(f"GitHub API error: {e}", exit_code=1) from e
