# Building a Time Tracker with Hive

A comprehensive tutorial for building a real-world application that exercises all of Hive's features.

## What We're Building

**Trakr** is a personal project and time tracking application that lets you:

- Track projects with clients and billing rates
- Log time entries with descriptions
- Generate invoices and reports
- Sync with external services (GitHub issues)
- View everything in a terminal UI

By the end of this tutorial, you'll have built an application that demonstrates:

| Feature | Hive Concept |
|---------|--------------|
| Data models | `@entity` decorator |
| State changes | `@command` decorator |
| Read operations | `@query` decorator with caching |
| External APIs | `@service` decorator with credentials |
| Input validation | Refinement types (`PositiveInt`, `NonEmptyStr`) |
| Business rules | `@requires` and `@ensures` contracts |
| Terminal UI | `@screen` decorator with widgets |
| Multiple interfaces | CLI, TUI, and REST from same code |
| Testing | `TestClient` and property-based testing |

## Prerequisites

- Python 3.12+
- `uv` package manager
- Basic familiarity with async Python and type hints

## Part 1: Project Setup

### 1.1 Create the Project

```bash
# Create a new Hive project
uv run hive new trakr

# Navigate to the project
cd trakr

# Install dependencies
uv sync --dev
```

This creates a standard project structure:

```
trakr/
├── pyproject.toml
├── src/
│   └── trakr/
│       ├── __init__.py
│       ├── app.py           # App instance
│       ├── entities.py      # Data models
│       ├── commands.py      # State-changing operations
│       └── queries.py       # Read operations
└── tests/
    ├── __init__.py
    └── test_commands.py
```

### 1.2 Define the App

Edit `src/trakr/app.py`:

```python
"""Trakr - Personal project and time tracking."""

from hive.app import App

app = App(
    "trakr",
    description="Track projects, time, and generate invoices",
)
```

The `App` instance is the central registry. All decorators receive it to register themselves.

### 1.3 Understand the Architecture

Hive follows a three-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │   CLI   │  │   TUI   │  │   MCP   │  │    REST API     │ │
│  │ (Typer) │  │(Textual)│  │(FastMCP)│  │    (FastAPI)    │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
└───────┼────────────┼────────────┼────────────────┼──────────┘
        │            │            │                │
        ▼            ▼            ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Specification Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   App Registry                        │   │
│  │  @command, @query, @entity, @screen, @service        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Runtime Layer                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │  ctx.db    │  │ctx.services│  │      ctx.config        │ │
│  │ (SQLModel) │  │  (httpx)   │  │  (Pydantic Settings)   │ │
│  └────────────┘  └────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

You write decorated Python code. Hive generates interfaces.

## Part 2: Entities and Data Modeling

### 2.1 Define Core Entities

Entities are SQLModel classes that map to database tables. Create `src/trakr/entities.py`:

