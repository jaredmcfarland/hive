# Implementation Plan: Specification and Distribution

**Branch**: `003-spec-distribution` | **Date**: 2026-01-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-spec-distribution/spec.md`

## Summary

Phase 3 implements specification export (JSON Schema, TOML), MCP server generation via FastMCP, REST API generation via FastAPI, and project tooling CLI commands. The existing registry and decorator infrastructure (Phase 1) provides the foundation—this phase adds generators that serialize that specification to machine-readable formats and external interfaces.

## Technical Context

**Language/Version**: Python 3.12+ (enables type parameter syntax `class Foo[T]:`)
**Primary Dependencies**:
- Existing: Typer, Rich, SQLModel, Pydantic, beartype (runtime validation)
- New: FastMCP (MCP server), FastAPI (REST API), tomli-w (TOML writing)
**Storage**: N/A (this phase generates artifacts, not data)
**Testing**: pytest + pytest-asyncio (established), hypothesis for property-based testing
**Target Platform**: Cross-platform (Linux, macOS, Windows) - CLI application
**Project Type**: single (existing `src/hive/` structure)
**Performance Goals**:
- Specification export: <5 seconds for 100 commands/queries (SC-001)
- REST API: 100 concurrent requests (SC-004)
- Hot reload: <2 second detection (SC-008)
**Constraints**:
- JSON Schema must validate against Draft 2020-12 (SC-002)
- MCP clients must discover tools without manual config beyond connection (SC-003)
**Scale/Scope**: Typical app: 10-50 commands, 10-50 queries, 10-30 entities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Notes |
|-----------|--------|----------------|
| **I. Specification-First** | ✅ PASS | All generators derive from registry; JSON Schema, MCP tools, REST endpoints generated from decorated code |
| **II. CLI-First Architecture** | ✅ PASS | `hive spec export --json`, `hive spec diff` designed for machine parsing; all new commands headless-compatible |
| **III. Test-First Development** | ⏳ VERIFY | Tests must be written before implementation per /speckit.tasks workflow |
| **IV. Triple Interface Consistency** | ✅ PASS | Specification export ensures identical contract across CLI/TUI/API/MCP/REST |
| **V. Simplicity & YAGNI** | ✅ PASS | MCP/REST optional (only when dependencies installed); minimal config defaults |
| **Technology Stack** | ✅ PASS | Uses mandated: FastMCP (MCP), FastAPI (REST), Typer (CLI), Pydantic (schema) |

**Gate Result**: PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/003-spec-distribution/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── spec-export.yaml # JSON Schema export contract
│   ├── mcp-server.yaml  # MCP tool generation contract
│   └── rest-api.yaml    # REST endpoint contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/hive/
├── generators/
│   ├── cli.py           # Existing - CLI generation
│   ├── tui.py           # Existing - TUI generation
│   ├── schema.py        # NEW - JSON Schema generation
│   ├── mcp.py           # NEW - MCP server generation
│   └── rest.py          # NEW - REST API generation
├── spec/                # NEW - Specification export module
│   ├── __init__.py      # Public API
│   ├── export.py        # JSON/TOML export logic
│   └── diff.py          # Specification diffing
├── cli/                 # NEW - CLI commands for hive tool
│   ├── __init__.py
│   ├── spec.py          # hive spec export/diff
│   ├── mcp.py           # hive mcp serve
│   ├── serve.py         # hive serve (REST)
│   ├── project.py       # hive new/dev/build/publish
│   └── main.py          # CLI entrypoint
└── templates/           # NEW - Project scaffolding templates
    └── default/         # Default project template

tests/
├── contract/
│   ├── test_schema_export.py      # Schema export contracts
│   ├── test_mcp_generation.py     # MCP generation contracts
│   └── test_rest_generation.py    # REST generation contracts
├── integration/
│   ├── test_spec_workflow.py      # End-to-end spec export
│   ├── test_mcp_workflow.py       # End-to-end MCP serving
│   └── test_rest_workflow.py      # End-to-end REST serving
└── unit/
    ├── test_schema_generator.py   # Schema generator unit tests
    ├── test_mcp_generator.py      # MCP generator unit tests
    └── test_rest_generator.py     # REST generator unit tests
```

**Structure Decision**: Single project structure (existing `src/hive/`). New modules added as subpackages following established patterns from `generators/`, `runtime/`, `types/`.

## Complexity Tracking

> No Constitution Check violations requiring justification.

## Milestones Overview

| Milestone | Priority | Dependencies | Key Deliverables |
|-----------|----------|--------------|------------------|
| 3.1 Specification Export | P1 | None (uses existing registry) | `schema.py`, `spec/export.py`, `spec/diff.py`, CLI commands |
| 3.2 MCP Server | P2 | M3.1 (schema generation) | `mcp.py`, FastMCP integration |
| 3.3 REST API | P3 | M3.1 (schema generation) | `rest.py`, FastAPI integration |
| 3.4 Project Tooling | P4 | M3.1-3.3 functional | `cli/project.py`, templates |
| 3.5 TOML Export | P5 | M3.1 (JSON export) | TOML serializer in `spec/export.py` |

## Research Questions (Phase 0)

1. **JSON Schema Draft 2020-12 compliance**: How to map Pydantic/beartype constraints to JSON Schema?
2. **FastMCP integration**: Best practices for MCP tool definition and transport handling?
3. **FastAPI generation patterns**: How to dynamically generate endpoints from registry?
4. **Specification diff algorithms**: Existing libraries or custom implementation?
5. **Hot reload implementation**: watchfiles vs watchdog vs Textual's built-in?

**All research questions resolved** → See [research.md](research.md)

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion.*

| Principle | Status | Evidence/Notes |
|-----------|--------|----------------|
| **I. Specification-First** | ✅ PASS | All generators derive from registry; schemas in data-model.md match registry types |
| **II. CLI-First Architecture** | ✅ PASS | All CLI commands in contracts/ support `--json`, exit codes documented |
| **III. Test-First Development** | ⏳ READY | Contract schemas define test targets; /speckit.tasks will generate test-first tasks |
| **IV. Triple Interface Consistency** | ✅ PASS | Same Specification model exports to JSON, TOML, MCP, REST |
| **V. Simplicity & YAGNI** | ✅ PASS | No speculative features; MCP/REST optional dependencies |
| **Technology Stack** | ✅ PASS | FastMCP, FastAPI, watchfiles, deepdiff all researched and justified |

**Gate Result**: PASS - Ready for task generation
