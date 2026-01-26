"""Data entities for Trakr.

These SQLModel classes define the database schema. Each class with
`table=True` becomes a table. Hive's `@entity` decorator registers
them for CLI introspection and schema generation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from hive import entity
from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel

from trakr.app import app

if TYPE_CHECKING:
    pass  # Forward references handled via string literals


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

    @computed_field
    @property
    def effective_rate(self) -> Decimal:
        """Get the effective hourly rate (project override or client default).

        Note: Only returns the project's rate. Use get_effective_rate() in queries
        to include client fallback (requires relationship to be loaded).
        """
        return self.hourly_rate if self.hourly_rate is not None else Decimal("0.00")

    def get_effective_rate(self, client_rate: Decimal | None = None) -> Decimal:
        """Get effective rate with optional client fallback.

        Args:
            client_rate: Client's hourly rate as fallback.

        Returns:
            Project rate if set, otherwise client_rate, otherwise 0.
        """
        if self.hourly_rate is not None:
            return self.hourly_rate
        if client_rate is not None:
            return client_rate
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
    status: TimeEntryStatus = Field(default=TimeEntryStatus.DRAFT, description="/Billing status")

    # Relationships
    project: Project | None = Relationship(back_populates="time_entries")

    @computed_field
    @property
    def duration_hours(self) -> float:
        """Calculate duration in hours."""
        end = self.ended_at if self.ended_at else datetime.now()
        delta = end - self.started_at
        return delta.total_seconds() / 3600

    @computed_field
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
