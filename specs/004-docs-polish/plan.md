# Implementation Plan: Documentation and Polish

**Branch**: `004-docs-polish` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-docs-polish/spec.md`

## Summary

Implement the final "polish" phase of Hive framework: documentation generation from specification (markdown + man pages), testing utilities for application developers (TestClient + conformance/property test generation), and four example applications demonstrating framework capabilities.

**Technical Approach**: Leverage existing infrastructure:
- `hive.spec.models.Specification` for documentation source
- `hive.types.introspection.extract_constraints()` for constraint documentation
- `hive.testing.MockExecutionContext` as TestClient foundation
- `hive.testing.strategy_for_type()` for property test generation

## Technical Context

**Language/Version**: Python 3.12+ (per constitution and project requirements)
**Primary Dependencies**:
- Typer + Rich (CLI generation, already in stack)
- pytest + hypothesis (testing, already in stack)
- Jinja2 (template rendering for doc generation)
- groff/troff (man page format, standard Unix)
**Storage**: SQLite (default), DuckDB (analytics example)
**Testing**: pytest with hypothesis for property-based testing
**Target Platform**: Cross-platform (macOS, Linux, Windows for CLI; Unix for man pages)
**Project Type**: Single project (extending existing `src/hive/` structure)
**Performance Goals**: Documentation generation < 5 seconds for 50 commands
**Constraints**: Must integrate with existing spec export pipeline
**Scale/Scope**: 4 example applications, ~20 new test utilities, 2 doc formats

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | PASS | Documentation generated from `Specification` model; TestClient reads from registry |
| **II. CLI-First Architecture** | PASS | `hive docs` command supports `--format` and `--output` flags; all examples include `--json` |
| **III. Test-First Development** | PASS | Tests written before implementation; conformance tests verify contracts |
| **IV. Triple Interface Consistency** | PASS | Documentation covers all interfaces equally; TestClient works for CLI/TUI/API |
| **V. Simplicity & YAGNI** | PASS | Using existing infrastructure (spec models, testing module); no new abstractions |

**Technology Stack Compliance**:
| Requirement | Compliance |
|-------------|------------|
| CLI: Typer + Rich | Using existing generators |
| Testing: pytest + hypothesis | Using existing integration |
| MCP/REST: FastMCP/FastAPI | Examples demonstrate optional features |
| Jinja2 for templates | DEVIATION: New dependency - justified for documentation templating |

**Deviation Justification**:
- Jinja2: Required for documentation templating. Standard Python templating library, minimal footprint, widely used. Alternative (f-strings/template strings) would be verbose and unmaintainable for multi-format output.

## Project Structure

### Documentation (this feature)

```text
specs/004-docs-polish/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
src/hive/
├── docs/                # NEW: Documentation generators (Milestone 4.1)
│   ├── __init__.py
│   ├── markdown.py      # Markdown documentation generator
│   ├── manpage.py       # Unix man page generator
│   └── templates/       # Jinja2 templates for output formats
│       ├── markdown/
│       │   ├── command.md.j2
│       │   ├── query.md.j2
│       │   ├── entity.md.j2
│       │   └── index.md.j2
│       └── manpage/
│           └── command.1.j2
├── testing/             # EXTEND: Add TestClient (Milestone 4.2)
│   ├── __init__.py      # Add TestClient export
│   ├── client.py        # NEW: TestClient implementation
│   ├── conformance.py   # NEW: Conformance test generator
│   ├── mocks.py         # Existing MockExecutionContext
│   ├── strategies.py    # Existing strategy_for_type
│   └── properties.py    # NEW: Property test generator
├── cli/
│   ├── docs.py          # NEW: hive docs command
│   └── test.py          # NEW: hive test generate-* commands

tests/
├── contract/            # Contract tests for new modules
│   ├── test_docs_contract.py
│   └── test_testing_contract.py
├── integration/
│   ├── test_docs_integration.py
│   └── test_testclient_integration.py
└── unit/
    ├── test_markdown_generator.py
    ├── test_manpage_generator.py
    ├── test_testclient.py
    ├── test_conformance_generator.py
    └── test_property_generator.py

examples/               # NEW: Example applications (Milestone 4.3)
├── minimal/            # Single command demo
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/minimal/__init__.py
│   └── tests/
├── crud/               # Entity CRUD with CLI + TUI
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/crud/__init__.py
│   └── tests/
├── api-client/         # Service integration demo
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/api_client/__init__.py
│   └── tests/
└── analytics/          # DuckDB + data processing
    ├── pyproject.toml
    ├── README.md
    ├── src/analytics/__init__.py
    └── tests/
```

**Structure Decision**: Single project extension pattern. New modules (`docs/`, `testing/client.py`, etc.) follow existing package structure. Examples are standalone projects in `examples/` directory to demonstrate real-world usage patterns.

## Complexity Tracking

No violations requiring justification. All additions follow existing patterns:
- `docs/` module parallels `generators/` structure
- `testing/client.py` extends existing testing module
- Examples are independent projects, not framework complexity

## Implementation Milestones

### Milestone 4.1: Documentation Generation

**Objectives**: Generate markdown and man page documentation from Hive specification.

**Components**:
1. `hive.docs.markdown` - Markdown generator using Jinja2 templates
2. `hive.docs.manpage` - Man page generator (troff format)
3. `hive.cli.docs` - `hive docs` CLI command

**Key Design Decisions**:
- Use Jinja2 templates for flexible output formatting
- Leverage existing `hive.spec.export.build_specification()` as data source
- Use `hive.types.introspection.extract_constraints()` for constraint descriptions
- Output structure: one file per command/query/entity, plus index

### Milestone 4.2: Testing Utilities

**Objectives**: Provide TestClient and test generation for Hive applications.

**Components**:
1. `hive.testing.TestClient` - High-level testing interface
2. `hive.testing.conformance` - Conformance test generator
3. `hive.testing.properties` - Property test generator

**Key Design Decisions**:
- TestClient wraps `MockExecutionContext` with convenience methods
- Conformance tests verify @requires/@ensures contracts
- Property tests use existing `strategy_for_type()` infrastructure
- Generated tests output to pytest-compatible format

### Milestone 4.3: Example Applications

**Objectives**: Demonstrate framework capabilities through reference implementations.

**Applications**:
1. **minimal**: Single command showing basic Hive pattern
2. **crud**: Entity CRUD with CLI + TUI, refinement types, contracts
3. **api-client**: Service integration with httpx, credential management
4. **analytics**: DuckDB backend, data processing, rich output

**Key Design Decisions**:
- Each example is a standalone uv project
- Examples reference Hive as a dependency (not local path for portability)
- Each demonstrates at least 3 Hive features
- All pass quality checks (ruff, pyright, pytest)

## Dependencies Between Milestones

```
Milestone 4.1 (Documentation)
    └── No dependencies, can start immediately

Milestone 4.2 (Testing)
    └── No dependencies, can start immediately

Milestone 4.3 (Examples)
    ├── Depends on 4.1: Examples use hive docs for their own docs
    └── Depends on 4.2: Examples use TestClient for testing
```

Milestones 4.1 and 4.2 can be developed in parallel. Milestone 4.3 should start after 4.1 and 4.2 are complete.
