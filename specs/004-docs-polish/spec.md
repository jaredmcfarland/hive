# Feature Specification: Documentation and Polish

**Feature Branch**: `004-docs-polish`
**Created**: 2026-01-24
**Status**: Draft
**Input**: User description: "Phase 4: Documentation and Polish - Documentation generation (markdown, man pages), Testing utilities (TestClient, conformance tests, property-based testing), and Example applications (minimal, CRUD, API client, analytics)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Application Documentation (Priority: P1)

As a Hive application developer, I want to automatically generate comprehensive documentation from my decorated code so that my users have accurate, up-to-date reference materials without manual documentation effort.

**Why this priority**: Documentation is essential for user adoption and understanding. Auto-generation from the specification ensures accuracy and reduces maintenance burden. This is the core deliverable of the "polish" phase.

**Independent Test**: Can be fully tested by running a documentation generation command on a Hive application and verifying the output contains all commands, queries, parameters, and constraints documented correctly.

**Acceptance Scenarios**:

1. **Given** a Hive application with commands, queries, and entities, **When** I run the documentation command, **Then** I receive markdown documentation covering all public interfaces with descriptions, parameters, and constraints.
2. **Given** a command with refinement type parameters (e.g., PositiveInt, Email), **When** documentation is generated, **Then** the parameter documentation includes human-readable constraint descriptions (e.g., "must be greater than 0", "valid email format").
3. **Given** a command with contract decorators (@requires, @ensures), **When** documentation is generated, **Then** the preconditions and postconditions are documented alongside the command.
4. **Given** an application with no docstrings, **When** documentation is generated, **Then** the system uses parameter names and types to create meaningful placeholder descriptions.

---

### User Story 2 - Test Commands with TestClient (Priority: P1)

As a Hive application developer, I want a testing client that lets me invoke my commands and queries in tests without boilerplate setup so that I can write focused, readable tests quickly.

**Why this priority**: Testing is fundamental to application quality. A clean testing interface directly impacts developer productivity and test coverage. Equal priority with documentation as both are essential for "polish."

**Independent Test**: Can be fully tested by writing a test that uses TestClient to invoke a command and assert on the result, with minimal setup code.

**Acceptance Scenarios**:

1. **Given** a Hive application, **When** I create a TestClient, **Then** I can invoke any registered command by name with parameters and receive the result.
2. **Given** a command that requires database access, **When** I use TestClient, **Then** an isolated test database is automatically provided and cleaned up after each test.
3. **Given** a query that returns entities, **When** I invoke it through TestClient, **Then** I receive typed results matching the query's return type.
4. **Given** a command that should fail validation, **When** I invoke it with invalid parameters, **Then** TestClient raises an appropriate exception with clear error details.
5. **Given** a command with service dependencies, **When** I use TestClient, **Then** I can inject mock services to isolate my tests.

---

### User Story 3 - Generate Man Pages (Priority: P2)

As a Hive application developer distributing a CLI tool, I want to generate Unix man pages from my specification so that users on Unix-like systems can access documentation using standard `man` commands.

**Why this priority**: Man pages are standard for CLI tools but not universally required. Lower priority than markdown docs which work everywhere.

**Independent Test**: Can be fully tested by generating a man page file and verifying it renders correctly with the `man` command and contains all expected sections.

**Acceptance Scenarios**:

1. **Given** a Hive application, **When** I run the man page generation command, **Then** I receive properly formatted man pages (troff/groff format) for the main CLI and each subcommand.
2. **Given** generated man pages, **When** I install them to the system man directory, **Then** `man myapp` displays the documentation correctly.
3. **Given** a command with examples in its docstring, **When** man pages are generated, **Then** the examples appear in the EXAMPLES section of the man page.

---

### User Story 4 - Generate Conformance Tests (Priority: P2)

As a Hive application developer, I want automatic generation of tests that verify my implementation matches my specification so that I catch specification drift early.

**Why this priority**: Conformance testing ensures specification-implementation alignment. Important for maintaining correctness but requires existing implementation to test against.

**Independent Test**: Can be fully tested by generating conformance tests for an application, running them, and verifying they validate that implemented behavior matches declared contracts.

**Acceptance Scenarios**:

1. **Given** a Hive application specification, **When** I run conformance test generation, **Then** I receive test files covering all commands and queries.
2. **Given** a command with @requires decorator, **When** conformance tests run, **Then** they verify the precondition is enforced (fails with invalid inputs).
3. **Given** a command with @ensures decorator, **When** conformance tests run, **Then** they verify the postcondition holds for valid inputs.
4. **Given** a query with cache_ttl specified, **When** conformance tests run, **Then** they verify caching behavior matches the declared TTL.

---

### User Story 5 - Learn from Example Applications (Priority: P2)

As a developer evaluating or learning Hive, I want reference implementations demonstrating real patterns so that I can understand best practices and quickly bootstrap my own applications.

**Why this priority**: Examples accelerate adoption and demonstrate framework capabilities. Essential for onboarding but not blocking core functionality.

**Independent Test**: Can be fully tested by following the example application's README to build and run it, then verifying all documented features work as described.

**Acceptance Scenarios**:

1. **Given** the minimal example application, **When** I clone and run it, **Then** I have a working CLI with a single command demonstrating the basic Hive pattern.
2. **Given** the CRUD example application, **When** I follow the tutorial, **Then** I can create, read, update, and delete entities through both CLI and TUI interfaces.
3. **Given** the API client example application, **When** I run it, **Then** it demonstrates service integration patterns including credential management and error handling.
4. **Given** the analytics example application, **When** I run it with sample data, **Then** it demonstrates data processing with alternative database backend and rich output formatting.

---

### User Story 6 - Property-Based Testing Integration (Priority: P3)

As a Hive application developer using refinement types, I want automatic generation of property-based tests so that my type constraints are thoroughly validated with diverse inputs.

**Why this priority**: Extends existing property-based testing infrastructure. Valuable but builds on existing `hive.testing.strategies` module rather than introducing new capability.

**Independent Test**: Can be fully tested by running generated property tests and verifying they produce valid inputs for all refinement types used in commands.

**Acceptance Scenarios**:

1. **Given** a command using refinement types (PositiveInt, Email, etc.), **When** I run property-based test generation, **Then** I receive tests that use appropriate strategies for each type.
2. **Given** a custom refinement type defined in my application, **When** property tests run, **Then** the framework introspects the type constraints to generate valid values.
3. **Given** generated property tests, **When** they run, **Then** any constraint violation in my command logic is caught by the hypothesis shrinking process.

---

### Edge Cases

- What happens when a command has no docstring or description?
  - Documentation generator uses parameter names and types to create basic descriptions, with a warning noting missing documentation.

- How does documentation handle deeply nested entity relationships?
  - Entities are documented individually with cross-references. Circular references are handled by reference rather than inline expansion.

- What happens when TestClient is used with commands that have side effects (email, external APIs)?
  - TestClient operates in isolation mode by default where services are replaced with no-op mocks. Developers can explicitly inject functional services when testing integration.

- How does man page generation handle commands with very long descriptions?
  - Long descriptions are wrapped appropriately per man page conventions. The NAME section uses a short summary; full description goes in DESCRIPTION.

- What happens when conformance tests are generated for a partial implementation?
  - Tests are generated for all declared specifications. Missing implementations cause test failures, helping identify incomplete work.

- How do example applications handle platform-specific differences?
  - Examples use cross-platform patterns. Platform-specific notes are included in documentation where necessary (e.g., path separators, credential storage).

## Requirements *(mandatory)*

### Functional Requirements

**Documentation Generation (Milestone 4.1)**

- **FR-001**: System MUST generate markdown documentation from a Hive application's registered commands, queries, and entities.
- **FR-002**: System MUST document all command/query parameters including name, type, description, default value, and any constraints from refinement types.
- **FR-003**: System MUST document preconditions and postconditions from @requires and @ensures decorators in human-readable format.
- **FR-004**: System MUST generate Unix man pages (troff format) for CLI commands with proper section structure (NAME, SYNOPSIS, DESCRIPTION, OPTIONS, EXAMPLES, SEE ALSO).
- **FR-005**: System MUST support output to file or stdout for both markdown and man page formats.
- **FR-006**: System MUST include entity documentation showing field names, types, descriptions, and relationships.
- **FR-007**: System MUST automatically extract constraint descriptions from refinement types (e.g., PositiveInt -> "integer greater than 0").

