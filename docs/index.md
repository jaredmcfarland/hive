# Hive Framework

A Python framework for building terminal-agent-native applications.

!!! tip "AI-Friendly Documentation"
    For LLM-optimized documentation, visit [DeepWiki](https://deepwiki.com/jaredmcfarland/hive) which provides structured context designed for AI assistants.

## Why This Exists

Hive lets you write decorated Python code once and generate multiple interfaces automatically:

- **CLI** via Typer with Rich formatting
- **TUI** via Textual with reactive widgets
- **REST API** via FastAPI with OpenAPI docs
- **MCP Server** via FastMCP for AI agent integration

No boilerplate duplication. One specification, many outputs.

## Quick Example

```python
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr
from sqlmodel import Field

app = App("tasks")

@entity(app)
class Task:
    """A task to be completed."""
    id: int | None = Field(default=None, primary_key=True)
    title: NonEmptyStr = Field(description="Task title")
    priority: PositiveInt = Field(default=1, description="Priority level")
    done: bool = Field(default=False)

@command(app, entities=[Task])
async def create(ctx, title: NonEmptyStr, priority: PositiveInt = 1) -> Task:
    """Create a new task."""
    task = Task(title=title, priority=priority)
    ctx.db.add(task)
    await ctx.db.commit()
    return task

@query(app, entities=[Task], cache_ttl=60)
async def list_tasks(ctx, include_done: bool = False) -> list[Task]:
    """List all tasks."""
    query = select(Task)
    if not include_done:
        query = query.where(Task.done == False)
    return await ctx.db.exec(query).all()
```

This single file generates:

```bash
# CLI
hive tasks create "Write docs" --priority 2
hive tasks list-tasks --json

# REST API endpoints
POST /tasks/create
GET /tasks/list-tasks?include_done=false

# MCP tools for AI agents
tasks_create, tasks_list_tasks
```

## Capabilities

### Commands and Queries

Commands modify state. Queries read state. Both get CLI arguments, REST endpoints, and MCP tools automatically.

```python
@command(app)
async def complete(ctx, task_id: PositiveInt) -> Task:
    """Mark a task as done."""
    task = await ctx.db.get(Task, task_id)
    task.done = True
    await ctx.db.commit()
    return task

@query(app, cache_ttl=300)
async def stats(ctx) -> dict:
    """Get task statistics."""
    return {"total": await ctx.db.count(Task)}
```

### Entities

SQLModel-based data models with Pydantic validation:

```python
@entity(app)
class Project:
    id: int | None = Field(default=None, primary_key=True)
    name: NonEmptyStr
    tasks: list[Task] = Relationship(back_populates="project")
```

### Services

External API clients with credential management:

```python
@service(app, credentials="keyring:github")
class GitHubClient:
    """GitHub API client."""

    async def list_issues(self, repo: str) -> list[Issue]:
        ...
```

### Screens (TUI)

Textual screens for interactive terminal UIs:

```python
@screen(app, default=True, keybinding="t")
class TaskListScreen:
    """Main task list view."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="tasks")
        yield Footer()
```

### Verification Stack

Three layers of runtime validation:

```python
from hive.types import PositiveInt, Email, Percentage
from hive.contracts import requires, ensures

@command(app)
@requires(lambda ctx, pct: 0 <= pct <= 100, "Percentage must be 0-100")
@ensures(lambda ctx, pct, result: result.progress == pct)
async def set_progress(ctx, task_id: PositiveInt, pct: Percentage) -> Task:
    ...
```

## For Humans and Agents

Hive follows CLI-first design principles:

- Every command supports `--json` for machine-readable output
- Commands work headlessly without interactive prompts
- `--yes` flags bypass confirmations for automation
- Structured errors with exit codes

```bash
# Human-friendly
$ hive tasks list-tasks
┌────┬─────────────┬──────────┐
│ ID │ Title       │ Priority │
├────┼─────────────┼──────────┤
│ 1  │ Write docs  │ 2        │
│ 2  │ Add tests   │ 1        │
└────┴─────────────┴──────────┘

# Agent-friendly
$ hive tasks list-tasks --json
[{"id": 1, "title": "Write docs", "priority": 2}, ...]
```

## LLM-Optimized Documentation

This documentation follows the [llms.txt](https://llmstxt.org/) specification for AI-friendly content:

- [`/llms.txt`](/llms.txt) - Documentation index for LLMs
- [`/llms-full.txt`](/llms-full.txt) - Complete documentation in single file

## Next Steps

<div class="grid cards" markdown>

-   :material-download: **[Installation](getting-started/installation.md)**

    Install Hive and set up your development environment

-   :material-rocket-launch: **[Quick Start](getting-started/quickstart.md)**

    Build your first Hive application in 5 minutes

-   :material-api: **[API Reference](api/index.md)**

    Complete API documentation for all modules

-   :material-console: **[CLI Reference](cli/index.md)**

    Command-line interface documentation

</div>
