# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hive is a Python framework for building terminal-agent-native applications. It generates CLI (Typer), TUI (Textual), and Python API interfaces from a single decorated codebase. Optional MCP server (FastMCP) and REST API (FastAPI) generation.

**Status**: Active development - verification stack complete, core framework in progress.

## Development Commands

```bash
# Install dependencies (uses uv)
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/hive --cov-report=term-missing

# Linting and formatting
uv run ruff check .              # Check for issues
uv run ruff check . --fix        # Auto-fix issues
uv run ruff format .             # Format code

# Type checking
uv run pyright

# Docstring coverage
uv run interrogate -vv src/

# Security checks
uv run bandit -c pyproject.toml -r src/
uv run pip-audit

# Architecture validation
uv run lint-imports

# Dead code detection
uv run vulture src/ --min-confidence 80

# Pre-commit hooks
uv run pre-commit install        # Install hooks
uv run pre-commit run --all-files # Run all hooks

# Hive CLI
uv run hive new <name>           # Create new project (scaffold)
uv run hive new <name> --features tui,mcp,rest  # With optional features
uv run hive dev                  # Development server with hot reload
uv run hive dev --interfaces cli,rest,mcp  # Multiple interfaces
uv run hive build                # Build distribution (wraps uv build)
uv run hive publish              # Publish to PyPI (wraps uv publish)
uv run hive spec export          # Export specification as JSON Schema
uv run hive spec export --format toml  # Export as TOML
uv run hive spec export -o spec.json   # Export to file
uv run hive spec diff v1.json v2.json  # Compare specifications
uv run hive spec diff v1.json v2.json --fail-on-breaking  # CI mode
uv run hive mcp serve            # Start MCP server (stdio transport)
uv run hive mcp serve --transport sse --port 8080  # SSE transport
uv run hive serve                # Start REST API server
uv run hive serve --port 8000 --reload  # With hot reload
uv run hive serve --auth api_key # With API key authentication
```

## Architecture

### Three-Layer Design

1. **Specification Layer**: Decorated Python code (`@command`, `@query`, `@entity`, `@screen`, `@service`) registered at import time
2. **Framework Core**: Generators that produce CLI (Typer), TUI (Textual), and artifacts (MCP, REST, Schema) from registry
3. **Runtime Layer**: Execution context providing `ctx.db`, `ctx.services`, `ctx.config`, `ctx.output`

### Core Decorators

- `@entity(app)` - SQLModel table definitions
- `@command(app, entities=[...])` - State-modifying operations
- `@query(app, entities=[...], cache_ttl=N)` - Read-only operations with optional caching
- `@screen(app, default=True, keybinding="x")` - Textual screen definitions
- `@service(app, credentials="keyring:...")` - External API clients with credential management

### Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| CLI | Typer + Rich | Type-hint driven argument parsing |
| TUI | Textual | CSS-like styling, reactive data binding |
| Data | SQLModel | Pydantic + SQLAlchemy unified |
| Database | SQLite (default) | Also supports DuckDB, PostgreSQL |
| MCP | FastMCP | Optional, decorator-based tool generation |
| REST | FastAPI | Optional, OpenAPI docs at `/docs` |

## Project Structure

```
src/hive/
├── __init__.py         # Public API exports
├── app.py              # App class definition
├── errors.py           # Exception hierarchy
├── core/               # Specification parsing and registry
│   ├── decorators.py   # @command, @query, @entity decorators
│   ├── registry.py     # Command/query registration
│   └── types.py        # Core type definitions
├── types/              # Refinement types (beartype-based)
│   ├── numeric.py      # PositiveInt, Percentage, Port, etc.
│   ├── strings.py      # NonEmptyStr, Email, Slug, etc.
│   ├── primitives.py   # Base type utilities
│   └── introspection.py # extract_constraints() for CLI/Schema
├── contracts/          # Design-by-contract (deal-based)
│   └── decorators.py   # @requires, @ensures, @invariant
├── testing/            # Test utilities (hypothesis-based)
│   ├── strategies.py   # strategy_for_type() auto-generation
│   └── mocks.py        # MockExecutionContext
├── cli/                # CLI commands (hive <cmd>)
│   ├── main.py         # CLI entrypoint and subcommand registration
│   ├── spec.py         # hive spec export/diff commands
│   ├── mcp.py          # hive mcp serve command
│   ├── serve.py        # hive serve (REST API) command
│   └── project.py      # hive new/dev/build/publish commands
├── spec/               # Specification export and diffing
│   ├── models.py       # Specification, CommandSchema, etc.
│   ├── export.py       # build_specification(), export_specification()
│   ├── diff.py         # diff_specifications() for breaking changes
│   └── constraints.py  # Parameter constraint extraction
├── generators/         # Interface generators
│   ├── cli.py          # Typer CLI generation
│   ├── tui.py          # Textual TUI generation
│   ├── mcp.py          # MCPGenerator for MCP server
│   ├── rest.py         # RESTGenerator for FastAPI
│   └── schema.py       # JSON Schema generation
└── runtime/            # Execution context and services
    ├── context.py      # ExecutionContext implementation
    ├── config.py       # Pydantic settings
    ├── database.py     # SQLModel async session
    └── output.py       # Format-aware output (--json support)
```

