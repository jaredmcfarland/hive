# Design

Hive is built on a three-layer architecture that separates specification, generation, and execution concerns. This design enables a single decorated Python codebase to generate multiple interfaces (CLI, TUI, REST, MCP) while maintaining consistency and type safety.

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SPECIFICATION LAYER                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │@command │  │ @query  │  │ @entity │  │ @screen │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                          │                                      │
│                    ApplicationRegistry                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                     FRAMEWORK CORE                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Generators                          │   │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌──────┐          │   │
│  │  │ CLI │  │ TUI │  │ MCP │  │REST │  │Schema│          │   │
│  │  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬───┘          │   │
│  └─────┼────────┼───────┼────────┼────────┼────────────────┘   │
└────────┼────────┼───────┼────────┼────────┼─────────────────────┘
         │        │       │        │        │
┌────────┼────────┼───────┼────────┼────────┼─────────────────────┐
│        ▼        ▼       ▼        ▼        ▼                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   RUNTIME LAYER                          │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │              ExecutionContext                     │   │   │
│  │  │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐  │   │   │
│  │  │  │ctx.db  │ │ctx.config│ │ctx.out │ │ctx.svc │  │   │   │
│  │  │  └────────┘ └──────────┘ └────────┘ └────────┘  │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                       RUNTIME LAYER                             │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. Specification Layer

The specification layer captures application intent through Python decorators. Functions and classes are registered at import time, creating a complete specification of the application's capabilities.

**Core Decorators:**

| Decorator | Purpose | Example |
|-----------|---------|---------|
| `@command(app)` | State-modifying operations | Create, update, delete |
| `@query(app)` | Read-only operations | List, get, search |
| `@entity(app)` | Data models (SQLModel) | Task, User, Project |
| `@screen(app)` | TUI screens (Textual) | Dashboard, Editor |
| `@service(app)` | External API clients | GitHub, Slack |

**Example:**

```python
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr

app = App("taskmanager")

@entity(app)
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: NonEmptyStr
    priority: PositiveInt = 1

@command(app, entities=[Task])
async def create_task(ctx, title: NonEmptyStr, priority: PositiveInt = 1) -> Task:
    """Create a new task."""
    task = Task(title=title, priority=priority)
    ctx.db.add(task)
    return task

@query(app, entities=[Task])
async def list_tasks(ctx, limit: PositiveInt = 10) -> list[Task]:
    """List all tasks."""
    result = await ctx.db.exec(select(Task).limit(limit))
    return result.all()
```

### 2. Framework Core

The framework core consists of generators that read from the application registry and produce interfaces. Each generator is specialized for its target platform.

**Generator Responsibilities:**

| Generator | Input | Output |
|-----------|-------|--------|
| `CLIGenerator` | Registry | Typer application |
| `TUIGenerator` | Registry | Textual application |
| `MCPGenerator` | Registry | FastMCP server |
| `RESTGenerator` | Registry | FastAPI application |
| `SchemaGenerator` | Registry | JSON Schema |

**Generation Process:**

1. Read command/query registrations from registry
2. Extract parameter types and constraints
3. Build interface-specific representations
4. Generate runtime wrappers that invoke original functions

### 3. Runtime Layer

The runtime layer provides execution context to commands and queries. Every command receives a context object with access to database, configuration, services, and output formatting.

**Context Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `ctx.db` | `AsyncSession` | SQLAlchemy async session |
| `ctx.config` | `AppSettings` | Pydantic settings |
| `ctx.output` | `OutputFormatter` | Format-aware output |
| `ctx.services` | `ServiceProxy` | Lazy service access |

## Data Flow

```
User Input → Interface → Generator Wrapper → ExecutionContext → Command → Result
    │                                              │
    │                                              ├── ctx.db (database)
    │                                              ├── ctx.config (settings)
    │                                              └── ctx.services (APIs)
    │
    └── CLI: typer argument parsing
        TUI: Textual event handling
        REST: FastAPI request parsing
        MCP: Tool invocation parsing
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| CLI | Typer + Rich | Type-hint driven argument parsing, rich output |
| TUI | Textual | CSS-like styling, reactive data binding |
| Data | SQLModel | Pydantic + SQLAlchemy unified models |
| Database | SQLite (default) | Also supports DuckDB, PostgreSQL |
| MCP | FastMCP | Model Context Protocol server |
| REST | FastAPI | OpenAPI documentation, async support |
| Types | beartype | Runtime type enforcement |
| Contracts | deal | Design-by-contract decorators |
| Testing | Hypothesis | Property-based testing |

## Design Principles

### CLI-First Architecture

Every feature is designed to work from the command line first:

- **JSON Output**: Every command supports `--json` for machine parsing
- **Headless Operation**: Commands work without interactive prompts
- **Confirmation Bypass**: `--yes` flags for automation

### Specification-Driven Development

The decorated Python code is the single source of truth:

- All interfaces derive from the same specification
- JSON Schema export enables cross-language consumption
- Breaking changes are detectable via spec diffing

### Type Safety Throughout

Types flow from Python annotations to all interfaces:

```python
# Python type
priority: PositiveInt

# CLI: validated argument
--priority INTEGER  # with min=1 constraint

# REST: JSON Schema
{"type": "integer", "minimum": 1}

# MCP: Tool input schema
{"type": "integer", "minimum": 1}
```

### Layered Architecture Enforcement

Import restrictions are enforced via `import-linter`:

```
generators → runtime → core → contracts → types
```

- `hive.types` cannot import from `hive.core`, `hive.runtime`, or `hive.generators`
- `hive.contracts` cannot import from `hive.generators`
- This ensures clean dependencies and prevents circular imports
