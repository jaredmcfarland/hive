# Entities

Entities are SQLModel classes that define database tables. They combine Pydantic validation with SQLAlchemy ORM capabilities, providing a unified data model for your application.

## Basic Usage

Use the `@entity` decorator to register a SQLModel class:

```python
from hive import App, entity
from sqlmodel import SQLModel, Field

app = App("tasks")

@entity(app)
class Task(SQLModel, table=True):
    """A task in the system."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(description="Task title")
    completed: bool = Field(default=False, description="Completion status")
```

## Field Definitions

Use `Field()` to configure field behavior and add metadata:

```python
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field

@entity(app)
class Task(SQLModel, table=True):
    """A task with full metadata."""

    # Primary key (auto-generated)
    id: int | None = Field(default=None, primary_key=True)

    # Required field with description
    title: str = Field(description="Task title", min_length=1, max_length=200)

    # Optional field with default
    description: str | None = Field(default=None, description="Detailed description")

    # Field with default value
    priority: int = Field(default=1, ge=1, le=5, description="Priority 1-5")

    # Boolean with default
    completed: bool = Field(default=False, description="Completion status")

    # Timestamp with factory default
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp"
    )

    # Indexed field for faster lookups
    status: str = Field(default="pending", index=True, description="Task status")
```

### Field Parameters

| Parameter | Description |
|-----------|-------------|
| `default` | Default value for the field |
| `default_factory` | Function that returns default value |
| `primary_key` | Mark as primary key |
| `index` | Create database index |
| `unique` | Enforce unique constraint |
| `nullable` | Allow NULL values (inferred from type) |
| `description` | Human-readable description |
| `min_length`, `max_length` | String length constraints |
| `ge`, `gt`, `le`, `lt` | Numeric constraints |

## Relationships

Define relationships between entities using foreign keys and `Relationship`:

```python
from sqlmodel import SQLModel, Field, Relationship

@entity(app)
class Project(SQLModel, table=True):
    """A project containing tasks."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(description="Project name")

    # One-to-many: project has many tasks
    tasks: list["Task"] = Relationship(back_populates="project")


@entity(app)
class Task(SQLModel, table=True):
    """A task belonging to a project."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(description="Task title")

    # Foreign key to project
    project_id: int | None = Field(default=None, foreign_key="project.id")

    # Many-to-one: task belongs to project
    project: Project | None = Relationship(back_populates="tasks")
```

### Relationship Types

#### One-to-Many

```python
@entity(app)
class Author(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    # One author has many books
    books: list["Book"] = Relationship(back_populates="author")


@entity(app)
class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author_id: int | None = Field(default=None, foreign_key="author.id")

    # Many books belong to one author
    author: Author | None = Relationship(back_populates="books")
```

#### Many-to-Many

```python
@entity(app)
class TaskTagLink(SQLModel, table=True):
    """Association table for task-tag many-to-many."""

    task_id: int | None = Field(
        default=None, foreign_key="task.id", primary_key=True
    )
    tag_id: int | None = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )


@entity(app)
class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    tasks: list["Task"] = Relationship(
        back_populates="tags", link_model=TaskTagLink
    )


@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str

    tags: list[Tag] = Relationship(
        back_populates="tasks", link_model=TaskTagLink
    )
```

## Using Entities in Commands and Queries

### Creating Records

```python
@command(app, entities=[Task])
async def add(ctx, title: str, project_id: int | None = None) -> Task:
    """Add a new task."""
    task = Task(title=title, project_id=project_id)
    ctx.db.add(task)
    await ctx.db.commit()
    await ctx.db.refresh(task)  # Load auto-generated fields
    return task
```

### Reading Records

```python
@query(app, entities=[Task])
async def get_task(ctx, task_id: int) -> Task | None:
    """Get a task by ID."""
    return await ctx.db.get(Task, task_id)

@query(app, entities=[Task])
async def list_tasks(ctx) -> list[Task]:
    """List all tasks."""
    result = await ctx.db.execute(select(Task))
    return result.scalars().all()
```

### Updating Records

```python
@command(app, entities=[Task])
async def complete(ctx, task_id: int) -> Task:
    """Mark a task as complete."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task {task_id} not found")

    task.completed = True
    await ctx.db.commit()
    return task
```

### Deleting Records

```python
@command(app, entities=[Task])
async def delete(ctx, task_id: int) -> None:
    """Delete a task."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task {task_id} not found")

    await ctx.db.delete(task)
    await ctx.db.commit()
```

## Validation

SQLModel combines Pydantic validation with database constraints:

```python
from pydantic import field_validator

@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    priority: int = Field(ge=1, le=5, default=1)
    email: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and "@" not in v:
            raise ValueError("Invalid email address")
        return v
```

!!! tip "Validation Timing"
    Pydantic validation runs when creating model instances (in Python).
    Database constraints are enforced when committing to the database.

## Table Configuration

Customize table names and other SQLAlchemy options:

```python
@entity(app)
class Task(SQLModel, table=True):
    __tablename__ = "tasks"  # Custom table name
    __table_args__ = (
        UniqueConstraint("project_id", "title", name="unique_task_per_project"),
    )

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    title: str
```

## Best Practices

!!! success "Do"
    - Add descriptions to all fields for documentation
    - Use appropriate field constraints (`min_length`, `ge`, etc.)
    - Define relationships explicitly with `back_populates`
    - Create indexes for frequently queried fields
    - Use `datetime.now(UTC)` for timestamps (not naive datetimes)

!!! failure "Don't"
    - Store sensitive data without encryption
    - Use mutable default values (use `default_factory`)
    - Skip primary keys
    - Create circular imports between entity files

## Database Migrations

!!! note "Future Feature"
    Automatic migration generation is planned for a future release.
    Currently, use Alembic directly for schema migrations.

```python
# Generate migration
alembic revision --autogenerate -m "Add task priority"

# Apply migration
alembic upgrade head
```
