# Feature Specification: Core Framework

**Feature Branch**: `001-core-framework`
**Created**: 2026-01-11
**Status**: Draft
**Input**: Phase 1: Core Framework - Decorator system, registry, execution context, and CLI generation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Commands with Decorators (Priority: P1)

As a framework developer, I want to define application commands using simple decorators on my functions so that I can focus on business logic without manually configuring command-line interfaces.

**Why this priority**: This is the foundational capability. Without decorators, developers cannot define any application functionality. All other features depend on this working first.

**Independent Test**: Can be fully tested by decorating a function with `@command` and verifying it registers correctly. Delivers immediate value by proving the core pattern works.

**Acceptance Scenarios**:

1. **Given** a Python function with type-annotated parameters, **When** I apply the `@command` decorator, **Then** the function is registered in the application's command registry with its name, parameters, return type, and docstring preserved.

2. **Given** multiple decorated functions in the same module, **When** the module is imported, **Then** all decorated functions are collected in the registry without manual registration calls.

3. **Given** a function decorated with `@query`, **When** the module is imported, **Then** the function is registered separately from commands (queries are read-only operations).

4. **Given** a decorated function with a docstring, **When** I inspect the registry, **Then** the docstring is available for generating help text and documentation.

---

### User Story 2 - Define Data Models as Entities (Priority: P2)

As a framework developer, I want to define my data models with an `@entity` decorator so that the framework knows which models to manage for database operations and schema generation.

**Why this priority**: Data models are essential for most applications, but the decorator system must exist first. This enables persistent storage capabilities.

**Independent Test**: Can be fully tested by decorating a model class and verifying it registers with its schema information intact.

**Acceptance Scenarios**:

1. **Given** a model class with typed fields, **When** I apply the `@entity` decorator, **Then** the model is registered in the entity registry with field names, types, and constraints.

2. **Given** an entity with relationships to other entities, **When** I inspect the registry, **Then** the relationships are captured and queryable.

3. **Given** multiple entities in separate modules, **When** all modules are imported, **Then** all entities are collected in a single registry.

---

### User Story 3 - Execute Commands with Context (Priority: P2)

As a framework developer, I want my command functions to receive a context object providing database access, configuration, and output formatting so that I can perform operations without manual setup.

**Why this priority**: Commands need runtime services to be useful. Context injection is the standard pattern for providing these services cleanly.

**Independent Test**: Can be fully tested by invoking a command and verifying it receives a context with working database session and configuration.

**Acceptance Scenarios**:

1. **Given** a command function expecting a context parameter, **When** the command is invoked, **Then** the context is automatically provided with an active database session.

2. **Given** a command that reads configuration values, **When** the command is invoked, **Then** configuration is loaded from environment variables and/or configuration files.

3. **Given** a command that produces output, **When** the command returns a result, **Then** the output formatter renders it appropriately based on the requested format.

4. **Given** a command that fails, **When** an error occurs, **Then** the context handles cleanup (database rollback) and error formatting.

---

### User Story 4 - Generate CLI from Decorated Commands (Priority: P3)

As a framework developer, I want the framework to automatically generate a command-line interface from my decorated commands so that users can invoke my application from the terminal.

**Why this priority**: CLI generation is the primary output of the core framework, but it depends on decorators, registry, and context being in place first.

**Independent Test**: Can be fully tested by defining commands and invoking the generated CLI, verifying that arguments parse correctly and output renders as expected.

**Acceptance Scenarios**:

1. **Given** an application with registered commands, **When** I run the CLI with a command name and arguments, **Then** the corresponding function is invoked with parsed arguments.

2. **Given** a command with typed parameters, **When** I run the CLI with `--help`, **Then** help text shows parameter names, types, and descriptions from docstrings.

3. **Given** a command that returns a result, **When** I run with `--json` flag, **Then** the output is formatted as valid JSON.

4. **Given** a command that returns a result, **When** I run with default flags, **Then** the output is formatted as a human-readable table.

5. **Given** a command with optional parameters, **When** I omit optional arguments, **Then** default values are used.

---

### User Story 5 - Define TUI Screens (Priority: P3)

As a framework developer, I want to define terminal UI screens with a `@screen` decorator so that the framework can generate an interactive TUI alongside the CLI.

**Why this priority**: TUI is a core interface but can be deferred after CLI works. The decorator pattern established in P1 extends naturally to screens.

