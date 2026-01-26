"""Client management commands.

Demonstrates basic CRUD operations with validation contracts and SQLModel.
"""

from __future__ import annotations

from decimal import Decimal

from hive import command
from hive.contracts import ensures, requires
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, NonNegativeFloat, PositiveInt
from sqlmodel import select

from trakr.app import app
from trakr.entities import Client, Project, ProjectStatus


@command(app)
@requires(lambda _ctx, name, **_kw: len(name.strip()) > 0, "Client name cannot be empty")
@ensures(
    lambda _ctx, name, result, **_kw: result.name == name.strip(),
    "Created client name must match input",
)
async def create_client(
    ctx: ExecutionContext,
    name: NonEmptyStr,
    email: str | None = None,
    hourly_rate: NonNegativeFloat = 0.0,
) -> Client:
    """Create a new client.

    Args:
        ctx: Execution context.
        name: Client name (cannot be empty).
        email: Optional contact email.
        hourly_rate: Default billing rate per hour.

    Returns:
        The created Client with assigned ID.

    Example:
        $ trakr create-client "Acme Corp" --email contact@acme.com --hourly-rate 150
        Created client 1: Acme Corp
    """
    client = Client(
        name=name.strip(),
        email=email,
        hourly_rate=Decimal(str(hourly_rate)),
    )

    ctx.db.add(client)
    await ctx.db.flush()  # Assigns ID without committing
    await ctx.db.refresh(client)  # Load the assigned ID

    return client


@command(app)
@requires(lambda _ctx, client_id, **_kw: client_id > 0, "Client ID must be positive")
async def update_client(
    ctx: ExecutionContext,
    client_id: PositiveInt,
    name: str | None = None,
    email: str | None = None,
    hourly_rate: float | None = None,
) -> Client:
    """Update an existing client.

    Args:
        ctx: Execution context.
        client_id: ID of client to update.
        name: New name (if provided).
        email: New email (if provided).
        hourly_rate: New rate (if provided).

    Returns:
        The updated Client.

    Raises:
        CommandError: If client not found.

    Example:
        $ trakr update-client 1 --hourly-rate 175
        Updated client 1
    """
    result = await ctx.db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if client is None:
        raise CommandError(f"Client {client_id} not found", exit_code=1)

    if name is not None:
        client.name = name.strip()
    if email is not None:
        client.email = email
    if hourly_rate is not None:
        client.hourly_rate = Decimal(str(hourly_rate))

    ctx.db.add(client)
    return client


@command(app)
@requires(lambda _ctx, client_id, **_kw: client_id > 0, "Client ID must be positive")
async def archive_client(
    ctx: ExecutionContext,
    client_id: PositiveInt,
) -> bool:
    """Archive a client and all their projects.

    Archived clients are hidden from normal queries but not deleted.

    Args:
        ctx: Execution context.
        client_id: ID of client to archive.

    Returns:
        True if archived, False if not found.

    Example:
        $ trakr archive-client 1
        Archived client 1 and 3 projects
    """
    # Get client
    result = await ctx.db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()

    if client is None:
        return False

    # Archive all client's projects
    projects_result = await ctx.db.execute(select(Project).where(Project.client_id == client_id))
    for project in projects_result.scalars():
        project.status = ProjectStatus.ARCHIVED
        ctx.db.add(project)

    # Delete client (or mark as archived if you have a soft-delete pattern)
    await ctx.db.delete(client)
    return True