```python
"""Data entities for Trakr.

These SQLModel classes define the database schema. Each class with
`table=True` becomes a table. Hive's `@entity` decorator registers
them for CLI introspection and schema generation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel

from trakr.app import app
from hive import entity


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TimeEntryStatus(str, Enum):
    """Time entry billing status."""

    DRAFT = "draft"
    BILLABLE = "billable"
    BILLED = "billed"
    NON_BILLABLE = "non_billable"


@entity(app)
class Client(SQLModel, table=True):
    """A client who owns projects.

    Attributes:
        id: Auto-generated primary key.
        name: Client display name.
        email: Contact email address.
        hourly_rate: Default hourly rate in dollars.
        created_at: When the client was created.
        projects: Related projects (back-populated).
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Client display name")
    email: str | None = Field(default=None, description="Contact email")
    hourly_rate: Decimal = Field(default=Decimal("0.00"), description="Default rate per hour")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    # Relationships
    projects: list["Project"] = Relationship(back_populates="client")


@entity(app)
class Project(SQLModel, table=True):
    """A project belonging to a client.

    Attributes:
        id: Auto-generated primary key.
        client_id: Foreign key to owning client.
        name: Project name.
        description: Optional project description.
        status: Current project status.
        hourly_rate: Override rate (None = use client rate).
        budget_hours: Optional hour budget.
        created_at: When the project was created.
    """

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id", description="Owning client")
    name: str = Field(index=True, description="Project name")
    description: str | None = Field(default=None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    hourly_rate: Decimal | None = Field(default=None, description="Override hourly rate")
    budget_hours: float | None = Field(default=None, description="Hour budget")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    # Relationships
    client: Client | None = Relationship(back_populates="projects")
    time_entries: list["TimeEntry"] = Relationship(back_populates="project")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_rate(self) -> Decimal:
        """Get the effective hourly rate (project override or client default)."""
        if self.hourly_rate is not None:
            return self.hourly_rate
        if self.client is not None:
            return self.client.hourly_rate
        return Decimal("0.00")


@entity(app)
class TimeEntry(SQLModel, table=True):
    """A time tracking entry.

    Attributes:
        id: Auto-generated primary key.
        project_id: Foreign key to associated project.
        description: What was worked on.
        started_at: When work began.
        ended_at: When work ended (None = in progress).
        status: Billing status.
    """

    __tablename__ = "time_entry"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", description="Associated project")
    description: str = Field(description="Work description")
    started_at: datetime = Field(default_factory=datetime.now, description="Start time")
    ended_at: datetime | None = Field(default=None, description="End time (None = running)")
    status: TimeEntryStatus = Field(default=TimeEntryStatus.DRAFT, description="Billing status")

    # Relationships
    project: Project | None = Relationship(back_populates="time_entries")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours."""
        end = self.ended_at if self.ended_at else datetime.now()
        delta = end - self.started_at
        return delta.total_seconds() / 3600

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_running(self) -> bool:
        """Check if timer is currently running."""
        return self.ended_at is None


@entity(app)
class Invoice(SQLModel, table=True):
    """An invoice for billable time.

    Attributes:
        id: Auto-generated primary key.
        client_id: Foreign key to client being invoiced.
        number: Invoice number (e.g., "INV-2024-001").
        issued_at: When invoice was created.
        due_at: Payment due date.
        total_amount: Total in dollars.
        paid: Whether invoice has been paid.
    """

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id", description="Client being invoiced")
    number: str = Field(unique=True, description="Invoice number")
    issued_at: datetime = Field(default_factory=datetime.now, description="Issue date")
    due_at: datetime = Field(description="Payment due date")
    total_amount: Decimal = Field(description="Total amount")
    paid: bool = Field(default=False, description="Payment status")

    # Relationships
    client: Client | None = Relationship()
```

**Key Points:**

1. **SQLModel classes** - Inherit from `SQLModel` with `table=True` for database tables.

2. **`@entity(app)` decorator** - Registers the model with Hive for CLI introspection and schema generation.

3. **`Field()` for metadata** - Provides descriptions, constraints, and database hints:
   - `primary_key=True` - Auto-increment ID
   - `foreign_key="table.column"` - Relationships
   - `index=True` - Database index
   - `unique=True` - Unique constraint
   - `description="..."` - Shows in `--help` and OpenAPI docs

4. **Relationships** - SQLModel/SQLAlchemy relationships for eager loading:
   - `Relationship(back_populates="field")` - Bidirectional
   - Accessed as `project.client.name` after loading

5. **Computed fields** - `@computed_field` + `@property` for derived values that appear in JSON output.

### 2.2 Database Initialization

Create `src/trakr/database.py` to handle table creation:

```python
"""Database initialization for Trakr."""

from __future__ import annotations

from sqlmodel import SQLModel

from hive.runtime.database import create_session_factory


async def init_database(database_url: str = "sqlite+aiosqlite:///trakr.db") -> None:
    """Initialize database tables.

    Creates all tables defined by SQLModel classes.

    Args:
        database_url: Database connection URL.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    # Import entities to register them with SQLModel
    from trakr import entities  # noqa: F401

    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await engine.dispose()


def get_session_factory(database_url: str = "sqlite+aiosqlite:///trakr.db"):
    """Get a session factory for the database.

    Args:
        database_url: Database connection URL.

    Returns:
        Async session factory.
    """
    return create_session_factory(database_url)
```

The database file (`trakr.db`) is created automatically on first run.

## Part 3: Commands with Contracts

Commands are state-changing operations. They create, update, or delete data.

### 3.1 Client Commands

Create `src/trakr/commands/clients.py`:

```python
"""Client management commands.

Demonstrates basic CRUD operations with validation contracts and SQLModel.
"""

from __future__ import annotations

from decimal import Decimal

from sqlmodel import select

from hive import command
from hive.contracts import ensures, requires
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, NonNegativeFloat, PositiveInt

from trakr.app import app
from trakr.entities import Client, Project, ProjectStatus


@command(app)
@requires(
    lambda _ctx, name, **_kw: len(name.strip()) > 0,
    "Client name cannot be empty"
)
@ensures(
    lambda _ctx, name, result, **_kw: result.name == name.strip(),
    "Created client name must match input"
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
@requires(
    lambda _ctx, client_id, **_kw: client_id > 0,
    "Client ID must be positive"
)
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
@requires(
    lambda _ctx, client_id, **_kw: client_id > 0,
    "Client ID must be positive"
)
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
    projects_result = await ctx.db.execute(
        select(Project).where(Project.client_id == client_id)
    )
    for project in projects_result.scalars():
        project.status = ProjectStatus.ARCHIVED
        ctx.db.add(project)

    # Delete client (or mark as archived if you have a soft-delete pattern)
    await ctx.db.delete(client)
    return True
```

