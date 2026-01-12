<!--
SYNC IMPACT REPORT
==================
Version Change: N/A → 1.0.0 (Initial ratification)
Added Principles:
  - I. Specification-First
  - II. CLI-First Architecture
  - III. Test-First Development
  - IV. Triple Interface Consistency
  - V. Simplicity & YAGNI
Added Sections:
  - Technology Stack
  - Development Workflow
Templates Requiring Updates:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md: ✅ Compatible (requirements format aligns)
  - .specify/templates/tasks-template.md: ✅ Compatible (test-first pattern supported)
Follow-up TODOs: None
-->

# Hive Constitution

## Core Principles

### I. Specification-First

Decorated Python code IS the specification. The `@command`, `@query`, `@entity`, `@screen`, and `@service` decorators constitute the machine-readable contract from which all interfaces derive.

**Rules**:
- Every interface (CLI, TUI, Python API, MCP, REST) MUST be generated from the specification, never written independently
- Type hints define the schema; docstrings define the documentation
- Changes to command signatures MUST propagate automatically to all generated interfaces
- Breaking changes MUST be detectable via specification diffing (`hive spec diff`)

**Rationale**: Single source of truth eliminates drift between interfaces and reduces maintenance burden.

### II. CLI-First Architecture

The command-line interface is the primary interface, designed for AI agents operating via terminal (e.g., Claude Code's bash tool) while remaining accessible to human power users.

**Rules**:
- Every command MUST work headlessly without interactive prompts
- Every command MUST support `--json` output for machine parsing
- Interactive prompts are conveniences, not requirements; `--yes` flags MUST bypass confirmations
- Commands MUST use conventional exit codes (0 success, non-zero failure)
- Output MUST be clean and suitable for piping/composition

**Rationale**: Terminal-agent-native design ensures AI agents can reliably consume and parse command output.

### III. Test-First Development

Tests MUST be written before implementation code. Red-Green-Refactor cycle is mandatory for all features.

**Rules**:
- Tests MUST be written and approved before implementation begins
- Tests MUST fail initially (Red phase) to prove they test the right thing
- Implementation MUST be minimal to make tests pass (Green phase)
- Refactoring MUST NOT change test behavior
- Contract tests MUST verify command signatures match specification
- Integration tests MUST verify cross-component interactions

**Rationale**: Test-first ensures specifications are executable and implementations are verifiable.

### IV. Triple Interface Consistency

CLI, TUI, and Python API MUST expose identical functionality with consistent behavior. Optional interfaces (MCP, REST) MUST also maintain this consistency.

**Rules**:
- Return types from commands MUST serialize identically across all interfaces
- Parameter names and types MUST match across CLI flags, TUI inputs, and Python function signatures
- Error handling MUST produce equivalent error information across all interfaces
- Documentation MUST be generated from the same docstrings for all interfaces

**Rationale**: Users and agents must be able to switch between interfaces without behavioral surprises.

### V. Simplicity & YAGNI

Start with the minimum viable implementation. Complexity MUST be justified.

**Rules**:
- Features MUST NOT be added speculatively ("we might need this later")
- Abstractions MUST NOT be created until the third use case appears
- Dependencies MUST be from the approved technology stack unless explicitly justified
- Generated code SHOULD be readable and debuggable, not clever
- Configuration options MUST have sensible defaults; most users should need zero configuration

**Rationale**: Terminal applications should be lightweight and fast. Unnecessary complexity defeats the purpose.

## Technology Stack

The following technologies are mandated for consistency and philosophical alignment:

| Component | Technology | Constraint |
|-----------|------------|------------|
| CLI | Typer + Rich | MUST use; same author ecosystem |
| TUI | Textual | MUST use; same team as Rich |
| Data Layer | SQLModel | MUST use; Pydantic + SQLAlchemy unified |
| Database (default) | SQLite | Default; DuckDB and PostgreSQL supported |
| HTTP Client | httpx | MUST use for external API calls |
| Credentials | keyring | MUST use for secure credential storage |
| MCP Server | FastMCP | MUST use when MCP enabled |
| REST API | FastAPI | MUST use when REST enabled |
| Configuration | Pydantic Settings | MUST use for typed configuration |

**Deviations** from this stack require documented justification in the implementation plan with specific technical reasoning.

## Development Workflow

### Feature Implementation Flow

1. **Specification**: Define decorated functions with full type hints and docstrings
2. **Contract Tests**: Write tests verifying the specification contract
3. **Implementation**: Implement the minimal code to pass tests
4. **Generation Verification**: Confirm all interfaces generate correctly
5. **Integration Tests**: Verify cross-component behavior

### Code Organization

```
src/hive/
├── core/           # Specification parsing and registry
├── generators/     # CLI, TUI, MCP, REST, Schema generators
├── runtime/        # Execution context (db, services, config, output)
└── testing/        # Test utilities and conformance testing
```

### Commit Standards

- Commits MUST be atomic (one logical change per commit)
- Commit messages MUST follow conventional commits format
- Breaking changes MUST be marked with `BREAKING CHANGE:` footer

## Governance

This constitution is the supreme authority for Hive development practices. All implementation decisions, code reviews, and architectural choices MUST comply with these principles.

**Amendment Process**:
1. Propose amendment with rationale in a dedicated PR
2. Document impact on existing code and specifications
3. Update all affected templates and documentation
4. Increment constitution version appropriately

**Versioning Policy**:
- MAJOR: Principle removal or redefinition (backward incompatible)
- MINOR: New principle or section added
- PATCH: Clarifications, wording refinements

**Compliance Review**:
- Every PR MUST include a Constitution Check verifying adherence to all principles
- Violations MUST be documented with explicit justification if proceeding
- The CLAUDE.md file provides runtime guidance aligned with this constitution

**Version**: 1.0.0 | **Ratified**: 2026-01-11 | **Last Amended**: 2026-01-11
