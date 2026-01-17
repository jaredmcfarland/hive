# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hive is a Python framework for building terminal-agent-native applications. It generates CLI (Typer), TUI (Textual), and Python API interfaces from a single decorated codebase. Optional MCP server (FastMCP) and REST API (FastAPI) generation.

**Status**: Active development - verification stack complete, core framework in progress.

## Development Commands

```bash
# Install in development mode (when pyproject.toml exists)
pip install -e ".[dev]"

# Run tests
pytest

# Hive CLI (after implementation)
hive new <name>           # Create new project
hive dev                  # Development server with hot reload
hive build                # Build distribution
hive db migrate <msg>     # Generate migration
hive db upgrade           # Apply migrations
hive spec export          # Export specification as JSON Schema
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
├── generators/         # Interface generators
│   └── cli.py          # Typer CLI generation
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
- Python 3.11+ (required for modern type hints including `X | None` syntax) + Typer, Rich, SQLModel, Pydantic, Pydantic-Settings (001-core-framework)
- SQLite via SQLModel/SQLAlchemy (async support via aiosqlite) (001-core-framework)
- beartype>=0.18.0 - Runtime type enforcement via refinement types
- deal>=4.24.0 - Design-by-contract decorators (pre/post/inv)
- hypothesis>=6.100.0 - Property-based testing (dev dependency)

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
- verification-stack: Complete verification pyramid implementation
  - `hive.types` - 20+ refinement types with beartype validation
  - `hive.contracts` - @requires/@ensures/@invariant decorators wrapping deal
  - `hive.testing` - strategy_for_type() and MockExecutionContext
  - User-friendly CLI error messages for validation failures
- 001-core-framework: Added Python 3.11+ + Typer, Rich, SQLModel, Pydantic, Pydantic-Settings