**Key Hive Concepts:**

1. **`ctx.db` is an AsyncSession** - Use SQLModel/SQLAlchemy operations:
   - `ctx.db.add(obj)` - Stage for insert/update
   - `ctx.db.execute(select(...))` - Run queries
   - `await ctx.db.flush()` - Flush pending changes (assigns IDs)
   - `await ctx.db.refresh(obj)` - Reload from database

2. **Automatic transaction management** - Hive's `ExecutionContext` auto-commits on success, auto-rollbacks on exception.

3. **Refinement Types** - `NonEmptyStr`, `PositiveInt`, `NonNegativeFloat` validate at the boundary.

4. **Contract Decorators**:
   - `@requires` - Preconditions checked before execution
   - `@ensures` - Postconditions validated after execution

5. **CommandError** - Raises user-friendly errors with exit codes.

### 3.2 Project Commands

Create `src/trakr/commands/projects.py`:

```python
"""Project management commands.

Demonstrates relationships between entities and enum handling.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from sqlmodel import select

from hive import command
from hive.contracts import requires
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, PositiveInt

from trakr.app import app
from trakr.entities import Client, Project, ProjectStatus


@command(app)
@requires(
    lambda _ctx, client_id, **_kw: client_id > 0,
    "Client ID must be positive"
)
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
@requires(
    lambda _ctx, project_id, **_kw: project_id > 0,
    "Project ID must be positive"
)
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
@requires(
    lambda _ctx, project_id, **_kw: project_id > 0,
    "Project ID must be positive"
)
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
```

**Key Points:**

1. **Literal Types** - `Literal["active", "paused", ...]` creates CLI choices automatically.

2. **Foreign key validation** - Check client exists before creating project.

3. **Optional with Meaning** - `hourly_rate: float | None` means "inherit from client."

### 3.3 Time Entry Commands

Create `src/trakr/commands/time.py`:

```python
"""Time tracking commands.

Demonstrates timer mechanics and complex validation with SQLModel.
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from hive import command
from hive.contracts import ensures, requires
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, PositiveInt

from trakr.app import app
from trakr.entities import Project, TimeEntry, TimeEntryStatus


async def _get_running_entry(ctx: ExecutionContext) -> TimeEntry | None:
    """Find any currently running time entry."""
    result = await ctx.db.execute(
        select(TimeEntry).where(TimeEntry.ended_at.is_(None))
    )
    return result.scalar_one_or_none()


@command(app)
@requires(
    lambda _ctx, project_id, **_kw: project_id > 0,
    "Project ID must be positive"
)
@ensures(
    lambda _ctx, _project_id, _description, result, **_kw: result.is_running,
    "Started entry must be running"
)
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
    "Stopped entry must not be running"
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
@requires(
    lambda _ctx, entry_id, **_kw: entry_id > 0,
    "Entry ID must be positive"
)
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
@requires(
    lambda _ctx, entry_id, **_kw: entry_id > 0,
    "Entry ID must be positive"
)
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
```

**Key Points:**

1. **Async helper function** - `_get_running_entry(ctx)` now takes context and uses `ctx.db`.

2. **SQLModel queries** - `select(TimeEntry).where(TimeEntry.ended_at.is_(None))` finds running entries.

3. **Timer State Machine** - `start_timer` stops any running timer first via database update.

4. **Boolean Flags** - `billable: bool = True` becomes `--billable/--no-billable` in CLI.

### 3.4 Register Commands

Create `src/trakr/commands/__init__.py`:

```python
"""Command modules for Trakr.

Import all command modules to register them with the app.
"""

from trakr.commands import clients, projects, time

__all__ = ["clients", "projects", "time"]
```

## Part 4: Queries with Caching

Queries are read-only operations. They retrieve data without modifying state.

### 4.1 Client and Project Queries

Create `src/trakr/queries.py`:

