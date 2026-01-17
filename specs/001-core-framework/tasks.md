# Tasks: Core Framework

**Input**: Design documents from `/specs/001-core-framework/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Status**: Complete (all phases finished)

**Tests**: Required per Constitution (Principle III: Test-First Development)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/hive/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md in src/hive/
- [X] T002 Create pyproject.toml with dependencies: typer, rich, sqlmodel, pydantic, pydantic-settings, aiosqlite
- [X] T003 [P] Create src/hive/__init__.py with version and placeholder exports
- [X] T004 [P] Create tests/conftest.py with shared pytest fixtures
- [X] T005 [P] Configure ruff for linting in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create src/hive/errors.py with HiveError, CommandError, ConfigurationError classes
- [X] T007 Create src/hive/core/__init__.py with submodule exports
- [X] T008 [P] Create src/hive/runtime/__init__.py with submodule exports
- [X] T009 [P] Create src/hive/generators/__init__.py with submodule exports

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Define Commands with Decorators (Priority: P1)

**Goal**: Enable developers to define commands using `@command` and `@query` decorators that automatically register with the application registry.

**Independent Test**: Decorate a function with `@command`, import the module, verify registration in registry with all metadata (name, parameters, return type, docstring).

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for @command decorator registration in tests/contract/test_decorators.py
- [X] T011 [P] [US1] Contract test for @query decorator registration in tests/contract/test_decorators.py
- [X] T012 [P] [US1] Contract test for registry query methods in tests/contract/test_registry.py
- [X] T013 [P] [US1] Contract test for duplicate name rejection in tests/contract/test_registry.py

### Implementation for User Story 1

- [X] T014 [P] [US1] Create ParameterInfo dataclass in src/hive/core/types.py
- [X] T015 [P] [US1] Create CommandRegistration dataclass in src/hive/core/types.py
- [X] T016 [P] [US1] Create QueryRegistration dataclass in src/hive/core/types.py
- [X] T017 [US1] Create ApplicationRegistry class with command/query storage in src/hive/core/registry.py
- [X] T018 [US1] Implement register_command() method in src/hive/core/registry.py
- [X] T019 [US1] Implement register_query() method in src/hive/core/registry.py
- [X] T020 [US1] Implement get_command(), list_commands() methods in src/hive/core/registry.py
- [X] T021 [US1] Implement duplicate name detection with error in src/hive/core/registry.py
- [X] T022 [US1] Create @command decorator factory in src/hive/core/decorators.py
- [X] T023 [US1] Create @query decorator factory in src/hive/core/decorators.py
- [X] T024 [US1] Implement parameter extraction using inspect.signature() in src/hive/core/decorators.py
- [X] T025 [US1] Implement return type extraction using get_type_hints() in src/hive/core/decorators.py
- [X] T026 [US1] Create App class with registry in src/hive/app.py
- [X] T027 [US1] Export App, command, query from src/hive/__init__.py

**Checkpoint**: User Story 1 complete - decorators register commands/queries with full metadata

---

## Phase 4: User Story 2 - Define Data Models as Entities (Priority: P2)

**Goal**: Enable developers to define data models with `@entity` decorator that registers them for database operations.

**Independent Test**: Decorate a SQLModel class with `@entity`, verify registration captures fields, types, and relationships.

### Tests for User Story 2

- [X] T028 [P] [US2] Contract test for @entity decorator registration in tests/contract/test_decorators.py
- [X] T029 [P] [US2] Contract test for entity field extraction in tests/contract/test_decorators.py
- [X] T030 [P] [US2] Contract test for entity relationship capture in tests/contract/test_registry.py

### Implementation for User Story 2

- [X] T031 [P] [US2] Create FieldInfo dataclass in src/hive/core/types.py
- [X] T032 [P] [US2] Create RelationshipInfo dataclass in src/hive/core/types.py
- [X] T033 [US2] Create EntityRegistration dataclass in src/hive/core/types.py
- [X] T034 [US2] Add entity storage to ApplicationRegistry in src/hive/core/registry.py
- [X] T035 [US2] Implement register_entity() method in src/hive/core/registry.py
- [X] T036 [US2] Implement get_entity(), list_entities() methods in src/hive/core/registry.py
- [X] T037 [US2] Create @entity decorator factory in src/hive/core/decorators.py
- [X] T038 [US2] Implement field extraction from SQLModel in src/hive/core/decorators.py
- [X] T039 [US2] Implement relationship detection in src/hive/core/decorators.py
- [X] T040 [US2] Export entity decorator from src/hive/__init__.py

**Checkpoint**: User Story 2 complete - entities register with schema metadata

---

## Phase 5: User Story 3 - Execute Commands with Context (Priority: P2)

**Goal**: Provide execution context to commands with database session, configuration, and output formatting.

**Independent Test**: Invoke a command, verify context provides working database session, configuration values, and output formatter.

### Tests for User Story 3

- [X] T041 [P] [US3] Integration test for context database session in tests/integration/test_context_lifecycle.py
- [X] T042 [P] [US3] Integration test for context transaction rollback on error in tests/integration/test_context_lifecycle.py
- [X] T043 [P] [US3] Unit test for config loading from env vars in tests/unit/test_config_loading.py
- [X] T044 [P] [US3] Unit test for OutputFormatter JSON mode in tests/unit/test_output_formatter.py
- [X] T045 [P] [US3] Unit test for OutputFormatter table mode in tests/unit/test_output_formatter.py

### Implementation for User Story 3

- [X] T046 [US3] Create AppSettings with Pydantic Settings in src/hive/runtime/config.py
- [X] T047 [US3] Create OutputFormat enum in src/hive/runtime/output.py
- [X] T048 [US3] Create OutputFormatter class with result(), info(), warning() methods in src/hive/runtime/output.py
- [X] T049 [US3] Implement JSON output mode in OutputFormatter in src/hive/runtime/output.py
- [X] T050 [US3] Implement table output mode with Rich in OutputFormatter in src/hive/runtime/output.py
- [X] T051 [US3] Create async database session factory in src/hive/runtime/database.py
- [X] T052 [US3] Create ExecutionContext class in src/hive/runtime/context.py
- [X] T053 [US3] Implement context manager __aenter__/__aexit__ in src/hive/runtime/context.py
- [X] T054 [US3] Implement transaction commit on success in src/hive/runtime/context.py
- [X] T055 [US3] Implement transaction rollback on exception in src/hive/runtime/context.py
- [X] T056 [US3] Wire context creation into command invocation in src/hive/app.py

**Checkpoint**: User Story 3 complete - commands receive working context with all services

---

## Phase 6: User Story 4 - Generate CLI from Decorated Commands (Priority: P3)

**Goal**: Automatically generate a Typer CLI from registered commands with help text, JSON output, and argument parsing.

**Independent Test**: Define commands, call `app.cli()`, invoke via CliRunner, verify correct output and argument parsing.

### Tests for User Story 4

- [X] T057 [P] [US4] Contract test for CLI generation from registry in tests/contract/test_cli_generation.py
- [X] T058 [P] [US4] Contract test for --json flag output in tests/contract/test_cli_generation.py
- [X] T059 [P] [US4] Contract test for --help output in tests/contract/test_cli_generation.py
- [X] T060 [P] [US4] Integration test for end-to-end command execution in tests/integration/test_end_to_end.py

### Implementation for User Story 4

- [X] T061 [US4] Create CLIGenerator class in src/hive/generators/cli.py
- [X] T062 [US4] Implement Typer app creation from registry in src/hive/generators/cli.py
- [X] T063 [US4] Implement command registration with Typer in src/hive/generators/cli.py
- [X] T064 [US4] Implement async-to-sync wrapper for Typer in src/hive/generators/cli.py
- [X] T065 [US4] Implement parameter mapping to Typer arguments/options in src/hive/generators/cli.py
- [X] T066 [US4] Implement --json flag injection on all commands in src/hive/generators/cli.py
- [X] T067 [US4] Implement --format flag for output format selection in src/hive/generators/cli.py
- [X] T068 [US4] Implement help text generation from docstrings in src/hive/generators/cli.py
- [X] T069 [US4] Add cli() method to App class in src/hive/app.py
- [X] T070 [US4] Wire output format from CLI flags to context in src/hive/generators/cli.py

**Checkpoint**: User Story 4 complete - full CLI generated from decorated commands

---

## Phase 7: User Story 5 - Define TUI Screens (Priority: P3)

**Goal**: Enable developers to define TUI screens with `@screen` decorator that registers navigation metadata.

**Independent Test**: Decorate a screen class with `@screen`, verify registration captures default flag and keybinding.

### Tests for User Story 5

- [X] T071 [P] [US5] Contract test for @screen decorator registration in tests/contract/test_decorators.py
- [X] T072 [P] [US5] Contract test for default screen validation (only one allowed) in tests/contract/test_registry.py
- [X] T073 [P] [US5] Contract test for keybinding uniqueness in tests/contract/test_registry.py

### Implementation for User Story 5

- [X] T074 [US5] Create ScreenRegistration dataclass in src/hive/core/types.py
- [X] T075 [US5] Add screen storage to ApplicationRegistry in src/hive/core/registry.py
- [X] T076 [US5] Implement register_screen() method in src/hive/core/registry.py
- [X] T077 [US5] Implement default screen validation (only one) in src/hive/core/registry.py
- [X] T078 [US5] Implement keybinding uniqueness validation in src/hive/core/registry.py
- [X] T079 [US5] Implement get_screen(), list_screens() methods in src/hive/core/registry.py
- [X] T080 [US5] Create @screen decorator factory in src/hive/core/decorators.py
- [X] T081 [US5] Export screen decorator from src/hive/__init__.py

**Checkpoint**: User Story 5 complete - screens register with navigation metadata

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T082 Implement app.validate() method to check all registrations in src/hive/app.py
- [X] T083 [P] Add Argument and Option types for Annotated hints in src/hive/core/types.py
- [X] T084 [P] Export Argument, Option from src/hive/__init__.py
- [X] T085 Add comprehensive docstrings to all public APIs
- [X] T086 Run quickstart.md validation - create and test example app
- [X] T087 Verify all tests pass with pytest
- [X] T088 Run ruff linting and fix issues

---

## Phase 9: User Story 6 - Refinement Types (Priority: P2)

**Goal**: Provide refinement types that validate at runtime with user-friendly error messages.

**Independent Test**: Use PositiveInt in a command, pass invalid value, verify clear error message.

### Tests for User Story 6

- [X] T089 [P] [US6] Unit test for numeric refinement types (PositiveInt, Port, etc.) in tests/unit/test_refinement_types.py
- [X] T090 [P] [US6] Unit test for string refinement types (Email, Slug, etc.) in tests/unit/test_refinement_types.py
- [X] T091 [P] [US6] Unit test for constraint extraction in tests/unit/test_refinement_types.py
- [X] T092 [P] [US6] Integration test for CLI error messages in tests/integration/test_cli_validation.py

### Implementation for User Story 6

- [X] T093 [P] [US6] Create src/hive/types/__init__.py with public exports
- [X] T094 [P] [US6] Create src/hive/types/primitives.py with base utilities
- [X] T095 [US6] Create numeric refinement types in src/hive/types/numeric.py
- [X] T096 [US6] Create string refinement types in src/hive/types/strings.py
- [X] T097 [US6] Implement extract_constraints() in src/hive/types/introspection.py
- [X] T098 [US6] Implement beartype error translation for CLI in src/hive/generators/cli.py
- [X] T099 [US6] Export refinement types from src/hive/__init__.py

**Checkpoint**: User Story 6 complete - refinement types with user-friendly CLI validation

---

## Phase 10: User Story 7 - Contract Decorators (Priority: P3)

**Goal**: Provide design-by-contract decorators for preconditions and postconditions.

**Independent Test**: Apply @requires decorator, violate precondition, verify CommandError with message.

### Tests for User Story 7

- [X] T100 [P] [US7] Unit test for @requires decorator in tests/unit/test_contracts.py
- [X] T101 [P] [US7] Unit test for @ensures decorator in tests/unit/test_contracts.py
- [X] T102 [P] [US7] Unit test for @invariant decorator in tests/unit/test_contracts.py

### Implementation for User Story 7

- [X] T103 [P] [US7] Create src/hive/contracts/__init__.py with public exports
- [X] T104 [US7] Implement @requires decorator in src/hive/contracts/decorators.py
- [X] T105 [US7] Implement @ensures decorator in src/hive/contracts/decorators.py
- [X] T106 [US7] Implement @invariant decorator in src/hive/contracts/decorators.py
- [X] T107 [US7] Export contract decorators from src/hive/__init__.py

**Checkpoint**: User Story 7 complete - contract decorators raise CommandError on violation

---

## Phase 11: User Story 8 - Testing Utilities (Priority: P3)

**Goal**: Provide Hypothesis strategies and mock context for property-based testing.

**Independent Test**: Generate strategy for PositiveInt, verify all values positive.

### Tests for User Story 8

- [X] T108 [P] [US8] Unit test for strategy_for_type() in tests/unit/test_strategies.py
- [X] T109 [P] [US8] Unit test for MockExecutionContext in tests/unit/test_strategies.py
- [X] T110 [P] [US8] Property test for refinement type strategies in tests/property/test_type_strategies.py

### Implementation for User Story 8

- [X] T111 [P] [US8] Create src/hive/testing/__init__.py with public exports
- [X] T112 [US8] Implement strategy_for_type() in src/hive/testing/strategies.py
- [X] T113 [US8] Implement MockExecutionContext in src/hive/testing/mocks.py
- [X] T114 [US8] Export testing utilities from src/hive/__init__.py

**Checkpoint**: User Story 8 complete - Hypothesis strategies auto-generate from types

---

## Phase 12: Verification Stack Polish

**Purpose**: Final verification and documentation for verification stack

- [X] T115 Update pyproject.toml with beartype, deal, hypothesis dependencies
- [X] T116 Run full test suite including property tests
- [X] T117 Update CLAUDE.md with verification stack documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - MVP, do first
- **User Story 2 (Phase 4)**: Depends on Foundational - can parallel with US3
- **User Story 3 (Phase 5)**: Depends on Foundational - can parallel with US2
- **User Story 4 (Phase 6)**: Depends on US1 + US3 (needs decorators and context)
- **User Story 5 (Phase 7)**: Depends on US1 (uses same decorator pattern)
- **Polish (Phase 8)**: Depends on all user stories being complete
- **User Story 6 (Phase 9)**: Depends on US4 (refinement types used in CLI)
- **User Story 7 (Phase 10)**: Depends on Foundational (uses error hierarchy)
- **User Story 8 (Phase 11)**: Depends on US6 (strategies for refinement types)
- **Verification Polish (Phase 12)**: Depends on US6, US7, US8 complete

### User Story Dependencies

```
Setup → Foundational → US1 (P1) → US4 (P3) → US6 (P2) → US8 (P3)
                    ↘        ↗              ↗
                      US3 (P2)              │
                    ↘                       │
                      US2 (P2) → US5 (P3)   │
                    ↘                       │
                      └─────── US7 (P3) ────┘
