"""Project management commands.

Demonstrates relationships between entities and enum handling.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from hive import command
from hive.contracts import requires
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, PositiveInt
from sqlmodel import select

from trakr.app import app
from trakr.entities import Client, Project, ProjectStatus


@command(app)
@requires(lambda _ctx, client_id, **_kw: client_id > 0, "Client ID must be positive")
async def create_project(
    ctx: ExecutionContext,
    client_id: PositiveInt,
    name: NonEmptyStr,
    description: str | None = None,
    hourly_rate: float | None = None,
    budget_hours: float | None = None,
) -> Project:
    """Create a new project for a client.

    Args:
        ctx: Execution context.
        client_id: Owning client's ID.
        name: Project name.
        description: Optional description.
        hourly_rate: Override rate (None = use client rate).
        budget_hours: Optional hour budget.

    Returns:
        The created Project.

    Raises:
        CommandError: If client not found.

    Example:
        $ trakr create-project 1 "Website Redesign" --budget-hours 40
        Created project 1: Website Redesign
    """
    # Verify client exists
    result = await ctx.db.execute(select(Client).where(Client.id == client_id))
    if result.scalar_one_or_none() is None:
        raise CommandError(f"Client {client_id} not found", exit_code=1)

    project = Project(
        client_id=client_id,
        name=name.strip(),
        description=description,
        hourly_rate=Decimal(str(hourly_rate)) if hourly_rate else None,
        budget_hours=budget_hours,
    )

    ctx.db.add(project)
    await ctx.db.flush()
    await ctx.db.refresh(project)

    return project


@command(app)
@requires(lambda _ctx, project_id, **_kw: project_id > 0, "Project ID must be positive")
async def update_project_status(
    ctx: ExecutionContext,
    project_id: PositiveInt,
    status: Literal["active", "paused", "completed", "archived"],
) -> Project:
    """Update a project's status.

    Args:
        ctx: Execution context.
        project_id: Project to update.
        status: New status (active, paused, completed, archived).

    Returns:
        The updated Project.

    Raises:
        CommandError: If project not found.

    Example:
        $ trakr update-project-status 1 completed
        Project 1 status: completed
    """
    result = await ctx.db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise CommandError(f"Project {project_id} not found", exit_code=1)

    project.status = ProjectStatus(status)
    ctx.db.add(project)

    return project


@command(app)
@requires(lambda _ctx, project_id, **_kw: project_id > 0, "Project ID must be positive")
async def set_project_budget(
    ctx: ExecutionContext,
    project_id: PositiveInt,
    budget_hours: float,
) -> Project:
    """Set or update a project's hour budget.

    Args:
        ctx: Execution context.
        project_id: Project to update.
        budget_hours: New hour budget (0 to remove).

    Returns:
        The updated Project.

    Example:
        $ trakr set-project-budget 1 80
        Project 1 budget: 80.0 hours
    """
    result = await ctx.db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise CommandError(f"Project {project_id} not found", exit_code=1)

    project.budget_hours = budget_hours if budget_hours > 0 else None
    ctx.db.add(project)

    return project