```python
"""Read-only queries for Trakr.

Demonstrates query caching, filtering, and aggregation with SQLModel.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel
from sqlmodel import select

from hive import query
from hive.contracts import requires
from hive.runtime.context import ExecutionContext
from hive.types import PositiveInt

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
@requires(
    lambda _ctx, client_id, **_kw: client_id > 0,
    "Client ID must be positive"
)
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
@requires(
    lambda _ctx, project_id, **_kw: project_id > 0,
    "Project ID must be positive"
)
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
    client_result = await ctx.db.execute(
        select(Client).where(Client.id == project.client_id)
    )
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
    result = await ctx.db.execute(
        select(TimeEntry).where(TimeEntry.started_at >= cutoff)
    )
    period_entries = list(result.scalars().all())

    # Calculate stats
    total_hours = sum(e.duration_hours for e in period_entries)
    billable_entries = [
        e for e in period_entries
        if e.status in (TimeEntryStatus.BILLABLE, TimeEntryStatus.BILLED)
    ]
    billable_hours = sum(e.duration_hours for e in billable_entries)

    # Calculate billable amount (need to look up rates)
    billable_amount = Decimal("0.00")
    project_ids = {e.project_id for e in period_entries}

    # Batch load projects and clients
    if project_ids:
        proj_result = await ctx.db.execute(
            select(Project).where(Project.id.in_(project_ids))
        )
        projects_map = {p.id: p for p in proj_result.scalars().all()}

        client_ids = {p.client_id for p in projects_map.values()}
        client_result = await ctx.db.execute(
            select(Client).where(Client.id.in_(client_ids))
        )
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
```

**Key Points:**

1. **Cache TTL** - `cache_ttl=300` caches results for 5 minutes, reducing database load.

2. **DTOs for Complex Results** - `ProjectSummary` and `TimeSummary` bundle related data.

3. **Literal for Choices** - Status filters become CLI choice arguments.

4. **Default Values** - `days: int = 7` provides sensible defaults.

## Part 5: External Services

Services integrate with external APIs and manage credentials securely.

### 5.1 GitHub Integration

Create `src/trakr/services/__init__.py`:

```python
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
```

### 5.2 Commands Using Services

Create `src/trakr/commands/sync.py`:

```python
"""GitHub sync commands.

Demonstrates using external services in commands.
"""

from __future__ import annotations

from hive.contracts import requires
from hive.core.decorators import command
from hive.errors import CommandError
from hive.runtime.context import ExecutionContext
from hive.types import NonEmptyStr, PositiveInt

from trakr.app import app
from trakr.entities import TimeEntry, get_store


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
    entries = get_store("time_entry")
    entry = entries.get(entry_id)

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
```

**Key Points:**

1. **`@service` Decorator** - Registers a factory function that receives credentials.

2. **Credential Patterns**:
   - `"env:GITHUB_TOKEN"` - Load from environment variable
   - `"keyring:github"` - Load from system keyring

3. **Service Access** - `ctx.services.github_client` provides lazy-initialized client.

4. **Error Handling** - Wrap service errors in `CommandError` for clean CLI output.

## Part 6: TUI Screens

The TUI provides a rich terminal interface using Textual.

### 6.1 Dashboard Screen

Create `src/trakr/screens/__init__.py`:

