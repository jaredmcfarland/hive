# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hive is a Python framework for building terminal-agent-native applications. It generates CLI (Typer), TUI (Textual), and Python API interfaces from a single decorated codebase. Optional MCP server (FastMCP) and REST API (FastAPI) generation.

**Status**: Greenfield project - specification complete, implementation not yet started.

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

## Project Structure (Target)

```
src/hive/
├── core/           # Specification parsing and registry
├── generators/     # CLI, TUI, and artifact generators
└── runtime/        # Execution context and database layer
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

1. **Core Framework**: Decorators, registry, execution context, CLI generation
2. **TUI and Services**: Textual app, service layer, standard widgets
3. **Specification and Distribution**: JSON Schema export, MCP/REST generation, project tooling
4. **Documentation and Polish**: Doc generation, testing utilities, examples

## Active Technologies
- Python 3.11+ (required for modern type hints including `X | None` syntax) + Typer, Rich, SQLModel, Pydantic, Pydantic-Settings (001-core-framework)
- SQLite via SQLModel/SQLAlchemy (async support via aiosqlite) (001-core-framework)

## Recent Changes
- 001-core-framework: Added Python 3.11+ (required for modern type hints including `X | None` syntax) + Typer, Rich, SQLModel, Pydantic, Pydantic-Settings
