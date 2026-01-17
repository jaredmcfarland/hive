# Implementation Plan: Core Framework

**Branch**: `001-core-framework` | **Created**: 2026-01-11 | **Updated**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-core-framework/spec.md`
**Status**: Complete

## Summary

Implement the foundational Hive framework components: decorator system (`@command`, `@query`, `@entity`, `@screen`), central application registry, execution context with database/config/output services, CLI generator using Typer, and verification stack (refinement types, contracts, testing utilities). This establishes the core "define once, generate everywhere" pattern that all future features build upon.

## Technical Context

**Language/Version**: Python 3.11+ (required for modern type hints including `X | None` syntax)
**Primary Dependencies**: Typer, Rich, SQLModel, Pydantic, Pydantic-Settings, beartype>=0.18.0, deal>=4.24.0
**Storage**: SQLite via SQLModel/SQLAlchemy (async support via aiosqlite)
**Testing**: pytest, pytest-asyncio, hypothesis>=6.100.0
**Target Platform**: Cross-platform (macOS, Linux, Windows)
**Project Type**: Single Python package (library + CLI)
**Performance Goals**: Import time <500ms, decorator registration <1ms per item
**Constraints**: Zero external services required for basic operation
**Scale/Scope**: Support applications with 100+ commands, 50+ entities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First

| Rule | Status | Evidence |
|------|--------|----------|
| Interfaces generated from specification | PASS | CLI generator reads from registry; no hand-written CLI |
| Type hints define schema | PASS | Parameter types extracted from function signatures |
| Docstrings define documentation | PASS | Help text derived from docstrings |
| Breaking changes detectable | DEFERRED | Spec diff tooling is Phase 3 scope |

### II. CLI-First Architecture

| Rule | Status | Evidence |
|------|--------|----------|
| Commands work headlessly | PASS | No interactive prompts in core; optional via context |
| `--json` output supported | PASS | FR-009 requires JSON flag on all commands |
| `--yes` bypasses confirmations | PASS | Context provides non-blocking confirmation API |
| Conventional exit codes | PASS | Typer handles exit codes by default |
| Clean piping output | PASS | Output formatter separates data from status messages |

### III. Test-First Development

| Rule | Status | Evidence |
|------|--------|----------|
| Tests before implementation | ENFORCED | Tasks will be ordered tests-first |
| Red-Green-Refactor cycle | ENFORCED | Contract tests written to fail initially |
| Contract tests for signatures | PASS | Registry inspection enables signature verification |
| Integration tests for components | PASS | Context + CLI integration testable end-to-end |

### IV. Triple Interface Consistency

| Rule | Status | Evidence |
|------|--------|----------|
| Return types serialize identically | PASS | Single serialization path via Pydantic models |
| Parameter names match across interfaces | PASS | Registry is single source; generators consume it |
| Error handling consistent | PASS | CommandError base class for all interfaces |
| Documentation from same source | PASS | Docstrings in registry serve all generators |

### V. Simplicity & YAGNI

| Rule | Status | Evidence |
|------|--------|----------|
| No speculative features | PASS | Only P1-P3 user stories; no extras |
| Abstractions after 3rd use | PASS | Direct implementation first |
| Approved technology stack | PASS | All deps from constitution table |
| Sensible defaults | PASS | SQLite default, env var config |

**Constitution Check Result**: PASS (no violations requiring justification)

## Project Structure

### Documentation (this feature)

```text
specs/001-core-framework/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/hive/
├── __init__.py          # Public API exports (App, decorators, types)
├── app.py               # App class definition
├── errors.py            # CommandError, ConfigurationError, etc.
├── core/
│   ├── __init__.py
│   ├── decorators.py    # @command, @query, @entity, @screen
│   ├── registry.py      # ApplicationRegistry class
│   └── types.py         # Registration dataclasses, type definitions
├── types/               # Refinement types (beartype-based)
│   ├── __init__.py      # Public exports
│   ├── numeric.py       # PositiveInt, Percentage, Port, etc.
│   ├── strings.py       # NonEmptyStr, Email, Slug, etc.
│   ├── primitives.py    # Base type utilities
│   └── introspection.py # extract_constraints() for CLI/Schema
├── contracts/           # Design-by-contract (deal-based)
│   ├── __init__.py
│   └── decorators.py    # @requires, @ensures, @invariant
├── testing/             # Test utilities (hypothesis-based)
│   ├── __init__.py
│   ├── strategies.py    # strategy_for_type() auto-generation
│   └── mocks.py         # MockExecutionContext
├── runtime/
│   ├── __init__.py
│   ├── context.py       # ExecutionContext class
│   ├── database.py      # Database session management
│   ├── config.py        # Pydantic Settings integration
│   └── output.py        # OutputFormatter (JSON, table, etc.)
└── generators/
    ├── __init__.py
    └── cli.py           # Typer CLI generator

tests/
├── conftest.py          # Shared fixtures
├── contract/
│   ├── test_decorators.py
│   ├── test_registry.py
│   └── test_cli_generation.py
├── integration/
│   ├── test_context_lifecycle.py
│   └── test_end_to_end.py
├── unit/
│   ├── test_output_formatter.py
│   ├── test_config_loading.py
│   ├── test_refinement_types.py
│   ├── test_contracts.py
│   └── test_strategies.py
└── property/
    └── test_type_strategies.py
```

**Structure Decision**: Single project following constitution's code organization. The `src/hive/` layout matches the constitution's prescribed structure with `core/`, `generators/`, and `runtime/` directories.

## Complexity Tracking

> No violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