```python
"""TUI screens for Trakr.

Provides rich terminal interface with keyboard navigation.
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from hive.core.decorators import screen
from hive.tui.screens import HiveScreen
from hive.tui.widgets import HiveDataTable, HiveFooter, HiveHeader

from trakr.app import app
from trakr.entities import ProjectStatus, TimeEntry


@screen(app, default=True, keybinding="d", queries=["get_time_summary"])
class DashboardScreen(HiveScreen[None]):
    """Main dashboard showing current status and quick actions.

    Keybinding: d
    """

    BINDINGS = [
        Binding("s", "start_timer", "Start Timer"),
        Binding("x", "stop_timer", "Stop Timer"),
        Binding("p", "go_projects", "Projects"),
        Binding("t", "go_time", "Time Entries"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        """Build the dashboard layout."""
        yield HiveHeader(show_screen_title=True)

        with Container(id="dashboard"):
            # Current timer section
            with Vertical(id="timer-section", classes="section"):
                yield Static("Current Timer", classes="section-title")
                yield Static("No timer running", id="current-timer")
                yield Static("Press 's' to start", id="timer-hint")

            # Summary section
            with Vertical(id="summary-section", classes="section"):
                yield Static("This Week", classes="section-title")
                yield Static("Loading...", id="summary-stats")

            # Quick actions
            with Horizontal(id="actions"):
                yield Static("[s] Start  [x] Stop  [p] Projects  [t] Time  [r] Refresh")

        yield HiveFooter(show_command_palette_hint=True)

    def on_mount(self) -> None:
        """Load initial data."""
        super().on_mount()
        self._update_timer_display()

    def watch_data(self, data: list[Any]) -> None:
        """Update display when data changes."""
        if data:
            summary = data[0] if data else None
            if summary:
                stats = self.query_one("#summary-stats", Static)
                stats.update(
                    f"Total: {summary.total_hours:.1f}h | "
                    f"Billable: {summary.billable_hours:.1f}h (${summary.billable_amount})"
                )

    def _update_timer_display(self) -> None:
        """Update the current timer display."""
        # In a real implementation, this would query for the current timer
        timer_display = self.query_one("#current-timer", Static)
        timer_display.update("No timer running")

    async def action_start_timer(self) -> None:
        """Open timer start dialog."""
        self.ctx.notify("Use command palette (Ctrl+P) to start timer")

    async def action_stop_timer(self) -> None:
        """Stop the current timer."""
        # Would call stop_timer command
        self.ctx.notify("Timer stopped", severity="information")
        self._update_timer_display()

    async def action_go_projects(self) -> None:
        """Navigate to projects screen."""
        await self.ctx.navigate("ProjectsScreen")

    async def action_go_time(self) -> None:
        """Navigate to time entries screen."""
        await self.ctx.navigate("TimeScreen")

    async def action_refresh(self) -> None:
        """Refresh dashboard data."""
        await self.refresh_data()
        self._update_timer_display()


@screen(app, keybinding="p", queries=["list_projects"])
class ProjectsScreen(HiveScreen[None]):
    """Project list with status and budget info.

    Keybinding: p
    """

    BINDINGS = [
        Binding("n", "new_project", "New Project"),
        Binding("enter", "view_project", "View Details"),
        Binding("a", "filter_active", "Active Only"),
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Build the projects list."""
        yield HiveHeader(show_screen_title=True)
        yield HiveDataTable[Any](id="projects-table")
        yield HiveFooter()

    def on_mount(self) -> None:
        """Set up the table."""
        super().on_mount()
        table = self.query_one("#projects-table", HiveDataTable)
        table.add_columns("ID", "Name", "Client", "Status", "Budget")

    def watch_data(self, data: list[Any]) -> None:
        """Populate table when data loads."""
        if data:
            table = self.query_one("#projects-table", HiveDataTable)
            table.clear()
            for project in data:
                budget = f"{project.budget_hours}h" if project.budget_hours else "-"
                table.add_row(
                    str(project.id),
                    project.name,
                    str(project.client_id),  # Would look up client name
                    project.status.value,
                    budget,
                )

    async def action_new_project(self) -> None:
        """Open new project dialog."""
        self.ctx.notify("Use command palette to create project")

    async def action_view_project(self) -> None:
        """View selected project details."""
        table = self.query_one("#projects-table", HiveDataTable)
        row = table.cursor_row
        if row is not None:
            # Would navigate to project detail screen
            self.ctx.notify(f"Viewing project {row}")

    async def action_filter_active(self) -> None:
        """Toggle active-only filter."""
        self.ctx.notify("Filtering to active projects")
        await self.refresh_data()

    async def action_go_back(self) -> None:
        """Return to dashboard."""
        await self.ctx.go_back()


@screen(app, keybinding="t", queries=["list_time_entries"])
class TimeScreen(HiveScreen[None]):
    """Time entries list with filtering.

    Keybinding: t
    """

    BINDINGS = [
        Binding("s", "start_timer", "Start"),
        Binding("x", "stop_timer", "Stop"),
        Binding("b", "mark_billable", "Toggle Billable"),
        Binding("7", "filter_week", "This Week"),
        Binding("m", "filter_month", "This Month"),
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Build the time entries list."""
        yield HiveHeader(show_screen_title=True)

        with Container(id="time-container"):
            yield Static("Recent Time Entries", classes="section-title")
            yield HiveDataTable[TimeEntry](id="time-table")

        yield HiveFooter()

    def on_mount(self) -> None:
        """Set up the table."""
        super().on_mount()
        table = self.query_one("#time-table", HiveDataTable)
        table.add_columns("Date", "Project", "Description", "Hours", "Status")

    def watch_data(self, data: list[Any]) -> None:
        """Populate table when data loads."""
        if data:
            table = self.query_one("#time-table", HiveDataTable)
            table.clear()
            for entry in data:
                status = "RUNNING" if entry.is_running else entry.status.value
                table.add_row(
                    entry.started_at.strftime("%m/%d %H:%M"),
                    str(entry.project_id),
                    entry.description[:40],
                    f"{entry.duration_hours:.2f}",
                    status,
                )

    async def action_start_timer(self) -> None:
        """Start a new timer."""
        self.ctx.notify("Use command palette to start timer")

    async def action_stop_timer(self) -> None:
        """Stop current timer."""
        self.ctx.notify("Timer stopped")
        await self.refresh_data()

    async def action_mark_billable(self) -> None:
        """Toggle billable status on selected entry."""
        table = self.query_one("#time-table", HiveDataTable)
        row = table.cursor_row
        if row is not None:
            self.ctx.notify(f"Toggled billable on entry {row}")

    async def action_filter_week(self) -> None:
        """Filter to this week."""
        self.ctx.notify("Showing this week")
        await self.refresh_data()

    async def action_filter_month(self) -> None:
        """Filter to this month."""
        self.ctx.notify("Showing this month")
        await self.refresh_data()

    async def action_go_back(self) -> None:
        """Return to dashboard."""
        await self.ctx.go_back()


# Register all screens by importing them
__all__ = ["DashboardScreen", "ProjectsScreen", "TimeScreen"]
```