**Testing Utilities (Milestone 4.2)**

- **FR-008**: System MUST provide a TestClient class that can invoke any registered command or query by name.
- **FR-009**: TestClient MUST automatically provision an isolated test database for each test session.
- **FR-010**: TestClient MUST support dependency injection for service mocks.
- **FR-011**: TestClient MUST return typed results matching the command/query's declared return type.
- **FR-012**: TestClient MUST provide clear error messages when commands fail validation or raise exceptions.
- **FR-013**: System MUST generate conformance tests that verify implementations honor declared contracts (@requires, @ensures, @invariant).
- **FR-014**: Generated conformance tests MUST be runnable with standard test runners without additional configuration.
- **FR-015**: System MUST integrate with property-based testing to generate strategies for all refinement types used in command signatures.
- **FR-016**: Generated property tests MUST include shrinking support for debugging failing cases.

**Example Applications (Milestone 4.3)**

- **FR-017**: Project MUST include a minimal example application demonstrating basic Hive patterns with a single command.
- **FR-018**: Project MUST include a CRUD example application demonstrating entity management with CLI and TUI interfaces.
- **FR-019**: Project MUST include an API client example application demonstrating service integration and credential management.
- **FR-020**: Project MUST include an analytics example application demonstrating alternative database usage and data processing.
- **FR-021**: Each example application MUST include a README with setup instructions, feature explanations, and learning objectives.
- **FR-022**: Each example application MUST pass all quality checks (linting, type checking, tests) as configured in the main project.
- **FR-023**: Example applications MUST demonstrate verification stack usage (refinement types, contracts, property-based tests).

### Key Entities

- **DocumentationSpec**: Represents the extracted specification used for documentation generation, containing commands, queries, entities, and their metadata.
- **TestSession**: Represents an isolated test execution context with database, service mocks, and captured output.
- **ConformanceTest**: Represents a generated test case verifying a specific contract or behavior.
- **ExampleProject**: Represents a complete sample application with source code, tests, and documentation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Documentation Quality**

- **SC-001**: Generated documentation covers 100% of public commands, queries, and entities without manual intervention.
- **SC-002**: Developers can generate complete markdown documentation for their application in under 5 seconds for typical applications (up to 50 commands).
- **SC-003**: Generated man pages pass `man -l` validation without warnings on standard Unix systems.
- **SC-004**: Documentation accuracy: All parameter constraints are correctly represented in generated docs (verifiable by sampling 10 random commands).

**Testing Effectiveness**

- **SC-005**: TestClient reduces test setup code by 80% compared to manual ExecutionContext configuration (measured by line count comparison).
- **SC-006**: Developers can write and run a basic command test in under 2 minutes from starting the test file.
- **SC-007**: Conformance tests achieve 100% coverage of declared contracts (@requires, @ensures, @invariant).
- **SC-008**: Property-based test generation produces valid inputs for all 20+ refinement types in the verification stack.

**Example Application Quality**

- **SC-009**: New developers can run any example application within 5 minutes of cloning the repository (time from clone to first successful command).
- **SC-010**: Each example application demonstrates at least 3 distinct Hive features (measured by feature checklist per example).
- **SC-011**: Example applications collectively demonstrate all major Hive capabilities: CLI generation, TUI, entities, services, refinement types, contracts, and testing.
- **SC-012**: 90% of developers following example tutorials successfully complete them without external assistance (measurable via user testing).

**Overall Polish**

- **SC-013**: Framework documentation enables new developers to build a working application within 30 minutes.
- **SC-014**: Test coverage for new testing utilities is at least 90%.
- **SC-015**: All example applications include at least 3 passing tests demonstrating testing patterns.

## Assumptions

- Documentation format (markdown) is sufficient for most use cases; additional formats (HTML, PDF) can be derived from markdown if needed.
- Man page installation paths follow Unix conventions and are the user's responsibility; the framework generates but does not install.
- Test database cleanup happens automatically at test session end; long-running test sessions are acceptable.
- Example applications target developers with basic familiarity with the command line and testing concepts.
- Property-based testing uses the existing hypothesis integration; no new testing framework introduction.
- Analytics example uses DuckDB as mentioned in project context; this demonstrates pluggable database support.