**Independent Test**: Can be fully tested by decorating a screen class and verifying it registers with navigation metadata (default, keybinding).

**Acceptance Scenarios**:

1. **Given** a screen class, **When** I apply the `@screen` decorator with `default=True`, **Then** the screen is registered as the initial screen for TUI launch.

2. **Given** multiple screens with keybindings, **When** I inspect the registry, **Then** each screen's keybinding is captured for navigation.

3. **Given** a screen marked as default, **When** another screen is also marked default, **Then** the system reports a configuration error (only one default allowed).

---

### Edge Cases

- What happens when two commands have the same name? System MUST reject duplicate registrations with a clear error message.
- What happens when a decorator is applied to an invalid target (e.g., class instead of function for @command)? System MUST raise a descriptive error at decoration time.
- How does the system handle commands with no return type annotation? System MUST accept them but issue a warning; output formatting may be limited.
- What happens when configuration is missing required values? System MUST fail fast with a clear error indicating which values are missing.
- How does the system handle database connection failures? Commands MUST receive a clear error before execution; partial state changes MUST NOT persist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Framework MUST provide decorators (`@command`, `@query`, `@entity`, `@screen`) that register definitions with a central application registry.
- **FR-002**: Registry MUST capture function/class names, parameter types, return types, docstrings, and decorator-specific metadata (e.g., `cache_ttl` for queries).
- **FR-003**: Registration MUST occur automatically at module import time without explicit registration calls.
- **FR-004**: Framework MUST provide an execution context object to commands containing database session, configuration, and output formatter.
- **FR-005**: Database session in context MUST support SQLModel async operations: `exec()` for queries, `get()` for lookup by ID, `add()` for staging, `commit()`, `rollback()`, `refresh()`.
- **FR-006**: Configuration MUST load from environment variables with optional file-based overrides.
- **FR-007**: Output formatter MUST support at minimum JSON and human-readable table formats.
- **FR-008**: CLI generator MUST produce a command-line interface with subcommands matching registered command names.
- **FR-009**: CLI MUST support `--json` flag on all commands for machine-readable output.
- **FR-010**: CLI MUST support `--help` flag showing parameter documentation from function docstrings and type hints.
- **FR-011**: CLI MUST parse arguments according to type hints (integers, strings, dates, booleans).
- **FR-012**: Framework MUST reject duplicate command/query/entity/screen names with descriptive error messages.
- **FR-013**: Framework MUST validate decorator usage at decoration time (e.g., @command on functions only).
- **FR-014**: Context MUST handle database transaction lifecycle (commit on success, rollback on failure).

### Key Entities

- **Command Registration**: Represents a decorated command function; captures name, parameter schema, return type, docstring, related entities.
- **Query Registration**: Represents a decorated query function; same as command plus cache settings (TTL).
- **Entity Registration**: Represents a decorated model class; captures class name, field schema, relationships.
- **Screen Registration**: Represents a decorated screen class; captures name, default flag, keybinding.
- **Application Registry**: Central collection holding all registrations; queryable by type (commands, queries, entities, screens).
- **Execution Context**: Runtime container providing database session, service registry, configuration, and output formatter to commands.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can define a new command in under 1 minute by writing a decorated function with type hints.
- **SC-002**: A simple application with 5 commands generates a working CLI with accurate help text for all commands.
- **SC-003**: Commands with database operations complete successfully with automatic transaction management (no manual commit/rollback).
- **SC-004**: JSON output from CLI is valid JSON parseable by standard tools (e.g., `jq`).
- **SC-005**: Configuration changes via environment variables take effect without code changes.
- **SC-006**: Invalid decorator usage produces error messages within 100ms at import time (fail fast).
- **SC-007**: Registry inspection returns complete metadata for all registered items programmatically.
- **SC-008**: A developer unfamiliar with the framework can follow documentation to create a working 3-command application within 30 minutes.

## Assumptions

- Developers will use standard Python type hints (PEP 484) for parameters and return types.
- Applications will typically define commands, queries, and entities across multiple modules that are imported by a main application module.
- The primary database for initial implementation is SQLite; other databases will be supported through the same interface.
- Environment variables follow standard naming conventions (uppercase, underscore-separated).
- TUI generation (Phase 2) will build on the screen registry established here but full TUI functionality is out of scope for this phase.