**Key Points:**

1. **`@screen` Decorator**:
   - `default=True` - Sets the startup screen
   - `keybinding="d"` - Global key to navigate to this screen
   - `queries=["list_projects"]` - Auto-load these queries on mount

2. **HiveScreen Base Class**:
   - `data` reactive property - Automatically updated by bound queries
   - `ctx` - Screen context with `navigate()`, `go_back()`, `notify()`
   - `refresh_data()` - Reload bound queries

3. **Textual Integration**:
   - `BINDINGS` - Keyboard shortcuts
   - `compose()` - Build widget tree
   - `watch_data()` - React to data changes

### 6.2 Styling with CSS

Create `src/trakr/trakr.tcss`:

```css
/* Trakr TUI Styles */

/* Layout */
#dashboard {
    padding: 1;
}

.section {
    border: solid $primary;
    padding: 1;
    margin-bottom: 1;
}

.section-title {
    text-style: bold;
    color: $primary;
    margin-bottom: 1;
}

#actions {
    dock: bottom;
    height: 3;
    padding: 1;
    background: $surface;
}

/* Timer Display */
#current-timer {
    text-style: bold;
    color: $success;
}

#timer-hint {
    color: $text-muted;
}

/* Tables */
HiveDataTable {
    height: 100%;
}

/* Container spacing */
#time-container {
    padding: 1;
}
```

## Part 7: Testing

Hive provides comprehensive testing utilities.

### 7.1 Unit Testing Commands

Create `tests/test_commands.py`:

```python
"""Unit tests for Trakr commands.

Demonstrates TestClient usage for command testing.
"""

from __future__ import annotations

import pytest

from hive.testing import TestClient

from trakr.app import app
from trakr.entities import reset_stores


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset stores before each test."""
    reset_stores()
    yield
    reset_stores()


class TestClientCommands:
    """Tests for client management commands."""

    @pytest.mark.asyncio
    async def test_create_client_success(self):
        """Test creating a client with valid data."""
        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name="Acme Corp",
                email="contact@acme.com",
                hourly_rate=150.0,
            )

            assert result.id == 1
            assert result.name == "Acme Corp"
            assert result.email == "contact@acme.com"
            assert float(result.hourly_rate) == 150.0

    @pytest.mark.asyncio
    async def test_create_client_strips_whitespace(self):
        """Test that client names are trimmed."""
        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name="  Acme Corp  ",
            )

            assert result.name == "Acme Corp"

    @pytest.mark.asyncio
    async def test_create_client_empty_name_fails(self):
        """Test that empty names are rejected."""
        async with TestClient(app) as client:
            with pytest.raises(Exception) as exc_info:
                await client.invoke(
                    "create_client",
                    name="   ",  # Only whitespace
                )

            assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_client_not_found(self):
        """Test updating non-existent client."""
        from hive.errors import CommandError

        async with TestClient(app) as client:
            with pytest.raises(CommandError) as exc_info:
                await client.invoke(
                    "update_client",
                    client_id=999,
                    name="New Name",
                )

            assert "not found" in str(exc_info.value).lower()


class TestTimeCommands:
    """Tests for time tracking commands."""

    @pytest.fixture
    async def setup_project(self):
        """Create a client and project for testing."""
        async with TestClient(app) as client:
            await client.invoke("create_client", name="Test Client")
            await client.invoke(
                "create_project",
                client_id=1,
                name="Test Project",
            )

    @pytest.mark.asyncio
    async def test_start_timer_creates_running_entry(self, setup_project):
        """Test starting a timer."""
        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start timer
            result = await client.invoke(
                "start_timer",
                project_id=1,
                description="Working on feature",
            )

            assert result.is_running
            assert result.description == "Working on feature"
            assert result.project_id == 1

    @pytest.mark.asyncio
    async def test_stop_timer_ends_running_entry(self, setup_project):
        """Test stopping a running timer."""
        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")
            await client.invoke(
                "start_timer",
                project_id=1,
                description="Working",
            )

            # Stop
            result = await client.invoke("stop_timer")

            assert result is not None
            assert not result.is_running
            assert result.ended_at is not None

    @pytest.mark.asyncio
    async def test_stop_timer_when_none_running(self):
        """Test stopping when no timer is running."""
        async with TestClient(app) as client:
            result = await client.invoke("stop_timer")

            assert result is None

    @pytest.mark.asyncio
    async def test_start_timer_stops_previous(self, setup_project):
        """Test that starting a new timer stops the previous one."""
        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start first timer
            first = await client.invoke(
                "start_timer",
                project_id=1,
                description="First task",
            )

            # Start second timer
            second = await client.invoke(
                "start_timer",
                project_id=1,
                description="Second task",
            )

            # Verify first is stopped
            from trakr.entities import get_store
            entries = get_store("time_entry")
            first_entry = entries[first.id]

            assert not first_entry.is_running
            assert second.is_running


class TestQueryCaching:
    """Tests for query caching behavior."""

    @pytest.mark.asyncio
    async def test_list_clients_cached(self):
        """Test that list_clients returns cached results."""
        async with TestClient(app) as client:
            # Create a client
            await client.invoke("create_client", name="Test")

            # Query twice
            first = await client.query("list_clients")
            second = await client.query("list_clients")

            # Both should return the same data
            assert len(first) == len(second)
            assert first[0].id == second[0].id
```