## Key Design Patterns

### CLI-First Architecture
- Every command supports `--json` output for machine parsing
- Commands work headlessly without interactive prompts
- `--yes` flags for confirmation bypass

### Specification-Driven Development
- Decorated Python code is the specification source of truth
- All interfaces derived from single specification
- JSON Schema export for cross-language consumption
- Breaking changes detectable via spec diffing

### Execution Context
Commands receive `ctx` with:
- `ctx.db` - Async SQLModel session
- `ctx.services.<name>` - Lazy-loaded service clients
- `ctx.config` - Pydantic settings
- `ctx.output` - Format-aware output (respects `--json`)

## Implementation Phases

1. **Core Framework**: Decorators, registry, execution context, CLI generation *(in progress)*
2. **Verification Stack**: Refinement types, contracts, testing utilities *(complete)*
3. **TUI and Services**: Textual app, service layer, standard widgets
4. **Specification and Distribution**: JSON Schema export, MCP/REST generation, project tooling
5. **Documentation and Polish**: Doc generation, examples

## Active Technologies
- Python 3.12+ (enables type parameter syntax `class Foo[T]:`) + Typer, Rich, SQLModel, Pydantic, Pydantic-Settings
- SQLite via SQLModel/SQLAlchemy (async support via aiosqlite)
- beartype>=0.18.0 - Runtime type enforcement via refinement types
- deal>=4.24.0 - Design-by-contract decorators (pre/post/inv)
- hypothesis>=6.100.0 - Property-based testing (dev dependency)
- Python 3.12+ + Textual (TUI), keyring (credentials), httpx (HTTP client), existing: Typer, Rich, SQLModel, Pydantic (002-tui-services)
- SQLite via SQLModel (existing infrastructure from Phase 1) (002-tui-services)
- Python 3.12+ (enables type parameter syntax `class Foo[T]:`) (003-spec-distribution)
- N/A (this phase generates artifacts, not data) (003-spec-distribution)

## Development Tools (strict Python standards)
- **uv** - Fast Python package manager and project tool
- **Ruff** - Linting and formatting (replaces Black, isort, Flake8)
- **Pyright** - Static type checking in strict mode
- **pytest** - Testing with 90% coverage requirement
- **interrogate** - Docstring coverage (95% threshold)
- **import-linter** - Architecture enforcement
- **bandit** - Security linting
- **vulture** - Dead code detection
- **pre-commit** - Git hooks for automated checks

## Coding Standards

This project follows strict Python standards for agent-ready code. See `context/strict_python/STRICT_PYTHON_GUIDE.md` for full rationale.

### Type Annotations
- **Pyright strict mode** - All code must pass with zero errors
- **No bare `# type: ignore`** - Must use specific codes: `# type: ignore[arg-type]`
- **Use `from __future__ import annotations`** - Avoid string-based type refs
- **Explicit return types** - All public functions must have return type annotations

### Documentation
- **Google-style docstrings** - Args, Returns, Raises sections
- **95% docstring coverage** - Enforced by interrogate
- **Pydantic Field descriptions** - All fields should have `Field(description="...")`

### Architecture Contracts (enforced by import-linter)
- `hive.types` cannot import from `hive.core`, `hive.runtime`, or `hive.generators`
- `hive.contracts` cannot import from `hive.generators`
- Layered architecture: generators → runtime → core → contracts → types

### Patterns to Use