```

- **US1**: Foundation only - MVP candidate
- **US2**: Foundation only - can start after US1 or in parallel
- **US3**: Foundation only - can start after US1 or in parallel
- **US4**: Requires US1 (commands to generate) + US3 (context for execution)
- **US5**: Requires US1 (decorator pattern) - uses same registry pattern
- **US6**: Requires US4 (CLI integration for error messages)
- **US7**: Requires Foundational (error hierarchy for CommandError)
- **US8**: Requires US6 (strategies generate from refinement types)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Types/dataclasses before registry methods
- Registry methods before decorators
- Decorators before App integration

### Parallel Opportunities

- T003, T004, T005 (Setup)
- T007, T008, T009 (Foundational)
- T010, T011, T012, T013 (US1 tests)
- T014, T015, T016 (US1 types)
- T028, T029, T030 (US2 tests)
- T031, T032 (US2 types)
- T041, T042, T043, T044, T045 (US3 tests)
- T057, T058, T059, T060 (US4 tests)
- T071, T072, T073 (US5 tests)
- T083, T084 (Polish)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for @command decorator registration in tests/contract/test_decorators.py"
Task: "Contract test for @query decorator registration in tests/contract/test_decorators.py"
Task: "Contract test for registry query methods in tests/contract/test_registry.py"
Task: "Contract test for duplicate name rejection in tests/contract/test_registry.py"

# Launch all type definitions together:
Task: "Create ParameterInfo dataclass in src/hive/core/types.py"
Task: "Create CommandRegistration dataclass in src/hive/core/types.py"
Task: "Create QueryRegistration dataclass in src/hive/core/types.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test decorator registration independently
5. Demo: Show commands registering with full metadata

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Test → Demo (decorators work!)
3. US2 + US3 (parallel) → Test → Demo (entities + context work!)
4. US4 → Test → Demo (CLI generates!)
5. US5 → Test → Demo (screens register!)
6. Polish → Full validation

### Recommended Order (Solo Developer)

1. Setup (T001-T005)
2. Foundational (T006-T009)
3. US1 (T010-T027) - MVP
4. US3 (T041-T056) - Context needed for US4
5. US4 (T057-T070) - CLI is primary deliverable
6. US2 (T028-T040) - Entity registration
7. US5 (T071-T081) - Screen registration
8. Polish (T082-T088)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [USn] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (Red-Green-Refactor)
- Commit after each task or logical group
- Constitution requires Test-First: write tests before implementation
