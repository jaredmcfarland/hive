# Hive: A Framework for Terminal-Agent-Native Python Applications

**Project Specification Document**

Version 0.2.0 | January 2026

---

## Executive Summary

Hive is a Python framework for building terminal-native applications that serve three distinct consumers from a single specification: command-line interfaces for agents and power users, terminal user interfaces for interactive human use, and programmatic Python APIs for developer integration. The framework follows a "define once, expose three ways" philosophy, enabling developers to write application logic once and automatically generate consistent interfaces across all access patterns.

Hive draws architectural inspiration from Wasp, a full-stack web application framework that uses a domain-specific language to generate React frontends and Node.js backends from a single specification. Where Wasp targets web applications with React and Node.js, Hive targets terminal applications with Typer, Rich, and Textual. Where Wasp provides full-stack type safety between client and server, Hive provides interface consistency between CLI, TUI, and Python API.

**What's New in v0.2.0**: This version introduces a comprehensive verification stack integrating beartype, deal, and Hypothesis. Type hints become executable contracts with automatic validation and test generation. Refinement types (like `PositiveInt`, `Port`, `Email`) provide semantic constraints that are enforced at runtime and propagate to CLI validation, JSON Schema export, and property-based testing.

The framework is designed for the emerging category of "terminal-agent-native" software—applications primarily consumed by AI agents operating through command-line tools (such as Claude Code's bash tool) while remaining fully accessible to human users through both command-line and graphical terminal interfaces.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Core Philosophy](#core-philosophy)
3. [Architecture Overview](#architecture-overview)
4. [Verification Stack](#verification-stack)
5. [Specification System Design](#specification-system-design)
6. [Execution Context](#execution-context)
7. [CLI Generation](#cli-generation)
8. [TUI Generation](#tui-generation)
9. [MCP Server Generation](#mcp-server-generation-optional)
10. [REST API Generation](#rest-api-generation-optional)
11. [Specification Export](#specification-export)
12. [Project Structure](#project-structure)
13. [CLI Tooling](#cli-tooling)
14. [Testing Support](#testing-support)
15. [Conformance-Driven Specification](#conformance-driven-specification-cds)
16. [Implementation Status](#implementation-status)
17. [Open Questions](#open-questions)
18. [Appendix: Complete Example](#appendix-complete-example)

---

## Problem Statement

Modern terminal applications increasingly serve multiple audiences with different interaction patterns. A data toolkit might be invoked by an AI agent through structured CLI commands, explored interactively by a human through a TUI dashboard, and integrated programmatically by a developer through Python imports. Building and maintaining three consistent interfaces for the same underlying functionality presents significant challenges.

The current approach requires developers to manually synchronize command-line argument parsers, TUI screen layouts, and Python function signatures. Changes to the underlying data model or business logic must be propagated across all three interfaces, leading to inconsistencies, duplicated code, and maintenance burden. Documentation for each interface must be written and maintained separately.

Furthermore, as AI agents become primary consumers of command-line tools, applications must be designed with agent ergonomics in mind from the start. This includes structured output formats, predictable command patterns, and machine-readable documentation. Retrofitting these concerns onto human-first designs is difficult and error-prone.

**Additionally, traditional type hints serve only as documentation**—they describe constraints but don't enforce them. A parameter typed as `int` accepts any integer, even when the domain requires positive values only. Validation logic must be written manually, kept in sync with documentation, and tested separately.

Hive addresses these challenges by establishing a single specification layer from which all interfaces are derived. The specification captures the essential semantics of commands, queries, data models, and screens. **Type hints become executable contracts**: refinement types like `PositiveInt` or `Port` are validated at runtime, generate appropriate CLI error messages, and inform property-based test generation.

---

## Core Philosophy

### The Triple Interface Paradigm (Plus Two)

Hive applications expose functionality through multiple interfaces, each optimized for its primary consumer. The three core interfaces serve the terminal-native use case; two additional interfaces extend reach when needed.

The **command-line interface** serves as the primary interface, designed for both AI agents and human power users. Every command supports structured output (JSON, CSV, table formats) enabling agents to parse results reliably. Commands are designed to be scriptable, composable, and headless by default, with optional interactive prompts for human convenience.

The **terminal user interface** provides a graphical experience within the terminal, designed for human exploration and interaction. Screens present information visually, support keyboard navigation, and expose commands through a searchable command palette. The TUI wraps the same underlying commands, providing a different interaction modality rather than different functionality.

The **Python API** provides direct programmatic access for developers integrating Hive applications into larger systems. Functions mirror command signatures with full type safety, enabling IDE autocomplete and static analysis. Async-first design supports high-performance integrations.

These three interfaces are always generated and constitute the core of every Hive application.

Two additional interfaces are available when applications need to extend beyond the terminal.

The **MCP server** (optional) exposes commands as tools for AI agents operating outside terminal environments (desktop applications, web-based assistants). This interface derives directly from the command specification with no additional development required. MCP enables AI assistants like Claude Desktop or ChatGPT to invoke Hive application commands through the standardized Model Context Protocol. Enable this when your application needs to integrate with non-terminal AI agents.

The **REST API** (optional) exposes commands as HTTP endpoints using FastAPI. This interface enables web integrations, webhooks, remote access from non-terminal contexts, and programmatic access from other programming languages. Enable this when your application needs HTTP accessibility.

Both optional interfaces are generated from the same command specification, ensuring consistency across all access patterns.

### Specification-Driven Development

Hive adopts principles from Conformance-Driven Specification (CDS), treating the decorated Python code as a machine-readable specification from which implementations are derived.

The specification captures command names, parameter types, return types, documentation, and relationships to data entities. From this specification, the framework generates CLI argument parsers, TUI screen registrations, Python function signatures, MCP tool definitions, JSON Schema exports, and documentation.

**Refinement types extend specifications beyond basic types**. Where traditional specifications might say "port: integer", Hive specifications say "port: Port" where Port carries semantic meaning (1-65535) that is enforced at runtime, documented in help text, exported to JSON Schema, and used to generate valid test inputs.

Because all interfaces derive from a single specification, they are guaranteed to be consistent. A change to a command's signature automatically propagates to all interfaces. Breaking changes can be detected by diffing specifications between versions.

### CLI-First Architecture

The command-line interface is the primary interface, reflecting the terminal-agent-native design philosophy. This has several implications for the framework design.

Every command must work headlessly without interactive prompts. Prompts are conveniences for human users, not requirements. Commands provide `--yes` flags for confirmation bypass and environment variable fallbacks for credentials.

Structured output is always available. Every command supports `--json` for machine-readable output, with `--table` and `--csv` alternatives. The JSON output represents the canonical response format; other formats are presentations of the same data.

Commands are designed for composition. They accept input from stdin where appropriate, produce clean output suitable for piping, and use conventional exit codes to signal success or failure.

**Validation errors are user-friendly**. When a refinement type constraint fails (e.g., port > 65535), the CLI displays a clear, actionable error message rather than a Python traceback.

---

## Architecture Overview

### Technology Stack

Hive builds upon a carefully selected set of Python libraries that share philosophical alignment and technical compatibility.

**Typer** serves as the CLI framework. Created by Sebastián Ramírez (author of FastAPI), Typer provides type-hint-driven argument parsing with automatic help generation. Its integration with Rich enables beautiful console output including tables, progress bars, and formatted panels.

**Rich** provides the console rendering layer. It handles text formatting, syntax highlighting, tables, trees, progress displays, and other visual elements. Typer uses Rich internally; Hive uses it for consistent output formatting across CLI and TUI contexts.

**Textual** provides the TUI framework. Also from the Textualize team (creators of Rich), Textual builds full terminal applications with widgets, layouts, and event handling. Its CSS-like styling system and reactive data binding enable sophisticated interfaces.

**SQLModel** provides the data layer. Created by Sebastián Ramírez, SQLModel combines Pydantic validation with SQLAlchemy's ORM capabilities. Models are simultaneously Pydantic schemas (for validation and serialization) and SQLAlchemy tables (for database operations).

**SQLite** serves as the default database. As the standard embedded database, SQLite provides zero-configuration persistence suitable for single-user terminal applications. The framework also supports DuckDB (for analytics-heavy workloads) and PostgreSQL (for networked deployments) through SQLAlchemy's dialect system.

**Pydantic Settings** handles configuration. Environment variables, configuration files, and command-line overrides are unified through typed settings classes with validation.

**httpx** provides HTTP client capabilities for applications integrating with external APIs. Its async support aligns with Hive's async-first design.

**keyring** provides secure credential storage, integrating with system keychains (macOS Keychain, Windows Credential Manager, Linux Secret Service).

**FastMCP** provides the MCP server implementation. Built as a higher-level abstraction over the official MCP Python SDK, FastMCP uses a decorator-based approach that mirrors Hive's design philosophy. Where the raw MCP SDK requires manual server setup, tool registration, and protocol handling, FastMCP enables declaring tools with simple decorators. This alignment with Hive's decorator patterns allows seamless MCP server generation from the command specification.

**FastAPI** (optional) provides REST API generation for applications requiring HTTP interfaces. Created by Sebastián Ramírez (author of Typer and SQLModel), FastAPI shares the same design philosophy: type hints drive behavior, decorators define routes, and Pydantic models handle validation. When enabled, Hive generates a FastAPI application exposing commands as HTTP endpoints, enabling web integrations, webhooks, and cross-language access. This interface is opt-in to keep simple terminal applications simple.

#### Verification Stack

The verification stack transforms type hints from documentation into executable contracts:

**beartype** (>=0.18.0) provides runtime type enforcement with near-zero overhead (~1-10μs per call). Its `Annotated` type support enables refinement types—types with logical constraints like "integer > 0" or "string matching email pattern". beartype validates these constraints at function boundaries, catching invalid inputs immediately.

**deal** (>=4.24.0) implements Design by Contract with pre/post conditions and invariants. It enables explicit specification of function requirements (`@deal.pre`) and guarantees (`@deal.post`). For framework internals, deal provides invariants that catch invalid state transitions.

**Hypothesis** (>=6.100.0, dev dependency) provides property-based testing. Combined with the verification stack, Hypothesis can automatically generate valid test inputs from refinement type constraints. The `deal.cases` integration generates tests directly from contracts.

### System Architecture

The Hive runtime operates in four layers.

The **specification layer** contains the decorated Python code defining commands, queries, entities, screens, and services. At import time, decorators register these definitions with the central application registry, building an in-memory representation of the complete specification.

The **verification layer** enforces constraints at runtime. Refinement types are validated by beartype at function boundaries. Deal contracts check pre/post conditions on framework internals and optionally on user commands. Constraint metadata is extracted from types for use in CLI help text, JSON Schema export, and test generation.

The **framework core** processes the specification registry to generate interface implementations. The CLI generator creates a Typer application with commands, argument parsers, and output formatters. The TUI generator creates a Textual application with screen routing and command palette integration. The API layer exposes async functions with typed signatures. The artifact generator produces MCP tool definitions, JSON Schema exports, and documentation.

The **runtime layer** handles execution. Commands execute with a context object providing access to database sessions, service clients, configuration, and output formatting. Queries support caching with configurable TTL. Screens bind to reactive data sources updated by queries.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Specification Layer                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │ @command  │ │  @query   │ │  @entity  │ │   @screen     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘   │
│                              │                                  │
│                    Application Registry                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Verification Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │  beartype   │ │    deal     │ │  Constraint Extraction  │   │
│  │ (runtime)   │ │ (contracts) │ │   (introspection)       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Framework Core                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │Spec Parser  │ │Type System  │ │ Validation Engine       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │CLI Generator│ │TUI Generator│ │ Artifact Generator      │   │
│  │  (Typer)    │ │ (Textual)   │ │ (MCP, REST, Schema)     │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Runtime Layer                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Execution Context                      │   │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐   │   │
│  │  │   DB    │ │ Services │ │ Config │ │   Output     │   │   │
│  │  │ Session │ │ Clients  │ │        │ │  Formatter   │   │   │
│  │  └─────────┘ └──────────┘ └────────┘ └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
      ┌─────────┐        ┌───────────┐       ┌───────────┐
      │   CLI   │        │    TUI    │       │    MCP    │
      │  (mp)   │        │ (mp-tui)  │       │  Server   │
      └─────────┘        └───────────┘       │ (FastMCP) │
                                             └───────────┘
                                                   │
                                             ┌─────┴─────┐
                                             ▼           ▼
                                       ┌───────────┐ ┌───────────┐
                                       │  REST API │ │  Python   │
                                       │ (FastAPI) │ │    API    │
                                       │ [optional]│ │           │
                                       └───────────┘ └───────────┘
```

### The Verification Pyramid

The verification stack forms a pyramid where each layer adds different guarantees:

```
                    ┌─────────────────────────────────────┐
                    │         Hypothesis + deal.cases     │  Test-time verification
                    │      Property-based test generation │  (comprehensive coverage)
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │              deal                    │  Runtime contracts
                    │    Pre/post conditions, invariants   │  (framework internals)
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │            beartype                  │  Runtime type enforcement
                    │    Refinement types as primitives    │  (every function call)
                    └─────────────────────────────────────┘
```

---

## Verification Stack

The verification stack transforms Python's type hints from documentation into executable contracts. It provides three layers of verification: refinement types for semantic constraints, design-by-contract for behavioral specifications, and property-based testing for comprehensive validation.

### Refinement Types

Refinement types are type aliases with runtime-enforced constraints. They use Python's `Annotated` type with beartype validators:

```python
from hive.types import PositiveInt, Port, Email, NonEmptyStr, Percentage

@command(app)
async def create_server(
    ctx,
    name: NonEmptyStr,
    port: Port,
    admin_email: Email,
    max_connections: PositiveInt = 100,
) -> ServerResult:
    """Create a new server configuration."""
    ...
```

When a user calls `create_server --port 70000`, the CLI automatically:
1. Validates the value against the Port constraint (1-65535)
2. Displays a user-friendly error: "Invalid value for 'port': must be between 1 and 65535"
3. Exits with appropriate error code

#### Available Refinement Types

**Primitive Numeric Types:**

| Type | Constraint | Use Case |
|------|------------|----------|
| `PositiveInt` | x > 0 | IDs, counts, quantities |
| `NonNegativeInt` | x >= 0 | Indices, offsets |
| `NegativeInt` | x < 0 | Decrements, debits |
| `PositiveFloat` | x > 0.0 | Prices, measurements |
| `NonNegativeFloat` | x >= 0.0 | Distances, durations |
| `UnitInterval` | 0.0 <= x <= 1.0 | Progress, opacity |
| `Percentage` | 0.0 <= x <= 100.0 | Completion, utilization |
| `Probability` | 0.0 <= x <= 1.0 | Statistical values |

**Domain-Specific Numeric Types:**

| Type | Constraint | Use Case |
|------|------------|----------|
| `Port` | 1 <= x <= 65535 | Network ports |
| `HttpStatusCode` | 100 <= x <= 599 | HTTP responses |
| `UnixTimestamp` | x >= 0 | Timestamps |
| `Year` | 1 <= x <= 9999 | Calendar years |
| `Month` | 1 <= x <= 12 | Calendar months |
| `Day` | 1 <= x <= 31 | Calendar days |
| `Hour` | 0 <= x <= 23 | Time hours |
| `Minute` | 0 <= x <= 59 | Time minutes |
| `Second` | 0 <= x <= 59 | Time seconds |

**String Refinement Types:**

| Type | Constraint | Use Case |
|------|------------|----------|
| `NonEmptyStr` | len(s) > 0 | Required text fields |
| `TrimmedStr` | s == s.strip() | Normalized text |
| `LowercaseStr` | s == s.lower() | Case-insensitive identifiers |
| `UppercaseStr` | s == s.upper() | Constants, codes |
| `Identifier` | s.isidentifier() | Python names |
| `Slug` | lowercase, hyphens only | URL slugs |
| `Email` | basic email pattern | Email addresses |
| `Url` | http(s):// pattern | Web URLs |
| `FilePath` | non-empty, no nulls | File system paths |
| `DirectoryPath` | alias for FilePath | Directory paths |

#### Creating Custom Refinement Types

Define domain-specific types using beartype's `Is` validator:

```python
from typing import Annotated
from beartype.vale import Is

# Simple constraint
TaskPriority = Annotated[int, Is[lambda x: 1 <= x <= 5]]
"""Task priority level (1-5, where 1 is highest)."""

# Regex-based constraint
import re
SlackChannel = Annotated[str, Is[lambda s: bool(re.match(r'^#[a-z0-9-]+$', s))]]
"""Slack channel name (e.g., #general, #dev-team)."""

# Compound constraints
SecurePassword = Annotated[str,
    Is[lambda s: len(s) >= 12] &
    Is[lambda s: any(c.isupper() for c in s)] &
    Is[lambda s: any(c.isdigit() for c in s)]
]
"""Password with minimum security requirements."""
```

### Contract Decorators

For explicit pre/post conditions beyond type constraints, use contract decorators:

```python
from hive import command
from hive.contracts import requires, ensures

@command(app, entities=[Task])
@requires(lambda ctx, task_id: task_id > 0, "Task ID must be positive")
@requires(lambda ctx, task_id: ctx.db.exists(Task, task_id), "Task must exist")
@ensures(lambda ctx, task_id, result: result.id == task_id)
async def get_task(ctx, task_id: int) -> Task:
    """Retrieve a task by ID."""
    task = await ctx.db.get(Task, task_id)
    return task
```

**`@requires(condition, message)`** - Precondition decorator:
- Checked before function executes
- Receives same arguments as function
- Raises `CommandError` with user-friendly message if condition is False
- Use for: input validation, state checks, authorization

**`@ensures(condition, message)`** - Postcondition decorator:
- Checked after function executes
- Receives original arguments plus `result` keyword
- Raises `CommandError` if condition is False
- Use for: output validation, consistency checks

**`@invariant(condition, message)`** - Class invariant decorator:
- Applied to entity classes
- Checked after every state mutation
- Wraps `deal.inv` with Hive error handling
- Use for: data integrity, business rules

```python
from hive import entity
from hive.contracts import invariant

@entity(app)
@invariant(lambda self: self.balance >= 0, "Balance cannot be negative")
@invariant(lambda self: self.status in ('active', 'suspended', 'closed'))
class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    balance: float = 0.0
    status: str = "active"
```

### Constraint Introspection

The framework extracts constraint metadata from refinement types for use in:

1. **CLI Help Text**: Shows valid ranges and patterns
2. **Validation Error Messages**: User-friendly constraint descriptions
3. **JSON Schema Export**: Includes min/max, pattern, etc.
4. **Test Generation**: Produces valid inputs automatically

```python
from hive.types.introspection import extract_constraints
from hive.types import Port

info = extract_constraints(Port)
# ConstraintInfo(
#     base_type=int,
#     description="integer between 1 and 65535",
#     min_value=1,
#     max_value=65535,
#     validator=<function>,
# )
```

---

## Specification System Design

### The App Object

Every Hive application begins with an App instance that defines global configuration and serves as the registration target for decorators.

```python
from hive import App

app = App(
    name="mixpanel-data",
    version="0.1.0",
    description="Analytics data toolkit for Mixpanel",
    cli_command="mp",
    tui_title="Mixpanel Data Explorer",
    database="sqlite:///~/.mixpanel_data/data.db",
)
```

The App object accepts the following configuration:

**name**: The package name, used for imports and distribution. Should be a valid Python identifier using underscores.

**version**: Semantic version string following PEP 440.

**description**: Human-readable description used in help text and documentation.

**cli_command**: The command name installed as a console script entry point. Users invoke the application with this name.

**tui_title**: The title displayed in the TUI header bar.

**database**: Database connection URL. Defaults to SQLite at a platform-appropriate location. Supports `sqlite://`, `duckdb://`, and `postgresql://` schemes. Environment variable interpolation is supported via `${VAR_NAME}` syntax.

**mcp_server**: Boolean, defaults to False. When True, generates an MCP server entry point exposing commands as tools for AI agents.

**rest_api**: Boolean, defaults to False. When True, generates a FastAPI application exposing commands as HTTP endpoints.

**rest_api_prefix**: URL prefix for REST API endpoints (e.g., "/api/v1"). Only used when rest_api is True.

### Entity Definitions

Entities define the data model using SQLModel. The `@entity` decorator registers models with the application for migration management and context injection.

```python
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON
from hive import entity

@entity(app)
class Project(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    api_secret: str | None = Field(default=None, exclude=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

@entity(app)
class Event(SQLModel, table=True):
    id: str = Field(primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    name: str = Field(index=True)
    distinct_id: str
    timestamp: datetime = Field(index=True)
    properties: dict = Field(default_factory=dict, sa_type=JSON)
```

SQLModel classes are simultaneously Pydantic models (supporting validation, serialization, and JSON Schema export) and SQLAlchemy ORM models (supporting database operations). The `table=True` parameter indicates the class maps to a database table.

The `@entity` decorator records the model in the application registry. This enables automatic migration generation, context injection of entity classes, and spec export.

### Command Definitions

Commands represent actions that modify state or interact with external systems. The `@command` decorator registers functions as CLI commands, TUI actions, and API methods.

```python
from datetime import date
from typing import Annotated
from hive import command
from hive.types import Argument, Option, PositiveInt
from hive.contracts import requires, ensures

@command(app, entities=[Event, Project])
@requires(lambda ctx, project_id: project_id > 0, "Project ID must be positive")
@ensures(lambda ctx, project_id, start, end, result: result.count >= 0)
async def export(
    ctx,
    project_id: Annotated[PositiveInt, Argument(help="Mixpanel project ID")],
    start: Annotated[date, Option("--start", "-s", help="Start date")],
    end: Annotated[date, Option("--end", "-e", help="End date")] = None,
) -> ExportResult:
    """
    Export event data from Mixpanel.

    Downloads events for the specified date range and stores them
    in the local database for fast querying.

    Examples:
        mp export 12345 --start 2024-01-01 --end 2024-01-31
        mp export 12345 -s 2024-01-01 --json
    """
    end = end or date.today()

    project = await ctx.db.get(Project, project_id)
    if not project:
        raise CommandError(f"Project {project_id} not found. Run 'mp init' first.")

    events = await ctx.services.mixpanel.export_events(project, start, end)
    await ctx.db.bulk_insert([Event(**e, project_id=project_id) for e in events])

    return ExportResult(count=len(events), date_range=(start, end), project_id=project_id)
```

The decorator accepts the following parameters:

**entities**: List of entity classes the command interacts with. Used for dependency documentation and potential cache invalidation.

**name**: Override the command name (defaults to function name).

**aliases**: Alternative names for the command.

**hidden**: If True, hide from help text (useful for deprecated commands).

Function parameters use `Annotated` types to specify CLI behavior. `Argument` marks positional arguments; `Option` marks named flags. Type hints determine parsing behavior: `int` parses integers, `date` parses ISO dates, `Path` validates file paths.

**Refinement types in parameters are automatically validated**. Using `PositiveInt` instead of `int` ensures the CLI validates the constraint before execution.

The first parameter is always the execution context, providing access to database sessions, service clients, configuration, and output formatting.

The return type must be a Pydantic model or primitive type. This type is used for JSON Schema generation, output serialization, and type checking.

The docstring provides command help text. The first paragraph becomes the short description; the full text appears in detailed help. The Examples section is formatted specially in help output.

### Query Definitions

Queries represent read operations that retrieve data without side effects. They support caching and are optimized for repeated execution.

```python
from hive import query
from hive.types import PositiveInt, NonNegativeInt

@query(app, entities=[Event], cache_ttl=300)
async def events(
    ctx,
    project_id: PositiveInt,
    event_name: str | None = None,
    start: date | None = None,
    end: date | None = None,
    limit: NonNegativeInt = 1000,
) -> list[Event]:
    """Query events from local database."""
    q = select(Event).where(Event.project_id == project_id)

    if event_name:
        q = q.where(Event.name == event_name)
    if start:
        q = q.where(Event.timestamp >= datetime.combine(start, time.min))
    if end:
        q = q.where(Event.timestamp <= datetime.combine(end, time.max))

    q = q.order_by(Event.timestamp.desc()).limit(limit)

    return await ctx.db.exec(q)
```

Queries differ from commands in several ways. They are expected to be side-effect-free and idempotent. They support time-based caching via `cache_ttl` (seconds). They are exposed in the CLI as subcommands but may also be invoked internally by screens for data binding.

The `cache_ttl` parameter enables response caching. Cached results are keyed by parameter values and invalidated after the specified duration. Cache invalidation also occurs when commands targeting the same entities execute.

### Screen Definitions

Screens define TUI views using Textual's component model. The `@screen` decorator registers screens for navigation and command palette integration.

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable
from hive import screen
from hive.widgets import CommandPalette

@screen(app, default=True, keybinding="d")
class DashboardScreen(Screen):
    """Main dashboard showing project overview."""

    BINDINGS = [
        ("e", "push_screen('export')", "Export"),
        ("q", "push_screen('query')", "Query"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield ProjectSelector(id="project-selector")
        yield EventSummaryTable(id="summary")
        yield RecentEventsLog(id="recent")
        yield Footer()
        yield CommandPalette()

    async def on_mount(self) -> None:
        await self.refresh_data()

    async def refresh_data(self) -> None:
        project_id = self.query_one("#project-selector").value
        if project_id:
            events = await self.app.queries.events(project_id=project_id, limit=100)
            self.query_one("#recent").update(events)

    def action_refresh(self) -> None:
        self.run_worker(self.refresh_data())
```

The decorator accepts:

**default**: If True, this screen displays on application start.

**keybinding**: Global key to navigate to this screen.

**name**: Screen identifier for navigation (defaults to class name).

Screens are standard Textual Screen subclasses. The framework provides additional widgets (CommandPalette, themed Header/Footer) and integrates queries through the app context.

### Service Definitions

Services represent external API clients with managed credentials and lifecycle.

```python
from hive import service

@service(app, credentials="keyring:mixpanel/{project_id}")
class MixpanelService:
    """Mixpanel API client."""

    def __init__(self, api_secret: str):
        self.client = httpx.AsyncClient(
            base_url="https://data.mixpanel.com/api/2.0",
            auth=("", api_secret),
        )

    async def export_events(
        self,
        project: Project,
        start: date,
        end: date,
    ) -> list[dict]:
        response = await self.client.get("/export", params={
            "from_date": start.isoformat(),
            "to_date": end.isoformat(),
        })
        response.raise_for_status()
        return [json.loads(line) for line in response.text.strip().split("\n")]

    async def close(self) -> None:
        await self.client.aclose()
```

The **credentials** parameter specifies where to retrieve authentication data. The `keyring:` prefix indicates system keychain storage. The path supports interpolation from context.

Services are instantiated lazily and cached for the application lifetime. The framework calls `close()` methods during shutdown.

---

## Execution Context

Commands, queries, and screens receive an execution context object providing access to framework services.

```python
class Context:
    db: DatabaseSession       # SQLModel async session
    entities: EntityRegistry  # Access to entity classes by name
    services: ServiceRegistry # Access to service instances
    config: AppSettings       # Pydantic settings object
    output: OutputFormatter   # Rich console with format awareness

    # Metadata
    command_name: str         # Current command being executed
    output_format: OutputFormat  # Requested format (json, table, csv)
    interactive: bool         # True if TTY attached
```

### Context Invariants

The execution context maintains invariants enforced by deal contracts:

```python
@deal.inv(lambda self: self._session is not None or self._closed)
@deal.inv(lambda self: not (self._committed and not self._closed))
@deal.inv(lambda self: not (self._rolled_back and self._committed))
class ExecutionContext:
    """
    Invariants:
    - Session is always available unless context is closed
    - Cannot be both committed and still open
    - Cannot be both committed and rolled back
    """
```

These invariants prevent:
- Accessing database after context is closed
- Committing twice
- Committing after rollback

### Database Access

The `ctx.db` object is an async SQLModel session supporting standard operations:

```python
# Query
results = await ctx.db.exec(select(Event).where(Event.name == "signup"))

# Get by primary key
project = await ctx.db.get(Project, project_id)

# Insert
ctx.db.add(Project(id=123, name="My Project"))
await ctx.db.commit()

# Bulk insert
await ctx.db.bulk_insert(events)

# Raw SQL (for complex queries)
results = await ctx.db.execute(text("SELECT * FROM events WHERE ..."))
```

### Output Formatting

The `ctx.output` object handles format-aware rendering:

```python
# Automatic formatting based on --json/--table/--csv flags
await ctx.output.result(export_result)

# Explicit table output
await ctx.output.table(events, columns=["name", "timestamp", "distinct_id"])

# Progress indication
async with ctx.output.progress("Exporting events...") as progress:
    for batch in batches:
        await process(batch)
        progress.advance()

# Status messages (hidden in JSON mode)
ctx.output.info("Processing complete")
ctx.output.warning("Some events skipped")
ctx.output.error("Failed to connect")
```

The formatter inspects `ctx.output_format` to determine rendering behavior. In JSON mode, only the final `result()` call produces output; status messages are suppressed. In table mode, Rich tables with formatting are rendered. In interactive mode (TTY detected), progress bars animate; in non-interactive mode, they degrade to log lines.

---

## CLI Generation

The framework generates a Typer application from the command and query registry.

### Generated Structure

```python
# Generated: mixpanel_data/cli.py

import typer
from .app import app as hive_app

cli = typer.Typer(
    name="mp",
    help="Analytics data toolkit for Mixpanel",
    rich_markup_mode="rich",
)

@cli.command()
def export(
    project_id: Annotated[int, typer.Argument(help="Mixpanel project ID")],
    start: Annotated[datetime, typer.Option("--start", "-s", help="Start date")],
    end: Annotated[datetime | None, typer.Option("--end", "-e")] = None,
    output_format: Annotated[str, typer.Option("--format", "-f")] = "table",
    json_output: Annotated[bool, typer.Option("--json")] = False,
):
    """Export event data from Mixpanel."""
    result = asyncio.run(hive_app.commands.export(project_id, start, end))
    _output(result, json_output or output_format == "json")

# ... additional commands and queries
```

### Validation Integration

The CLI generator integrates beartype validation with user-friendly error handling:

```python
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation

async def _execute_command(self, func, output_format, **kwargs):
    """Execute command with validation."""
    async with ExecutionContext(...) as ctx:
        try:
            # Apply beartype validation
            validated_func = beartype(func)
            result = await validated_func(ctx, **kwargs)
            # ... output handling
        except BeartypeCallHintParamViolation as e:
            # Convert to user-friendly error
            error_msg = self._format_validation_error(e, kwargs)
            raise CommandError(error_msg, exit_code=1)
```

When validation fails, the CLI shows:

```
$ mp export 12345 --port 70000
Error: Invalid value for 'port': must be between 1 and 65535
```

Instead of a Python traceback.

### Standard Flags

Every command receives standard flags for output control:

**--json**: Output result as JSON (shorthand for --format json).

**--format, -f**: Output format selection (json, table, csv, yaml).

**--quiet, -q**: Suppress non-essential output.

**--verbose, -v**: Enable detailed logging.

**--yes, -y**: Assume yes for confirmation prompts.

### Entry Points

The generated `pyproject.toml` includes console script entry points. Core entry points are always generated; optional interfaces add additional entry points when enabled:

```toml
[project.scripts]
# Always generated
mp = "mixpanel_data.cli:cli"
mp-tui = "mixpanel_data.tui:main"

# Generated when mcp_server=True
mp-mcp = "mixpanel_data.mcp:serve"

# Generated when rest_api=True
mp-api = "mixpanel_data.api:serve"
```

---

## TUI Generation

The framework generates a Textual application from the screen and command registry.

### Application Shell

The TUI provides a consistent application shell across all Hive applications:

```
┌─────────────────────────────────────────────────────────────────┐
│ Mixpanel Data Explorer                          [d]ash [q]uery  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      Screen Content                             │
│                   (User-defined layout)                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [Tab] Focus  [Ctrl+P] Commands  [?] Help  [Ctrl+Q] Quit        │
└─────────────────────────────────────────────────────────────────┘
```

**Header**: Application title with screen tabs showing keybindings.

**Content Area**: User-defined screen layouts.

**Footer**: Standard keybindings and context-sensitive hints.

**Command Palette**: Searchable overlay (Ctrl+P) listing all commands and screens.

### Screen Navigation

Screens register in a navigation stack supporting:

```python
# Push screen (with back navigation)
await self.app.push_screen("query")

# Replace screen (no back navigation)
await self.app.switch_screen("dashboard")

# Pop to previous screen
await self.app.pop_screen()

# Direct navigation via keybinding
# (configured in @screen decorator)
```

### Command Palette Integration

The command palette exposes all registered commands:

```
┌─────────────────────────────────────────────────────────────────┐
│ > export                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ▶ export      Export event data from Mixpanel                  │
│   init        Initialize a new Mixpanel project                │
│   query       Query events from local database                  │
│   funnel      Analyze conversion funnel                         │
└─────────────────────────────────────────────────────────────────┘
```

Selecting a command opens a modal dialog with parameter inputs:

```
┌─────────────── Export ──────────────────────────────────────────┐
│                                                                 │
│ Project ID: [12345          ]                                   │
│ Start Date: [2024-01-01     ]                                   │
│ End Date:   [2024-01-31     ]                                   │
│                                                                 │
│                    [Cancel]  [Execute]                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## MCP Server Generation (Optional)

When enabled, Hive generates an MCP (Model Context Protocol) server using FastMCP, exposing commands as tools for AI agents operating in non-terminal environments.

### Enabling MCP Server

The MCP server is opt-in, configured in the App definition:

```python
app = App(
    name="myapp",
    cli_command="myapp",
    mcp_server=True,  # Enable MCP server generation
)
```

Or via configuration file:

```toml
# hive.toml
[mcp]
enabled = true
```

### Why FastMCP

Hive uses FastMCP rather than the lower-level official MCP Python SDK for several reasons. FastMCP provides a decorator-based API that mirrors Hive's own design patterns, enabling natural integration between the specification layer and MCP tool generation. Where the raw SDK requires manual server instantiation, tool registration, and protocol handling, FastMCP abstracts these concerns behind a clean interface.

The alignment between FastMCP and Hive is not coincidental. Both frameworks embrace the philosophy that type hints and decorators should drive behavior, reducing boilerplate while maintaining full expressiveness. This shared philosophy enables Hive to generate FastMCP servers that feel native to both frameworks.

### Tool Definitions

Each command generates an MCP tool definition. **Refinement type constraints are included in the schema**:

```json
{
  "name": "export",
  "description": "Export event data from Mixpanel. Downloads events for the specified date range and stores them in the local database for fast querying.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_id": {
        "type": "integer",
        "description": "Mixpanel project ID",
        "minimum": 1
      },
      "port": {
        "type": "integer",
        "description": "Port number",
        "minimum": 1,
        "maximum": 65535
      },
      "start": {
        "type": "string",
        "format": "date",
        "description": "Start date"
      },
      "end": {
        "type": "string",
        "format": "date",
        "description": "End date"
      }
    },
    "required": ["project_id", "start"]
  }
}
```

### Server Implementation

The MCP server uses the standard JSON-RPC protocol:

```bash
# Start MCP server (stdio transport)
$ mp-mcp

# Or with specific transport
$ mp-mcp --transport sse --port 3000
```

The server handles tool discovery, invocation, and result formatting according to the MCP specification.

---

## REST API Generation (Optional)

When enabled, Hive generates a FastAPI application exposing commands as HTTP endpoints. This interface extends Hive applications beyond terminal contexts to web integrations, remote access, and cross-language consumption.

### Enabling REST API

The REST API is opt-in, configured in the App definition:

```python
app = App(
    name="myapp",
    cli_command="myapp",
    rest_api=True,  # Enable REST API generation
    rest_api_prefix="/api/v1",  # Optional: URL prefix
)
```

Or via configuration file:

```toml
# hive.toml
[rest_api]
enabled = true
prefix = "/api/v1"
cors_origins = ["http://localhost:3000"]
```

### Generated Endpoints

Each command generates a POST endpoint:

```
POST /api/v1/export
Content-Type: application/json

{
  "project_id": 12345,
  "start": "2024-01-01",
  "end": "2024-01-31"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "count": 47832,
    "date_range": ["2024-01-01", "2024-01-31"],
    "project_id": 12345
  }
}
```

Each query generates a GET endpoint:

```
GET /api/v1/events?project_id=12345&event_name=signup&limit=100
```

### OpenAPI Documentation

FastAPI automatically generates OpenAPI (Swagger) documentation from the command and query specifications. **Refinement type constraints are exported to the OpenAPI schema**:

```yaml
paths:
  /api/v1/export:
    post:
      parameters:
        - name: port
          schema:
            type: integer
            minimum: 1
            maximum: 65535
```

This documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the REST API server is running.

### Running the REST API Server

```bash
# Development server
$ hive serve --port 8000

# Or via generated entry point
$ myapp-api

# Production deployment (uvicorn)
$ uvicorn myapp.api:app --host 0.0.0.0 --port 8000
```

### Authentication

The REST API supports pluggable authentication:

```python
app = App(
    name="myapp",
    rest_api=True,
    rest_api_auth="bearer",  # Options: none, bearer, api_key, oauth2
)
```

Authentication configuration integrates with the existing service credential system, enabling secure remote access to the same commands available locally.

---

## Specification Export

The framework exports the specification in multiple formats for tooling integration and documentation.

### JSON Schema Export

```bash
$ hive spec export --format json > spec.json
```

**Refinement type constraints are included in the export**:

```json
{
  "$schema": "https://hive.dev/schema/v1",
  "app": {
    "name": "mixpanel-data",
    "version": "0.1.0",
    "cli_command": "mp"
  },
  "entities": {
    "Project": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"}
      },
      "required": ["id", "name"]
    },
    "Event": { ... }
  },
  "commands": {
    "export": {
      "description": "Export event data from Mixpanel.",
      "parameters": {
        "project_id": {
          "type": "integer",
          "minimum": 1,
          "description": "Mixpanel project ID"
        },
        "port": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535,
          "description": "Port number"
        }
      },
      "returns": {"$ref": "#/definitions/ExportResult"},
      "entities": ["Event", "Project"]
    }
  },
  "queries": { ... },
  "screens": { ... }
}
```

### TOML Export

```bash
$ hive spec export --format toml > hive.toml
```

Produces a human-readable configuration file suitable for documentation or alternate tooling.

### Specification Diffing

```bash
$ hive spec diff v1.0.0 v1.1.0

Commands:
  + added: funnel
  ~ modified: export
    - parameter 'format' type changed: str -> OutputFormat
    - return type changed: dict -> ExportResult

Entities:
  ~ modified: Event
    + added field: session_id (str, optional)

Breaking changes detected: 2
```

### Documentation Generation

```bash
$ hive docs generate --format markdown > docs/reference.md
$ hive docs generate --format man > man/mp.1
```

Generates reference documentation from specifications with proper formatting for each output type.

---

## Project Structure

A standard Hive project follows this structure:

```
myproject/
├── pyproject.toml           # Project metadata and dependencies
├── hive.toml                # Optional: explicit configuration overrides
├── README.md
├── src/
│   └── myproject/
│       ├── __init__.py      # Package init, exports app
│       ├── app.py           # App definition and decorators
│       ├── models.py        # SQLModel entity definitions
│       ├── types.py         # Custom refinement types
│       ├── commands/        # Command implementations
│       │   ├── __init__.py
│       │   ├── export.py
│       │   └── sync.py
│       ├── queries/         # Query implementations
│       │   ├── __init__.py
│       │   └── events.py
│       ├── screens/         # TUI screen definitions
│       │   ├── __init__.py
│       │   ├── dashboard.py
│       │   └── query_builder.py
│       ├── services/        # External service clients
│       │   ├── __init__.py
│       │   └── api_client.py
│       └── widgets/         # Custom Textual widgets
│           ├── __init__.py
│           └── event_table.py
├── tests/
│   ├── conftest.py          # Hypothesis profiles, fixtures
│   ├── strategies.py        # Custom Hypothesis strategies
│   ├── test_commands.py
│   ├── test_queries.py
│   └── test_properties.py   # Property-based tests
└── docs/
    └── ...
```

### Configuration Files

**pyproject.toml** contains standard Python project metadata:

```toml
[project]
name = "myproject"
version = "0.1.0"
dependencies = [
    "hive-framework>=0.2.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "hypothesis>=6.100.0",
]

[project.scripts]
myapp = "myproject.cli:cli"
myapp-tui = "myproject.tui:main"

[tool.hive]
app = "myproject.app:app"
```

**hive.toml** provides optional configuration overrides:

```toml
[database]
url = "sqlite:///~/.myproject/data.db"
echo = false

[tui]
theme = "tokyo-night"

[cli]
rich_errors = true
```

---

## CLI Tooling

Hive provides a CLI for project management and development.

### Project Initialization

```bash
$ hive new myproject
Creating new Hive project: myproject

Select template:
  [1] minimal    - Basic app with one command
  [2] crud       - CRUD app with entities and screens
  [3] api-client - App integrating with external API
  [4] analytics  - Data analysis app with DuckDB

Template: 3

Project created at ./myproject

Next steps:
  cd myproject
  hive dev
```

### Development Server

```bash
$ hive dev

🐝 Hive development server starting...

  CLI:  mp (available in shell)
  TUI:  mp-tui (or: mp --tui)
  MCP:  mp-mcp --port 3000

Watching for changes...
```

The development server provides hot reload for code changes, automatic database migrations, and integrated logging.

### Database Management

```bash
# Generate migration from model changes
$ hive db migrate "add session_id to events"

# Apply pending migrations
$ hive db upgrade

# Show migration history
$ hive db history

# Reset database
$ hive db reset --yes
```

### Build and Distribution

```bash
# Build distribution packages
$ hive build

# Validate package
$ hive build --check

# Publish to PyPI
$ hive publish
```

---

## Testing Support

Hive provides comprehensive testing utilities including property-based testing integration.

### Test Client

```python
import pytest
from hive.testing import TestClient
from myproject.app import app

@pytest.fixture
def client():
    return TestClient(app, database="sqlite:///:memory:")

async def test_export_command(client):
    # Setup
    await client.db.add(Project(id=123, name="Test"))
    await client.db.commit()

    # Execute command
    result = await client.invoke("export", project_id=123, start=date(2024, 1, 1))

    # Verify
    assert result.count > 0
    events = await client.db.exec(select(Event))
    assert len(events) == result.count

async def test_export_cli_output(client):
    # Test CLI output formatting
    output = await client.cli("export 123 --start 2024-01-01 --json")
    data = json.loads(output)
    assert "count" in data
```

### Property-Based Testing

The `hive.testing` module provides Hypothesis strategies for refinement types:

```python
from hypothesis import given, settings
from hive.testing import strategy_for_type, MockExecutionContext
from hive.types import PositiveInt, Port, Percentage

@given(x=strategy_for_type(PositiveInt))
def test_positive_int_always_positive(x):
    """Strategy generates only positive integers."""
    assert x > 0

@given(port=strategy_for_type(Port))
def test_port_in_range(port):
    """Strategy generates valid ports."""
    assert 1 <= port <= 65535

@given(pct=strategy_for_type(Percentage))
def test_percentage_in_range(pct):
    """Strategy generates valid percentages."""
    assert 0.0 <= pct <= 100.0
```

### Mock Execution Context

For testing commands without database:

```python
from hive.testing import MockExecutionContext

async def test_my_command():
    async with MockExecutionContext() as ctx:
        result = await my_command(ctx, task_id=1)

        # Verify database interactions
        assert ctx.db.add.called
        assert ctx.db.commit.called
```

### Property Tests from Commands

Generate property tests automatically from command specifications:

```python
from hive.testing import property_test_command

# Generates Hypothesis test from command signature and contracts
test_create_user_properties = property_test_command(
    app.registry.get_command("create_user")
)
```

### Contract-Derived Tests

Use `deal.cases` to generate tests from contracts:

```python
import deal
from myproject.commands import get_task

# Generates test cases from @requires/@ensures contracts
test_get_task_contracts = deal.cases(get_task)
```

### Hypothesis Configuration

```python
# tests/conftest.py
from hypothesis import settings, Verbosity
import os

# Fast profile for development
settings.register_profile(
    "fast",
    max_examples=10,
    verbosity=Verbosity.quiet
)

# Default profile
settings.register_profile(
    "default",
    max_examples=100,
    verbosity=Verbosity.normal
)

# Thorough profile for CI
settings.register_profile(
    "thorough",
    max_examples=1000,
    verbosity=Verbosity.verbose
)

# Load profile from environment
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
```

### Conformance Testing

```bash
# Generate tests from specification
$ hive spec test-gen > tests/test_conformance.py

# Run conformance tests
$ pytest tests/test_conformance.py -v
```

Generated tests verify that implementations match their declared signatures, return types are valid, and CLI output parses to declared types.

---

## Conformance-Driven Specification (CDS)

Hive is informed by Conformance-Driven Specification (CDS), a methodology for building software systems where a single, machine-readable specification serves as the authoritative source of truth from which multiple implementations are derived and verified.

### CDS Principles

Traditional software development often treats specifications as documentation artifacts, separate from and frequently out of sync with actual implementations. CDS inverts this relationship: the specification is the primary artifact, and implementations are derived from or validated against it.

The core principles of CDS are as follows.

**Single Source of Truth**: One specification defines the system's capabilities, data models, and interfaces. This specification is machine-readable (typically JSON Schema or equivalent) and serves as the contract that all implementations must honor.

**Derived Implementations**: Rather than manually implementing the same interface multiple times (CLI, API, SDK), implementations are generated from the specification or rigorously validated against it. This eliminates drift between interfaces and reduces duplication.

**Verifiable Conformance**: Any implementation can be tested for conformance against the specification. This enables parallel implementations in different languages or platforms, all guaranteed to behave consistently because they conform to the same spec.

**Schema-First Design**: Data models and operation signatures are defined in the specification before implementation begins. The schema constrains what implementations can do, ensuring predictability and enabling tooling.

**Breaking Change Detection**: Because the specification is versioned and machine-readable, changes between versions can be automatically detected and classified as breaking or non-breaking. This enables semantic versioning automation and migration tooling.

### CDS in Practice

A CDS workflow typically follows this pattern. First, define the specification: data models, operations, parameters, return types, and documentation. Second, generate or implement interfaces that conform to the specification. Third, validate that implementations match the specification through conformance tests. Fourth, when requirements change, update the specification first, then propagate changes to implementations.

The specification format is typically JSON Schema for data models, extended with operation definitions. The specification can be authored directly in JSON/YAML, or extracted from annotated source code in languages with sufficient type information.

### Hive's Relationship to CDS

Hive applies CDS principles using Python's type system as the specification language rather than external JSON Schema files. The decorated Python code (commands, queries, entities) constitutes the specification, with type hints serving as the schema. The framework extracts this specification at import time and derives all interfaces from it.

**The verification stack extends CDS with executable contracts**. Refinement types make type hints into runtime constraints. Contract decorators make behavioral specifications into runtime checks. Hypothesis generates tests from specifications automatically.

This approach provides the benefits of CDS (single source of truth, derived implementations, conformance verification) while offering superior developer experience: IDE support, type checking, and familiar Python tooling all work immediately because the specification is valid Python code.

The specification remains exportable to JSON Schema for language-agnostic consumption, enabling the full CDS workflow when interoperability with non-Python systems is required.

---

## Implementation Status

### Completed

**Phase 1: Foundation Layer** ✅

- [x] Dependencies: beartype>=0.18.0, deal>=4.24.0, hypothesis>=6.100.0 (dev)
- [x] Refinement Types: `hive.types` module with primitives, strings, numeric
- [x] Constraint Introspection: Extract bounds, patterns from types
- [x] Decorator Integration: `@command` extracts constraints from parameters
- [x] Core Types: `ConstraintMetadata` in `ParameterInfo`

**Phase 2: Contract Layer** ✅

- [x] User-facing decorators: `@requires`, `@ensures`, `@invariant`
- [x] ExecutionContext invariants with deal
- [x] Registry contracts for registration validation

**Phase 3: CLI Integration** ✅

- [x] beartype validation with user-friendly error messages

**Phase 4: Testing Utilities** ✅

- [x] Hypothesis strategies via `strategy_for_type()`
- [x] MockExecutionContext for command testing

### In Progress

**Core Framework**
- [ ] App object and registry
- [ ] @command, @query, @entity, @screen decorators
- [ ] CLI generation (Typer)
- [ ] TUI generation (Textual)
- [ ] Execution context (database, services)

### Planned

**Specification and Distribution**
- [ ] JSON Schema export with constraints
- [ ] MCP server generation (FastMCP)
- [ ] REST API generation (FastAPI)
- [ ] Project scaffolding (`hive new`)

**Documentation and Polish**
- [ ] Documentation generation
- [ ] Example applications
- [ ] Migration tooling

---

## Open Questions

Several design decisions remain open for resolution during implementation.

**Query caching strategy**: The current design uses simple TTL-based caching with entity-based invalidation. More sophisticated strategies (LRU, size-based, manual invalidation) may be needed. The caching layer should be pluggable.

**Screen-to-command binding**: How tightly should TUI screens bind to commands? Should screens be able to call commands directly, or should there be an intermediate action layer? The current design allows direct command invocation.

**Error handling patterns**: What is the standard error model? CommandError for expected failures, exceptions for unexpected? How do errors render across interfaces (CLI vs TUI vs MCP)?

**Plugin system**: Should Hive support plugins for custom generators, additional transports, or extended functionality? If so, what is the plugin API?

**Async-first implications**: The current design is async-first, but Typer is sync-based. The bridge layer (asyncio.run or trio) needs careful design for proper signal handling and cleanup.

**Disabling verification in production**: Should beartype/deal be disabled in production for performance? The overhead is minimal (~1-10μs for beartype, ~10-100μs for deal), but some applications may need zero overhead.

---

## Appendix: Complete Example

The following presents a complete Hive application demonstrating the verification stack integration.

```python
# src/todo_app/app.py

from datetime import datetime
from typing import Annotated

from hive import App, command, query, screen, entity
from hive.types import Argument, Option, PositiveInt, NonEmptyStr, Percentage
from hive.contracts import requires, ensures, invariant
from sqlmodel import Field, SQLModel
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Input, Button
from pydantic import BaseModel


# ============================================================
# APP DEFINITION
# ============================================================

app = App(
    name="todo-app",
    version="0.1.0",
    description="A simple todo list application",
    cli_command="todo",
    tui_title="Todo App",
    database="sqlite:///~/.todo/data.db",
)


# ============================================================
# ENTITIES
# ============================================================

@entity(app)
@invariant(lambda self: 0 <= self.progress <= 100, "Progress must be 0-100")
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: NonEmptyStr
    progress: Percentage = 0.0
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


# ============================================================
# RESULT MODELS
# ============================================================

class TaskResult(BaseModel):
    task: Task
    message: str


class TaskListResult(BaseModel):
    tasks: list[Task]
    total: int
    completed: int


# ============================================================
# COMMANDS
# ============================================================

@command(app, entities=[Task])
@requires(lambda ctx, title: len(title.strip()) > 0, "Title cannot be empty")
@ensures(lambda ctx, title, result: result.task.title == title)
async def add(
    ctx,
    title: Annotated[NonEmptyStr, Argument(help="Task title")],
) -> TaskResult:
    """Add a new task to the list."""
    task = Task(title=title)
    ctx.db.add(task)
    await ctx.db.commit()
    await ctx.db.refresh(task)
    return TaskResult(task=task, message=f"Created task #{task.id}")


@command(app, entities=[Task])
@requires(lambda ctx, task_id, progress: 0 <= progress <= 100, "Progress must be 0-100")
async def update_progress(
    ctx,
    task_id: Annotated[PositiveInt, Argument(help="Task ID")],
    progress: Annotated[Percentage, Option("--progress", "-p", help="Progress 0-100")],
) -> TaskResult:
    """Update task progress."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task #{task_id} not found")

    task.progress = progress
    if progress >= 100.0:
        task.completed = True
        task.completed_at = datetime.utcnow()

    await ctx.db.commit()
    return TaskResult(task=task, message=f"Updated task #{task.id}")


@command(app, entities=[Task])
async def complete(
    ctx,
    task_id: Annotated[PositiveInt, Argument(help="Task ID to complete")],
) -> TaskResult:
    """Mark a task as completed."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task #{task_id} not found")

    task.completed = True
    task.progress = 100.0
    task.completed_at = datetime.utcnow()
    await ctx.db.commit()

    return TaskResult(task=task, message=f"Completed task #{task.id}")


@command(app, entities=[Task])
async def delete(
    ctx,
    task_id: Annotated[PositiveInt, Argument(help="Task ID to delete")],
    yes: Annotated[bool, Option("--yes", "-y", help="Skip confirmation")] = False,
) -> TaskResult:
    """Delete a task from the list."""
    task = await ctx.db.get(Task, task_id)
    if not task:
        raise CommandError(f"Task #{task_id} not found")

    if not yes and ctx.interactive:
        if not ctx.output.confirm(f"Delete task #{task_id}: {task.title}?"):
            raise CommandAborted()

    await ctx.db.delete(task)
    await ctx.db.commit()

    return TaskResult(task=task, message=f"Deleted task #{task.id}")


# ============================================================
# QUERIES
# ============================================================

@query(app, entities=[Task])
async def list(
    ctx,
    all: Annotated[bool, Option("--all", "-a", help="Include completed")] = False,
    limit: PositiveInt = 50,
) -> TaskListResult:
    """List tasks."""
    q = select(Task).order_by(Task.created_at.desc())

    if not all:
        q = q.where(Task.completed == False)

    tasks = await ctx.db.exec(q.limit(limit))
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)

    return TaskListResult(tasks=tasks, total=total, completed=completed)


# ============================================================
# SCREENS
# ============================================================

@screen(app, default=True, keybinding="l")
class TaskListScreen(Screen):
    """Main task list view."""

    BINDINGS = [
        ("a", "add_task", "Add"),
        ("c", "complete_task", "Complete"),
        ("d", "delete_task", "Delete"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="tasks")
        yield Input(placeholder="New task...", id="new-task")
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one("#tasks", DataTable)
        table.add_columns("ID", "Title", "Progress", "Status", "Created")
        await self.refresh_tasks()

    async def refresh_tasks(self) -> None:
        result = await self.app.queries.list(all=True)
        table = self.query_one("#tasks", DataTable)
        table.clear()
        for task in result.tasks:
            status = "✓" if task.completed else " "
            table.add_row(
                str(task.id),
                task.title,
                f"{task.progress:.0f}%",
                status,
                task.created_at.strftime("%Y-%m-%d %H:%M"),
            )

    async def action_add_task(self) -> None:
        input = self.query_one("#new-task", Input)
        if input.value:
            await self.app.commands.add(title=input.value)
            input.value = ""
            await self.refresh_tasks()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        await self.action_add_task()

    async def action_complete_task(self) -> None:
        table = self.query_one("#tasks", DataTable)
        if table.cursor_row is not None:
            task_id = int(table.get_cell_at((table.cursor_row, 0)))
            await self.app.commands.complete(task_id=task_id)
            await self.refresh_tasks()

    async def action_delete_task(self) -> None:
        table = self.query_one("#tasks", DataTable)
        if table.cursor_row is not None:
            task_id = int(table.get_cell_at((table.cursor_row, 0)))
            await self.app.commands.delete(task_id=task_id, yes=True)
            await self.refresh_tasks()

    def action_refresh(self) -> None:
        self.run_worker(self.refresh_tasks())
```

### Tests with Property-Based Testing

```python
# tests/test_todo.py

import pytest
from hypothesis import given, settings
from hive.testing import strategy_for_type, MockExecutionContext
from hive.types import PositiveInt, Percentage, NonEmptyStr
from todo_app.app import app, Task, add, update_progress


# Property-based test for refinement types
@given(
    title=strategy_for_type(NonEmptyStr),
    progress=strategy_for_type(Percentage),
)
@settings(max_examples=100)
async def test_task_creation_properties(title, progress):
    """Property: Created tasks preserve their data."""
    async with MockExecutionContext() as ctx:
        result = await add(ctx, title=title)
        assert result.task.title == title
        assert result.task.progress == 0.0  # Default


# Contract-derived test
import deal
test_add_contracts = deal.cases(add)


# Unit test with mock context
async def test_update_progress():
    async with MockExecutionContext() as ctx:
        # Seed a task
        task = Task(id=1, title="Test")
        ctx.seed(Task, [task])

        result = await update_progress(ctx, task_id=1, progress=50.0)
        assert result.task.progress == 50.0
```

This application provides:

**CLI interface:**
```bash
$ todo add "Write documentation"
Created task #1

$ todo list
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ID ┃ Title                ┃ Progress ┃ Status ┃ Created             ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│  1 │ Write documentation  │ 0%       │        │ 2024-01-15 10:30    │
└────┴──────────────────────┴──────────┴────────┴─────────────────────┘

$ todo update-progress 1 --progress 150
Error: Invalid value for 'progress': must be between 0.0 and 100.0

$ todo update-progress 1 --progress 50
Updated task #1

$ todo list --json
{"tasks": [...], "total": 1, "completed": 0}
```

**TUI interface:**
```bash
$ todo --tui
```

Launches interactive terminal application with task table, progress tracking, and keyboard navigation.

**Python API:**
```python
from todo_app import app
from todo_app.app import add, list, complete

async def main():
    result = await add(title="New task")
    print(f"Created: {result.task.id}")

    tasks = await list(all=True)
    for task in tasks.tasks:
        print(f"- {task.title} ({task.progress}%)")
```

---

## Conclusion

Hive provides a framework for building terminal-native applications that serve AI agents, human power users, and developer integrations from a single codebase. By treating decorated Python code as a specification from which interfaces are derived, Hive ensures consistency across access patterns while minimizing duplication and maintenance burden.

**Version 0.2.0 introduces the verification stack**, transforming type hints from documentation into executable contracts. Refinement types like `PositiveInt`, `Port`, and `Email` carry semantic meaning that is enforced at runtime, documented in help text, exported to JSON Schema, and used to generate valid test inputs. Design-by-contract decorators enable explicit behavioral specifications. Property-based testing with Hypothesis provides comprehensive validation.

The framework builds on proven technologies (Typer, Rich, Textual, SQLModel, beartype, deal, Hypothesis) while adding the specification layer that connects them. This approach provides immediate productivity through familiar tools while enabling the framework to grow more capable over time.

The terminal-agent-native design philosophy positions Hive applications as first-class citizens in AI-assisted workflows, where command-line tools are the primary interface for both human operators and AI agents operating through shell access.

---

*Document Version: 0.2.0*
*Last Updated: January 2026*
*Status: Specification with Phase 1 Verification Implementation Complete*