```python
# Discriminated unions over inheritance
class TextMessage(BaseModel):
    type: Literal["text"] = "text"
    content: str

class ImageMessage(BaseModel):
    type: Literal["image"] = "image"
    url: HttpUrl
    alt_text: str = ""

Message = TextMessage | ImageMessage  # All variants visible

# Exhaustiveness checking
from typing import assert_never

def handle(msg: Message) -> str:
    match msg:
        case TextMessage(): return msg.content
        case ImageMessage(): return f"[Image: {msg.alt_text}]"
        case _ as unreachable: assert_never(unreachable)

# Explicit re-exports in __init__.py
from hive.models import User as User  # `as X` marks intentional export
__all__ = ["User"]

# Descriptive Pydantic fields
class Event(BaseModel):
    event_id: UUID = Field(description="Unique identifier for this event")
    user_id: UserId = Field(description="The user who triggered this event")
```

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Pattern |
|--------------|-----------------|
| `from models import *` | `from models import User, Event` |
| `getattr(module, name)()` | `handlers = {"create": handle_create}; handlers[name]()` |
| `def f(**kwargs: Any)` | Use TypedDict or explicit parameters |
| `def f() -> "User"` | `from __future__ import annotations` then `-> User` |
| `def f(items=[])` | `def f(items: list | None = None)` |
| `# type: ignore` | `# type: ignore[specific-code]` |

### Pydantic Model Standards

```python
from pydantic import BaseModel, ConfigDict

class StrictBase(BaseModel):
    """Base model with maximum validation strictness."""

    model_config = ConfigDict(
        strict=True,           # No type coercion
        frozen=True,           # Immutable after creation
        extra="forbid",        # No undeclared fields
        validate_default=True, # Validate default values
    )
```

## Verification Stack

Three-layer verification pyramid for runtime validation and testing.

### Refinement Types

Use from `hive.types` for automatic validation in command signatures:

```python
from hive import command, App
from hive.types import PositiveInt, Percentage, Port, NonEmptyStr

app = App("myapp")

@command(app)
async def set_priority(ctx, task_id: PositiveInt, progress: Percentage):
    ...
```

**Numeric Types:**
- `PositiveInt` - Integer > 0
- `NonNegativeInt` - Integer >= 0
- `NegativeInt` - Integer < 0
- `PositiveFloat`, `NonNegativeFloat`
- `UnitInterval` - Float 0.0-1.0
- `Percentage` - Float 0.0-100.0
- `Probability` - Alias for UnitInterval

**Domain Types:**
- `Port` - Valid TCP/UDP port (1-65535)
- `HttpStatusCode` - HTTP status (100-599)
- `Year`, `Month`, `Day`, `Hour`, `Minute`, `Second`

**String Types:**
- `NonEmptyStr` - Non-empty string
- `TrimmedStr` - No leading/trailing whitespace
- `Identifier` - Valid Python identifier
- `Slug` - URL-safe (lowercase, hyphens)
- `Email`, `Url`, `FilePath`

### Contract Decorators

Use from `hive.contracts` for explicit preconditions and postconditions:

```python
from hive import command, App
from hive.contracts import requires, ensures

app = App("myapp")

@command(app)
@requires(lambda ctx, task_id: task_id > 0, "Task ID must be positive")
@ensures(lambda ctx, task_id, result: result.id == task_id)
async def get_task(ctx, task_id: int) -> Task:
    ...
```

- `@requires(condition, message)` - Precondition, raises CommandError if False
- `@ensures(condition, message)` - Postcondition, validates return value
- `@invariant(condition, message)` - Class invariant for entities

### Testing Utilities

Use from `hive.testing` for property-based testing:

```python
from hive.testing import strategy_for_type, MockExecutionContext
from hive.types import PositiveInt
from hypothesis import given

@given(x=strategy_for_type(PositiveInt))
def test_always_positive(x):
    assert x > 0

async def test_my_command():
    async with MockExecutionContext() as ctx:
        result = await my_command(ctx, arg="value")
        assert ctx.db.add.called
```

## Recent Changes
- 003-spec-distribution: Added Python 3.12+ (enables type parameter syntax `class Foo[T]:`)
- 002-tui-services: Added Python 3.12+ + Textual (TUI), keyring (credentials), httpx (HTTP client), existing: Typer, Rich, SQLModel, Pydantic
- strict-python-tooling: Implemented strict Python development standards
  - Upgraded to Python 3.12+ (enables type parameter syntax)
  - Added uv as package manager with lockfile
  - Configured Ruff with full ruleset (`select = ["ALL"]`)
  - Added Pyright in strict mode with 30+ additional checks
  - Added GitHub Actions CI pipeline (lint → typecheck → test → docs → security → architecture)
  - Added pre-commit hooks for automated quality gates
  - `hive.types` - 20+ refinement types with beartype validation
  - `hive.contracts` - @requires/@ensures/@invariant decorators wrapping deal
  - `hive.testing` - strategy_for_type() and MockExecutionContext
  - User-friendly CLI error messages for validation failures
