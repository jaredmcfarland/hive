# Tasks: Documentation and Polish

**Input**: Design documents from `/specs/004-docs-polish/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US6)
- Include exact file paths in descriptions

> **Test-First Note**: Per Constitution III, tests MUST be written before implementation.
> Task ordering in this file reflects logical grouping, not development sequence.
> Within each phase, write test tasks FIRST, verify they fail (Red), then implement.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and new module structure

- [x] T001 Add Jinja2 dependency to pyproject.toml
- [x] T002 [P] Create src/hive/docs/__init__.py with module docstring and exports
- [x] T003 [P] Create src/hive/docs/templates/ directory structure
- [x] T004 [P] Create examples/ directory at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure shared across user stories

**⚠️ CRITICAL**: US1 and US3 both depend on doc generator base; US2, US4, US6 depend on TestClient base

- [x] T005 Create DocumentationConfig and DocumentationOutput models in src/hive/docs/models.py
- [x] T006 Create base documentation generator class in src/hive/docs/base.py with Jinja2 environment setup
- [x] T007 [P] Create base Jinja2 filters for constraint formatting in src/hive/docs/filters.py
- [x] T008 Update src/hive/cli/main.py to register new docs subcommand group
- [x] T008a Update src/hive/cli/main.py to register new test subcommand group

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Generate Application Documentation (Priority: P1) 🎯 MVP

**Goal**: Generate comprehensive markdown documentation from Hive specification

**Independent Test**: Run `hive docs --format markdown` on a Hive app and verify output contains all commands, queries, entities with constraints documented

### Implementation for User Story 1

- [x] T009 [P] [US1] Create markdown/base.md.j2 template in src/hive/docs/templates/markdown/
- [x] T010 [P] [US1] Create markdown/command.md.j2 template in src/hive/docs/templates/markdown/
- [x] T011 [P] [US1] Create markdown/query.md.j2 template in src/hive/docs/templates/markdown/
- [x] T012 [P] [US1] Create markdown/entity.md.j2 template in src/hive/docs/templates/markdown/
- [x] T013 [P] [US1] Create markdown/index.md.j2 template in src/hive/docs/templates/markdown/
- [x] T014 [US1] Implement MarkdownGenerator class in src/hive/docs/markdown.py
- [x] T015 [US1] Add constraint description extraction using hive.types.introspection in src/hive/docs/markdown.py
- [x] T016 [US1] Add contract documentation (@requires/@ensures) in src/hive/docs/markdown.py
- [x] T017 [US1] Implement `hive docs generate` command in src/hive/cli/docs.py with --format, --output flags, and stdout default (no --output = stdout)
- [x] T018 [US1] Add --json output support to hive docs command in src/hive/cli/docs.py
- [x] T019 [US1] Update src/hive/docs/__init__.py to export MarkdownGenerator
- [x] T020 [US1] Add unit tests in tests/unit/test_markdown_generator.py

**Checkpoint**: `hive docs --format markdown` generates complete documentation

---

## Phase 4: User Story 2 - Test Commands with TestClient (Priority: P1)

**Goal**: Provide TestClient for easy command/query testing without boilerplate

**Independent Test**: Write a test using TestClient to invoke a command and verify minimal setup code

### Implementation for User Story 2

- [x] T021 [P] [US2] Create TestSession dataclass in src/hive/testing/client.py
- [x] T022 [US2] Implement TestClient class in src/hive/testing/client.py with async context manager
- [x] T023 [US2] Add invoke() method to TestClient for command execution in src/hive/testing/client.py
- [x] T024 [US2] Add query() method to TestClient for query execution in src/hive/testing/client.py
- [x] T025 [US2] Add automatic in-memory SQLite database provisioning in src/hive/testing/client.py
- [x] T026 [US2] Add service mock injection support to TestClient in src/hive/testing/client.py
- [x] T027 [US2] Add get_output() method for captured output in src/hive/testing/client.py
- [x] T028 [US2] Add clear error messages for validation failures in src/hive/testing/client.py
- [x] T029 [US2] Update src/hive/testing/__init__.py to export TestClient
- [x] T030 [US2] Add unit tests in tests/unit/test_testclient.py
- [x] T031 [US2] Add integration tests in tests/integration/test_testclient_integration.py

**Checkpoint**: TestClient enables minimal-boilerplate command testing

---

## Phase 5: User Story 3 - Generate Man Pages (Priority: P2)

**Goal**: Generate Unix man pages (troff format) from Hive specification

**Independent Test**: Run `hive docs --format manpage` and verify `man -l output.1` renders correctly

### Implementation for User Story 3

- [x] T032 [P] [US3] Create manpage/command.1.j2 template in src/hive/docs/templates/manpage/
- [x] T033 [P] [US3] Create manpage/macros.j2 partial for troff macros in src/hive/docs/templates/manpage/
- [x] T034 [US3] Implement ManPageGenerator class in src/hive/docs/manpage.py
- [x] T035 [US3] Add proper troff escaping for special characters in src/hive/docs/manpage.py
- [x] T036 [US3] Add EXAMPLES section extraction from docstrings in src/hive/docs/manpage.py
- [x] T037 [US3] Add --format manpage support to hive docs command in src/hive/cli/docs.py (stdout default)
- [x] T038 [US3] Update src/hive/docs/__init__.py to export ManPageGenerator
- [x] T039 [US3] Add unit tests in tests/unit/test_manpage_generator.py

**Checkpoint**: `hive docs --format manpage` generates valid troff files

---

## Phase 6: User Story 4 - Generate Conformance Tests (Priority: P2)

**Goal**: Auto-generate tests verifying implementation honors declared contracts

**Independent Test**: Generate conformance tests for an app with @requires/@ensures and verify they catch violations

### Implementation for User Story 4

- [x] T040 [P] [US4] Create ConformanceTestCase model in src/hive/testing/conformance.py
- [x] T041 [US4] Implement contract extraction from registry in src/hive/testing/conformance.py
- [x] T042 [US4] Implement @requires test generation in src/hive/testing/conformance.py
- [x] T043 [US4] Implement @ensures test generation in src/hive/testing/conformance.py
- [x] T044 [US4] Implement @invariant test generation in src/hive/testing/conformance.py
- [x] T045 [US4] Add pytest-compatible code output in src/hive/testing/conformance.py
- [x] T046 [US4] Add `hive test generate-conformance` CLI command in src/hive/cli/test.py
- [x] T047 [US4] Update src/hive/testing/__init__.py to export conformance generator
- [x] T048 [US4] Add unit tests in tests/unit/test_conformance_generator.py

**Checkpoint**: `hive test generate-conformance` produces runnable pytest tests

---

## Phase 7: User Story 5 - Example Applications (Priority: P2)

**Goal**: Provide reference implementations demonstrating Hive patterns

**Independent Test**: Follow each example's README to build and run, verify documented features work

### Minimal Example

- [x] T049 [P] [US5] Create examples/minimal/pyproject.toml with hive dependency
- [x] T050 [P] [US5] Create examples/minimal/README.md with setup and learning objectives
- [x] T051 [US5] Implement single hello command in examples/minimal/src/minimal/__init__.py
- [x] T052 [US5] Add test using TestClient in examples/minimal/tests/test_hello.py
- [x] T053 [US5] Verify ruff/pyright pass for examples/minimal/

### CRUD Example

- [x] T054 [P] [US5] Create examples/crud/pyproject.toml with hive dependency
- [x] T055 [P] [US5] Create examples/crud/README.md with tutorial and features
- [x] T056 [US5] Implement Task entity with refinement types in examples/crud/src/crud/entities.py
- [x] T057 [US5] Implement CRUD commands with contracts in examples/crud/src/crud/commands.py
- [x] T058 [US5] Implement list query in examples/crud/src/crud/queries.py
- [ ] T059 [US5] Implement TUI screen in examples/crud/src/crud/screens.py (skipped - using in-memory storage)
- [x] T060 [US5] Add tests using TestClient in examples/crud/tests/
- [x] T061 [US5] Verify ruff/pyright/pytest pass for examples/crud/

### API Client Example

- [x] T062 [P] [US5] Create examples/api-client/pyproject.toml with hive and httpx
- [x] T063 [P] [US5] Create examples/api-client/README.md with service integration guide
- [x] T064 [US5] Implement @service decorated client in examples/api-client/src/api_client/services.py
- [x] T065 [US5] Implement commands using service in examples/api-client/src/api_client/commands.py
- [x] T066 [US5] Add credential management demo in examples/api-client/src/api_client/
- [x] T067 [US5] Add tests with service mocking in examples/api-client/tests/
- [x] T068 [US5] Verify ruff/pyright/pytest pass for examples/api-client/

### Analytics Example

- [x] T069 [P] [US5] Create examples/analytics/pyproject.toml with hive and duckdb
- [x] T070 [P] [US5] Create examples/analytics/README.md with DuckDB usage guide
- [x] T071 [US5] Implement DataPoint and Report entities in examples/analytics/src/analytics/entities.py
- [x] T072 [US5] Implement import/query commands in examples/analytics/src/analytics/commands.py
- [x] T073 [US5] Configure DuckDB as database backend in examples/analytics/src/analytics/
- [x] T074 [US5] Add rich output formatting in examples/analytics/src/analytics/
- [x] T075 [US5] Add tests in examples/analytics/tests/
- [x] T076 [US5] Verify ruff/pyright/pytest pass for examples/analytics/

**Checkpoint**: All 4 examples run independently with passing tests

---

## Phase 8: User Story 6 - Property-Based Testing Integration (Priority: P3)

**Goal**: Auto-generate hypothesis tests for commands using refinement types

**Independent Test**: Generate property tests for a command with PositiveInt parameter, verify hypothesis runs with valid inputs

### Implementation for User Story 6

- [ ] T077 [P] [US6] Create PropertyTestCase model in src/hive/testing/properties.py
- [ ] T078 [US6] Implement type-to-strategy mapping using existing strategy_for_type in src/hive/testing/properties.py
- [ ] T079 [US6] Implement property test generation for commands in src/hive/testing/properties.py
- [ ] T080 [US6] Implement property test generation for queries in src/hive/testing/properties.py
- [ ] T081 [US6] Add shrinking support configuration in src/hive/testing/properties.py
- [ ] T082 [US6] Add `hive test generate-properties` CLI command in src/hive/cli/test.py
- [ ] T083 [US6] Update src/hive/testing/__init__.py to export property generator
- [ ] T084 [US6] Add unit tests in tests/unit/test_property_generator.py

**Checkpoint**: `hive test generate-properties` produces runnable hypothesis tests

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration verification and cleanup

- [ ] T085 [P] Add contract tests for docs module in tests/contract/test_docs_contract.py
- [ ] T086 [P] Add contract tests for testing module in tests/contract/test_testing_contract.py
- [ ] T087 [P] Add integration tests for docs in tests/integration/test_docs_integration.py
- [ ] T088 Run quickstart.md validation steps for all user stories
- [ ] T089 Update CLAUDE.md with new commands and modules
- [ ] T090 Verify all tests pass with `uv run pytest`
- [ ] T090a Verify test coverage ≥90% for new modules with `uv run pytest --cov=src/hive/docs --cov=src/hive/testing --cov-fail-under=90`
- [ ] T091 Verify type checking passes with `uv run pyright`
- [ ] T092 Verify linting passes with `uv run ruff check .`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-4 (US1, US2)**: Can run in parallel after Phase 2
- **Phase 5-6 (US3, US4)**: Can run in parallel after Phase 2; US3 shares templates with US1
- **Phase 7 (US5)**: Depends on US1 (docs) and US2 (TestClient) completion
- **Phase 8 (US6)**: Can run after Phase 2; uses existing strategy_for_type
- **Phase 9 (Polish)**: Depends on all user stories

### User Story Dependencies

```
Phase 2 (Foundation)
    ├──► US1 (P1): Markdown Docs ──┬──► US5: Examples
    ├──► US2 (P1): TestClient ─────┘
    ├──► US3 (P2): Man Pages (shares templates with US1)
    ├──► US4 (P2): Conformance Tests
    └──► US6 (P3): Property Tests
