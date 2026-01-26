"""Time tracking commands.

Demonstrates timer mechanics and complex validation with SQLModel.
"""

from __future__ import annotations

from datetime import datetime

from hive import command
from hive.contracts import ensures, requires
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, PositiveInt
from sqlmodel import select

from trakr.app import app
from trakr.entities import Project, TimeEntry, TimeEntryStatus


async def _get_running_entry(ctx: ExecutionContext) -> TimeEntry | None:
    """Find any currently running time entry."""
    result = await ctx.db.execute(select(TimeEntry).where(TimeEntry.ended_at.is_(None)))
    return result.scalar_one_or_none()


@command(app)
@requires(lambda _ctx, project_id, **_kw: project_id > 0, "Project ID must be positive")
@ensures(lambda _ctx, result, **_kw: result.is_running, "Started entry must be running")
async def start_timer(
    ctx: ExecutionContext,
    project_id: PositiveInt,
    description: NonEmptyStr,
) -> TimeEntry:
    """Start a new time tracking timer.

    Stops any currently running timer before starting a new one.

    Args:
        ctx: Execution context.
        project_id: Project to track time for.
        description: What you're working on.

    Returns:
        The new running TimeEntry.

    Raises:
        CommandError: If project not found.

    Example:
        $ trakr start-timer 1 "Implementing login page"
        Started timer: Implementing login page
        Project: Website Redesign
    """
    # Verify project exists
    result = await ctx.db.execute(select(Project).where(Project.id == project_id))
    if result.scalar_one_or_none() is None:
        raise CommandError(f"Project {project_id} not found", exit_code=1)

    # Stop any running timer first
    running = await _get_running_entry(ctx)
    if running is not None:
        running.ended_at = datetime.now()
        ctx.db.add(running)

    # Create new entry
    entry = TimeEntry(
        project_id=project_id,
        description=description.strip(),
        started_at=datetime.now(),
    )

    ctx.db.add(entry)
    await ctx.db.flush()
    await ctx.db.refresh(entry)

    return entry


@command(app)
@ensures(
    lambda _ctx, result, **_kw: result is None or not result.is_running,
    "Stopped entry must not be running",
)
async def stop_timer(
    ctx: ExecutionContext,
) -> TimeEntry | None:
    """Stop the currently running timer.

    Args:
        ctx: Execution context.

    Returns:
        The stopped TimeEntry, or None if no timer was running.

    Example:
        $ trakr stop-timer
        Stopped: Implementing login page
        Duration: 1.5 hours
    """
    running = await _get_running_entry(ctx)
    if running is None:
        return None

    running.ended_at = datetime.now()
    ctx.db.add(running)

    return running


@command(app)
async def current(
    ctx: ExecutionContext,
) -> TimeEntry | None:
    """Show the currently running timer.

    Args:
        ctx: Execution context.

    Returns:
        The running TimeEntry, or None if no timer is running.

    Example:
        $ trakr current
        Running: Implementing login page
        Project: Website Redesign
        Duration: 0.5 hours (and counting)
    """
    return await _get_running_entry(ctx)


@command(app)
@requires(lambda _ctx, entry_id, **_kw: entry_id > 0, "Entry ID must be positive")
async def update_time_entry(
    ctx: ExecutionContext,
    entry_id: PositiveInt,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    description: str | None = None,
) -> TimeEntry:
    """Update a time entry's times or description.

    Args:
        ctx: Execution context.
        entry_id: Entry to update.
        started_at: New start time (if provided).
        ended_at: New end time (if provided).
        description: New description (if provided).

    Returns:
        The updated TimeEntry.

    Example:
        $ trakr update-time-entry 1 --ended-at "2024-01-15 11:30"
        Updated entry 1
    """
    result = await ctx.db.execute(select(TimeEntry).where(TimeEntry.id == entry_id))
    entry = result.scalar_one_or_none()

    if entry is None:
        raise CommandError(f"Entry {entry_id} not found", exit_code=1)

    if started_at is not None:
        entry.started_at = started_at
    if ended_at is not None:
        if ended_at <= entry.started_at:
            raise CommandError("End time must be after start time", exit_code=1)
        entry.ended_at = ended_at
    if description is not None:
        entry.description = description

    ctx.db.add(entry)
    return entry


@command(app)
@requires(lambda _ctx, entry_id, **_kw: entry_id > 0, "Entry ID must be positive")
async def mark_billable(
    ctx: ExecutionContext,
    entry_id: PositiveInt,
    billable: bool = True,
) -> TimeEntry:
    """Mark a time entry as billable or non-billable.

    Args:
        ctx: Execution context.
        entry_id: Entry to update.
        billable: Whether the entry is billable.

    Returns:
        The updated TimeEntry.

    Example:
        $ trakr mark-billable 1
        Entry 1 marked as billable
        $ trakr mark-billable 2 --no-billable
        Entry 2 marked as non-billable
    """
    result = await ctx.db.execute(select(TimeEntry).where(TimeEntry.id == entry_id))
    entry = result.scalar_one_or_none()

    if entry is None:
        raise CommandError(f"Entry {entry_id} not found", exit_code=1)

    if entry.is_running:
        raise CommandError("Cannot change status of running entry", exit_code=1)

    entry.status = TimeEntryStatus.BILLABLE if billable else TimeEntryStatus.NON_BILLABLE
    ctx.db.add(entry)

    return entry
