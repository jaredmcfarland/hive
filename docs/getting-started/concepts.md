# Core Concepts

Hive is built on a specification-driven architecture where your decorated Python code
serves as the single source of truth for all generated interfaces.

## Three-Layer Architecture

Hive separates concerns into three distinct layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SPECIFICATION LAYER                          │
│  @entity, @command, @query, @screen, @service decorators        │
│  Python code with type hints = your specification               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FRAMEWORK CORE                              │
│  Generators: CLI (Typer), TUI (Textual), MCP, REST, Schema      │
│  Reads registry → produces interfaces                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RUNTIME LAYER                              │
│  ExecutionContext: ctx.db, ctx.services, ctx.config, ctx.output │
│  Provides resources to commands and queries                     │
└─────────────────────────────────────────────────────────────────┘
```

### Specification Layer

Your decorated Python code defines what your application does. At import time, Hive
registers all decorated functions and classes:

```python
@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str

@command(app, entities=[Task])
async def add(ctx, title: str) -> Task:
    """Add a new task."""
    ...
```

!!! info "Single Source of Truth"
    The specification layer is the authoritative definition of your application.
    All interfaces (CLI, TUI, MCP, REST) are generated from this single source.

### Framework Core

Generators read the specification registry and produce different interfaces:

| Generator | Output | Technology |
|-----------|--------|------------|
| CLI | Command-line interface | Typer + Rich |
| TUI | Terminal user interface | Textual |
| MCP | Model Context Protocol server | FastMCP |
| REST | RESTful API | FastAPI |
| Schema | JSON Schema specification | Pydantic |

### Runtime Layer

When commands execute, they receive an `ExecutionContext` providing access to
resources. See [Execution Context](#execution-context) below.

## Decorators

Hive uses decorators to register components with the application.

### @entity

Defines database models using SQLModel:

```python
from hive import entity, App
from sqlmodel import SQLModel, Field
from typing import Optional

app = App("myapp")

@entity(app)
class User(SQLModel, table=True):
    """A user in the system."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, description="User's email address")
    name: str = Field(description="Display name")
    active: bool = Field(default=True, description="Whether user can log in")
```

!!! tip "SQLModel Integration"
    Entities use SQLModel, which combines Pydantic validation with SQLAlchemy ORM.
    This gives you type-safe models that work for both API validation and database operations.

### @command

Defines state-modifying operations:

```python
from hive import command
from hive.types import NonEmptyStr, PositiveInt

@command(app, entities=[User])
async def create_user(ctx, email: str, name: NonEmptyStr) -> User:
    """Create a new user.

    Args:
        ctx: Execution context
        email: User's email address
        name: Display name (cannot be empty)

    Returns:
        The created user
    """
    user = User(email=email, name=name)
    ctx.db.add(user)
    await ctx.db.commit()
    return user
```

Commands:

- Can modify database state
- Support refinement types for validation
- Generate CLI commands with proper argument parsing
- Return values are serialized for `--json` output

### @query

Defines read-only operations with optional caching:

```python
@query(app, entities=[User], cache_ttl=60)
async def get_user(ctx, user_id: PositiveInt) -> User | None:
    """Get a user by ID.

    Results are cached for 60 seconds.

    Args:
        ctx: Execution context
        user_id: The user's ID (must be positive)

    Returns:
        The user if found, None otherwise
    """
    return await ctx.db.get(User, user_id)
```

Queries:

- Are read-only (should not modify state)
- Support `cache_ttl` for automatic caching
- Generate CLI commands like commands
- Can be called from commands or other queries

### @screen

Defines Textual TUI screens:

```python
from hive import screen
from textual.widgets import DataTable

@screen(app, default=True, keybinding="u")
class UserListScreen:
    """Display all users in a table.

    Press 'u' from any screen to access this view.
    """

    async def compose(self, ctx):
        table = DataTable()
        table.add_columns("ID", "Email", "Name", "Active")

        users = await ctx.db.exec(select(User))
        for user in users:
            table.add_row(user.id, user.email, user.name, user.active)

        yield table
```

Screen options:

- `default=True` - Show this screen on startup
- `keybinding="x"` - Global keyboard shortcut to access screen

### @service

Defines external API clients with credential management:

```python
from hive import service
import httpx

@service(app, credentials="keyring:github")
class GitHubService:
    """GitHub API client.

    Credentials are stored securely in the system keyring.
    """

    def __init__(self, token: str):
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={"Authorization": f"token {token}"}
        )

    async def get_user(self, username: str) -> dict:
        """Get a GitHub user's profile."""
        response = await self.client.get(f"/users/{username}")
        return response.json()