### 7.2 Property-Based Testing

Create `tests/test_properties.py`:

```python
"""Property-based tests for Trakr.

Demonstrates Hypothesis integration for thorough testing.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from hive.testing import TestClient, strategy_for_type
from hive.types import NonEmptyStr, NonNegativeFloat, PositiveInt

from trakr.app import app
from trakr.entities import reset_stores


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset stores before each test."""
    reset_stores()
    yield


class TestClientProperties:
    """Property-based tests for client commands."""

    @given(
        name=strategy_for_type(NonEmptyStr),
        rate=strategy_for_type(NonNegativeFloat),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_create_client_always_strips_name(
        self,
        name: str,
        rate: float,
    ):
        """Property: Created client name has no leading/trailing whitespace."""
        reset_stores()  # Reset between examples

        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name=name,
                hourly_rate=rate,
            )

            # Property: name is trimmed
            assert result.name == result.name.strip()
            # Property: name equals trimmed input
            assert result.name == name.strip()

    @given(
        name=strategy_for_type(NonEmptyStr),
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_created_client_has_positive_id(self, name: str):
        """Property: Created clients always have positive IDs."""
        reset_stores()

        async with TestClient(app) as client:
            result = await client.invoke("create_client", name=name)

            assert result.id > 0


class TestTimeEntryProperties:
    """Property-based tests for time entries."""

    @given(
        description=strategy_for_type(NonEmptyStr),
        tags=st.lists(st.text(min_size=1, max_size=20), max_size=5),
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_started_timer_is_always_running(
        self,
        description: str,
        tags: list[str],
    ):
        """Property: A just-started timer is always in running state."""
        reset_stores()

        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start timer
            result = await client.invoke(
                "start_timer",
                project_id=1,
                description=description,
                tags=tags,
            )

            # Property: timer is running
            assert result.is_running
            assert result.ended_at is None

    @given(
        count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=10)
    @pytest.mark.asyncio
    async def test_only_one_timer_runs_at_a_time(self, count: int):
        """Property: At most one timer can be running at any time."""
        reset_stores()

        async with TestClient(app) as client:
            # Setup
            await client.invoke("create_client", name="Test")
            await client.invoke("create_project", client_id=1, name="Proj")

            # Start multiple timers
            for i in range(count):
                await client.invoke(
                    "start_timer",
                    project_id=1,
                    description=f"Task {i}",
                )

            # Count running timers
            entries = await client.query("list_time_entries", days=1)
            running = [e for e in entries if e.is_running]

            # Property: at most one running
            assert len(running) <= 1


class TestInvariantProperties:
    """Tests for data invariants."""

    @given(
        rate=strategy_for_type(NonNegativeFloat),
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_client_rate_never_negative(self, rate: float):
        """Property: Client hourly rate is never negative."""
        reset_stores()

        async with TestClient(app) as client:
            result = await client.invoke(
                "create_client",
                name="Test",
                hourly_rate=rate,
            )

            assert float(result.hourly_rate) >= 0
```

**Key Testing Concepts:**

1. **TestClient** - High-level test interface with `invoke()` and `query()` methods.

2. **strategy_for_type()** - Generates test data from refinement types.

3. **Property-Based Testing** - Tests invariants that should always hold.

4. **Fixtures** - `reset_stores()` ensures test isolation.

