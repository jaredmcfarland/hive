"""Read-only queries for Trakr.

Demonstrates query caching, filtering, and aggregation with SQLModel.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from hive import query
from hive.contracts import requires
from hive.runtime.context import ExecutionContext
from hive.types import PositiveInt
from pydantic import BaseModel
from sqlmodel import select

from trakr.app import app
from trakr.entities import (
    Client,
    Project,
    ProjectStatus,
    TimeEntry,
    TimeEntryStatus,
)

# --- Data Transfer Objects for Complex Results ---
# Use Pydantic models for DTOs to get JSON serialization


class ProjectSummary(BaseModel):
    """Summary of a project with time tracking stats."""

    project_id: int
    project_name: str
    client_name: str
    total_hours: float
    billable_hours: float
    budget_remaining: float | None
    effective_rate: Decimal


class TimeSummary(BaseModel):
    """Summary of time entries for a period."""

    period: str
    total_hours: float
    billable_hours: float
    billable_amount: Decimal
    entry_count: int
    projects: list[str]


# --- Client Queries ---


@query(app, cache_ttl=300)  # Cache for 5 minutes
async def list_clients(
    ctx: ExecutionContext,
) -> list[Client]:
    """List all clients.

    Results are cached for 5 minutes.

    Args:
        ctx: Execution context.

    Returns:
        List of all Client objects, sorted by name.

    Example:
        $ trakr list-clients
        1. Acme Corp ($150/hr)
        2. Beta Inc ($125/hr)
    """
    result = await ctx.db.execute(select(Client).order_by(Client.name))
    return list(result.scalars().all())


@query(app)
@requires(lambda _ctx, client_id, **_kw: client_id > 0, "Client ID must be positive")
async def get_client(
    ctx: ExecutionContext,
    client_id: PositiveInt,
) -> Client | None:
    """Get a client by ID.

    Args:
        ctx: Execution context.
        client_id: ID of client to retrieve.

    Returns:
        The Client if found, None otherwise.

    Example:
        $ trakr get-client 1
        Acme Corp
        Email: contact@acme.com
        Rate: $150/hr
    """
    result = await ctx.db.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


# --- Project Queries ---


@query(app, cache_ttl=60)  # Cache for 1 minute
async def list_projects(
    ctx: ExecutionContext,
    client_id: int | None = None,
    status: Literal["active", "paused", "completed", "archived", "all"] = "active",
) -> list[Project]:
    """List projects with optional filtering.

    Args:
        ctx: Execution context.
        client_id: Filter by client (None = all clients).
        status: Filter by status (default: active only).

    Returns:
        Matching projects sorted by name.

    Example:
        $ trakr list-projects
        Active Projects:
        1. Website Redesign (Acme Corp)
        2. Mobile App (Beta Inc)

        $ trakr list-projects --client-id 1 --status all
        All Projects for Acme Corp:
        ...
    """
    # Build query dynamically
    stmt = select(Project)

    if client_id is not None:
        stmt = stmt.where(Project.client_id == client_id)

    if status != "all":
        stmt = stmt.where(Project.status == ProjectStatus(status))

    stmt = stmt.order_by(Project.name)

    result = await ctx.db.execute(stmt)
    return list(result.scalars().all())


@query(app)
@requires(lambda _ctx, project_id, **_kw: project_id > 0, "Project ID must be positive")
async def get_project_summary(
    ctx: ExecutionContext,
    project_id: PositiveInt,
) -> ProjectSummary | None:
    """Get detailed summary for a project.

    Includes time tracking statistics and budget status.

    Args:
        ctx: Execution context.
        project_id: Project to summarize.

    Returns:
        ProjectSummary or None if project not found.

    Example:
        $ trakr get-project-summary 1
        Website Redesign
        Client: Acme Corp
        Total: 32.5 hours
        Billable: 28.0 hours ($4,200)
        Budget: 7.5 hours remaining
    """
    # Get project with client relationship
    result = await ctx.db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        return None

    # Get client
    client_result = await ctx.db.execute(select(Client).where(Client.id == project.client_id))
    client = client_result.scalar_one_or_none()
    if client is None:
        return None

    # Get time entries for this project
    entries_result = await ctx.db.execute(
        select(TimeEntry).where(TimeEntry.project_id == project_id)
    )
    project_entries = list(entries_result.scalars().all())

    # Calculate time stats
    total_hours = sum(e.duration_hours for e in project_entries)
    billable_hours = sum(
        e.duration_hours
        for e in project_entries
        if e.status in (TimeEntryStatus.BILLABLE, TimeEntryStatus.BILLED)
    )

    # Determine effective rate
    effective_rate = project.hourly_rate or client.hourly_rate

    # Calculate budget remaining
    budget_remaining = None
    if project.budget_hours is not None:
        budget_remaining = project.budget_hours - total_hours

    return ProjectSummary(
        project_id=project.id,
        project_name=project.name,
        client_name=client.name,
        total_hours=round(total_hours, 2),
        billable_hours=round(billable_hours, 2),
        budget_remaining=round(budget_remaining, 2) if budget_remaining else None,
        effective_rate=effective_rate,
    )


# --- Time Entry Queries ---


@query(app, cache_ttl=30)  # Cache for 30 seconds
async def list_time_entries(
    ctx: ExecutionContext,
    project_id: int | None = None,
    status: Literal["draft", "billable", "billed", "non_billable", "all"] = "all",
    days: int = 7,
) -> list[TimeEntry]:
    """List recent time entries.

    Args:
        ctx: Execution context.
        project_id: Filter by project (None = all).
        status: Filter by billing status.
        days: How many days back to look (default 7).

    Returns:
        Matching entries sorted by start time (newest first).

    Example:
        $ trakr list-time-entries --days 30 --status billable
        Billable entries (last 30 days):
        ...
    """
    cutoff = datetime.now() - timedelta(days=days)

    # Build query
    stmt = select(TimeEntry).where(TimeEntry.started_at >= cutoff)

    if project_id is not None:
        stmt = stmt.where(TimeEntry.project_id == project_id)

    if status != "all":
        stmt = stmt.where(TimeEntry.status == TimeEntryStatus(status))

    stmt = stmt.order_by(TimeEntry.started_at.desc())

    result = await ctx.db.execute(stmt)
    return list(result.scalars().all())


@query(app)
async def get_time_summary(
    ctx: ExecutionContext,
    days: int = 7,
) -> TimeSummary:
    """Get summary statistics for recent time entries.

    Args:
        ctx: Execution context.
        days: How many days to summarize.

    Returns:
        TimeSummary with aggregate statistics.

    Example:
        $ trakr get-time-summary --days 30
        Last 30 days:
        Total: 120.5 hours across 3 projects
        Billable: 95.0 hours ($14,250)
        Entries: 47
    """
    cutoff = datetime.now() - timedelta(days=days)

    # Get entries in period
    result = await ctx.db.execute(select(TimeEntry).where(TimeEntry.started_at >= cutoff))
    period_entries = list(result.scalars().all())

    # Calculate stats
    total_hours = sum(e.duration_hours for e in period_entries)
    billable_entries = [
        e for e in period_entries if e.status in (TimeEntryStatus.BILLABLE, TimeEntryStatus.BILLED)
    ]
    billable_hours = sum(e.duration_hours for e in billable_entries)

    # Calculate billable amount (need to look up rates)
    billable_amount = Decimal("0.00")
    project_ids = {e.project_id for e in period_entries}

    # Batch load projects and clients
    if project_ids:
        proj_result = await ctx.db.execute(select(Project).where(Project.id.in_(project_ids)))
        projects_map = {p.id: p for p in proj_result.scalars().all()}

        client_ids = {p.client_id for p in projects_map.values()}
        client_result = await ctx.db.execute(select(Client).where(Client.id.in_(client_ids)))
        clients_map = {c.id: c for c in client_result.scalars().all()}

        for entry in billable_entries:
            project = projects_map.get(entry.project_id)
            if project:
                client = clients_map.get(project.client_id)
                rate = project.hourly_rate or (client.hourly_rate if client else Decimal("0"))
                billable_amount += rate * Decimal(str(entry.duration_hours))

        project_names = [p.name for p in projects_map.values()]
    else:
        project_names = []

    return TimeSummary(
        period=f"Last {days} days",
        total_hours=round(total_hours, 2),
        billable_hours=round(billable_hours, 2),
        billable_amount=round(billable_amount, 2),
        entry_count=len(period_entries),
        projects=sorted(project_names),
    )


# --- Search Query ---


@query(app)
async def search_entries(
    ctx: ExecutionContext,
    search_query: str,
    limit: int = 20,
) -> list[TimeEntry]:
    """Search time entries by description.

    Args:
        ctx: Execution context.
        search_query: Search term (matches description).
        limit: Maximum results to return.

    Returns:
        Matching entries sorted by date (newest first).

    Example:
        $ trakr search-entries "login"
        Found 5 entries matching "login":
        ...
    """
    # Use SQL LIKE for text search
    result = await ctx.db.execute(
        select(TimeEntry)
        .where(TimeEntry.description.ilike(f"%{search_query}%"))
        .order_by(TimeEntry.started_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