```

Services:

- Support secure credential storage via keyring
- Are lazily loaded on first access
- Available via `ctx.services.<name>`

## Execution Context

Every command and query receives an `ExecutionContext` as its first argument:

```python
@command(app, entities=[Task])
async def example(ctx, task_id: int) -> Task:
    # Database access
    task = await ctx.db.get(Task, task_id)

    # Service access (lazy-loaded)
    github_user = await ctx.services.github.get_user("octocat")

    # Configuration access
    debug_mode = ctx.config.debug

    # Format-aware output
    ctx.output.success("Operation completed")
    ctx.output.table([task])  # Renders as table or JSON based on --json flag

    return task
```

### ctx.db

Async SQLModel session for database operations:

```python
# Get by primary key
user = await ctx.db.get(User, user_id)

# Execute queries
from sqlmodel import select
statement = select(User).where(User.active == True)
result = await ctx.db.exec(statement)
users = result.all()

# Add and commit
ctx.db.add(new_user)
await ctx.db.commit()
```

### ctx.services

Lazy-loaded service clients. Services are instantiated on first access:

```python
# First access initializes the service
user_data = await ctx.services.github.get_user("username")

# Subsequent accesses reuse the instance
repos = await ctx.services.github.list_repos()
```

### ctx.config

Pydantic Settings for configuration with environment variable support:

```python
# Access configuration values
if ctx.config.debug:
    ctx.output.warning("Debug mode enabled")

database_url = ctx.config.database_url
```

### ctx.output

Format-aware output that respects `--json` flag:

```python
# These render as Rich console output normally,
# or as JSON when --json flag is used
ctx.output.success("Task created")
ctx.output.error("Task not found")
ctx.output.warning("Task already completed")
ctx.output.table(tasks)  # Rich table or JSON array
```

## CLI-First Design

Hive follows CLI-first principles for agent-friendly applications:

### Machine-Readable Output

Every command supports `--json` for programmatic consumption:

```bash
# Human-readable (default)
myapp list-users
# ┌────┬─────────────────┬───────┐
# │ ID │ Email           │ Name  │
# ├────┼─────────────────┼───────┤
# │ 1  │ alice@test.com  │ Alice │
# └────┴─────────────────┴───────┘

# Machine-readable
myapp list-users --json
# [{"id": 1, "email": "alice@test.com", "name": "Alice"}]
```

### Headless Operation

Commands work without interactive prompts. Use flags for automation:

```bash
# Non-interactive deletion
myapp delete-user 1 --yes

# Batch operations in scripts
for id in $(myapp list-users --json | jq -r '.[].id'); do
    myapp deactivate-user "$id" --yes
done
```

### Consistent Error Handling

Errors return proper exit codes and structured error messages:

```bash
myapp get-user 999
# Error: User 999 not found
# Exit code: 1

myapp get-user 999 --json
# {"error": "User 999 not found", "code": "NOT_FOUND"}
# Exit code: 1
```

!!! tip "Agent Integration"
    The CLI-first design makes Hive applications easy to integrate with:

    - Shell scripts and automation
    - AI agents (Claude, GPT, etc.)
    - CI/CD pipelines
    - Monitoring and orchestration tools

## Next Steps

Now that you understand Hive's architecture:

- [Installation](installation.md) - Set up your development environment
- [Quick Start](quickstart.md) - Build your first application
- [Contracts](../api/contracts.md) - Add pre/post conditions and validation
- [Testing](../api/testing.md) - Property-based testing strategies