## Part 8: Running the Application

### 8.1 Entry Points

Update `src/trakr/__init__.py`:

```python
"""Trakr - Personal project and time tracking.

A Hive application demonstrating CLI, TUI, and REST interfaces.
"""

from trakr.app import app

# Import modules to register decorators
from trakr import commands  # noqa: F401
from trakr import queries  # noqa: F401
from trakr import screens  # noqa: F401
from trakr import services  # noqa: F401

__all__ = ["app"]
```

### 8.2 CLI Usage

```bash
# Start the CLI
uv run trakr --help

# Create a client
uv run trakr create-client "Acme Corp" --hourly-rate 150

# Create a project
uv run trakr create-project 1 "Website Redesign" --budget-hours 40

# Start tracking time
uv run trakr start 1 "Implementing login page" --tags frontend,auth

# Check current timer
uv run trakr current

# Stop timer
uv run trakr stop

# List time entries
uv run trakr list-time-entries --days 7

# Get summary
uv run trakr get-time-summary --days 30

# JSON output for scripts
uv run trakr list-projects --json | jq '.[] | .name'
```

### 8.3 TUI Mode

```bash
# Launch the TUI
uv run trakr tui

# Or using hive dev for hot reload
uv run hive dev --interfaces tui
```

### 8.4 REST API

```bash
# Start REST server
uv run hive serve --port 8000 --reload

# Or with authentication
uv run hive serve --auth api_key

# Access endpoints
curl http://localhost:8000/clients
curl -X POST http://localhost:8000/clients -d '{"name": "Test"}'

# OpenAPI docs at /docs
open http://localhost:8000/docs
```

### 8.5 MCP Server

```bash
# Start MCP server (stdio transport)
uv run hive mcp serve

# Or SSE for web clients
uv run hive mcp serve --transport sse --port 8080
```

## Part 9: Next Steps

You've built a complete Hive application. Here are ways to extend it:

### 9.1 Add Invoice Generation

```python
@command(app)
@requires(lambda _ctx, client_id, **_kw: client_id > 0)
async def generate_invoice(
    ctx: ExecutionContext,
    client_id: PositiveInt,
    from_date: datetime,
    to_date: datetime,
) -> Invoice:
    """Generate an invoice for billable time in a date range."""
    ...
```

### 9.2 Add Reports

```python
@query(app)
async def monthly_report(
    ctx: ExecutionContext,
    year: int,
    month: int,
) -> Report:
    """Generate a monthly time and billing report."""
    ...
```

### 9.3 Add More Services

```python
@service(app, credentials="keyring:jira")
def jira_client(credentials: str) -> JiraClient:
    """Jira integration for syncing time to work logs."""
    ...
```

### 9.4 Export to JSON Schema

```bash
# Export the API specification
uv run hive spec export -o trakr-spec.json

# Check for breaking changes
uv run hive spec diff v1.json v2.json --fail-on-breaking
```

## Summary

In this tutorial, you built a complete time tracking application that demonstrates:

| Feature | Implementation |
|---------|----------------|
| Data modeling | Dataclasses with computed properties |
| Commands | `@command` with `@requires`/`@ensures` contracts |
| Queries | `@query` with caching and filtering |
| Services | `@service` with credential management |
| Validation | Refinement types (`PositiveInt`, `NonEmptyStr`) |
| TUI | `@screen` with reactive data binding |
| Testing | `TestClient` and property-based testing |
| Multiple interfaces | CLI, TUI, REST, MCP from same code |

The complete source code is available in `examples/trakr/`.

## Appendix: Quick Reference

### Decorators

```python
@command(app, entities=[Task], name="add", aliases=["create"])
@query(app, cache_ttl=300, entities=[Task])
@entity(app)
@screen(app, default=True, keybinding="d", queries=["list_items"])
@service(app, credentials="env:API_KEY")
```

### Contracts

```python
@requires(lambda ctx, x: x > 0, "x must be positive")
@ensures(lambda ctx, x, result: result.id is not None, "must have ID")
@invariant(lambda self: self.start < self.end, "start must be before end")
```

### Refinement Types

```python
from hive.types import (
    PositiveInt, NonNegativeInt, NegativeInt,
    PositiveFloat, NonNegativeFloat,
    UnitInterval, Percentage, Probability,
    Port, HttpStatusCode,
    NonEmptyStr, TrimmedStr, Identifier, Slug, Email, Url,
)
```

### Testing

```python
from hive.testing import TestClient, MockExecutionContext, strategy_for_type

async with TestClient(app, services={"api": mock}) as client:
    result = await client.invoke("command_name", arg=value)
    data = await client.query("query_name", filter=value)
```