```

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T005, T006, T007 can run in parallel (different files)

**Within US1 (Phase 3)**:
- T009-T013 (all templates) can run in parallel
- T014-T016 sequential (same file)

**Within US2 (Phase 4)**:
- T021 parallel with T022-T028 (different files)

**Within US5 (Phase 7)**:
- All 4 examples can run in parallel (independent projects)
- Within each example: pyproject.toml and README parallel, then sequential

**Across Phases (after Phase 2)**:
- US1 and US2 can run in parallel
- US3, US4, US6 can run in parallel with each other

---

## Parallel Example: Foundational Phase

```bash
# Launch foundational tasks in parallel:
Task: "Create DocumentationConfig/Output models in src/hive/docs/models.py"
Task: "Create base generator class in src/hive/docs/base.py"
Task: "Create Jinja2 filters in src/hive/docs/filters.py"
```

## Parallel Example: US1 Templates

```bash
# Launch all markdown templates in parallel:
Task: "Create markdown/base.md.j2 template"
Task: "Create markdown/command.md.j2 template"
Task: "Create markdown/query.md.j2 template"
Task: "Create markdown/entity.md.j2 template"
Task: "Create markdown/index.md.j2 template"
```

## Parallel Example: All Examples

```bash
# Launch all 4 example projects in parallel:
Task: "Create examples/minimal/ project"
Task: "Create examples/crud/ project"
Task: "Create examples/api-client/ project"
Task: "Create examples/analytics/ project"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Markdown Documentation)
4. **STOP and VALIDATE**: Run `hive docs --format markdown` on a test app
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Markdown Docs) → Test → Deploy (MVP!)
3. Add US2 (TestClient) → Test → Deploy
4. Add US3 (Man Pages) → Test → Deploy
5. Add US4 (Conformance Tests) → Test → Deploy
6. Add US5 (Examples) → Test → Deploy
7. Add US6 (Property Tests) → Test → Deploy
8. Polish phase → Final release

### Parallel Team Strategy

With multiple developers after Phase 2:
- Developer A: US1 + US3 (documentation)
- Developer B: US2 + US4 + US6 (testing utilities)
- Developer C: US5 (all examples)

---

## Summary

| Phase | User Story | Tasks | Parallel |
|-------|------------|-------|----------|
| 1 | Setup | T001-T004 | 3 |
| 2 | Foundational | T005-T008a | 2 |
| 3 | US1: Markdown Docs | T009-T020 | 5 |
| 4 | US2: TestClient | T021-T031 | 1 |
| 5 | US3: Man Pages | T032-T039 | 2 |
| 6 | US4: Conformance Tests | T040-T048 | 1 |
| 7 | US5: Examples | T049-T076 | 8 |
| 8 | US6: Property Tests | T077-T084 | 1 |
| 9 | Polish | T085-T092 | 3 |
| **Total** | | **94 tasks** | **26 parallelizable** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- US1 and US2 are both P1 priority - complete both for full MVP
