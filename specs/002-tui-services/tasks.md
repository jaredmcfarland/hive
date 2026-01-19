# Tasks: TUI Generation and Service Layer

**Input**: Design documents from `/specs/002-tui-services/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per Constitution Principle III (Test-First Development).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/hive/`, `tests/` at repository root
- Test files in `tests/unit/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and package structure

- [x] T001 Add textual>=0.50.0 and keyring>=25.0.0 to pyproject.toml dependencies
- [x] T002 Add pytest-textual-snapshot>=1.0.0 to pyproject.toml dev dependencies
- [x] T003 [P] Create src/hive/tui/__init__.py with public exports
- [x] T004 [P] Create src/hive/tui/widgets/__init__.py with widget exports
- [x] T005 [P] Create src/hive/runtime/services.py module stub
- [x] T006 [P] Create tests/unit/tui/ directory structure
- [x] T007 [P] Create tests/unit/services/ directory structure
- [x] T008 Run `uv sync --dev` to install new dependencies

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types and registry extensions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Add ServiceRegistration dataclass to src/hive/core/types.py
- [x] T010 Add QueryBinding dataclass to src/hive/core/types.py
- [x] T011 Add CredentialSpec dataclass to src/hive/core/types.py
- [x] T012 Extend ScreenRegistration with queries field in src/hive/core/types.py
- [x] T013 Add register_service method to ApplicationRegistry in src/hive/core/registry.py
- [x] T014 Add list_services and get_service methods to ApplicationRegistry in src/hive/core/registry.py
- [x] T015 Add CredentialError exception to src/hive/errors.py
- [x] T016 Add ConfigurationError exception to src/hive/errors.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Generate TUI Application (Priority: P1) 🎯 MVP

**Goal**: Framework users can generate a working Textual app from @screen decorated classes with header, footer, and navigation

**Independent Test**: Create app with two @screen classes, verify navigation via keybindings works

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T017 [P] [US1] Contract test for @screen decorator in tests/unit/tui/test_screen_registration.py
- [x] T018 [P] [US1] Contract test for HiveApp generation in tests/unit/tui/test_app_generation.py
- [x] T019 [P] [US1] Integration test for screen navigation in tests/integration/test_tui_full_app.py

### Implementation for User Story 1

- [x] T020 [US1] Update @screen decorator to accept queries parameter in src/hive/core/decorators.py
- [x] T021 [US1] Implement HiveScreen base class with reactive data/loading/error in src/hive/tui/screens.py
- [x] T022 [US1] Implement ScreenContext extending ExecutionContext in src/hive/tui/screens.py
- [x] T023 [US1] Implement HiveApp with registry binding in src/hive/tui/app.py
- [x] T024 [US1] Implement screen installation and keybinding generation in HiveApp
- [x] T025 [US1] Implement basic HiveHeader widget in src/hive/tui/widgets/header.py
- [x] T026 [US1] Implement basic HiveFooter widget in src/hive/tui/widgets/footer.py
- [x] T027 [US1] Implement generate_tui_app function in src/hive/generators/tui.py
- [x] T028 [US1] Add TUI generator exports to src/hive/generators/__init__.py
- [x] T029 [US1] Add tui module exports to src/hive/__init__.py

**Checkpoint**: User Story 1 complete - TUI app generates with working navigation

---

## Phase 4: User Story 2 - Query Data Binding (Priority: P2)

**Goal**: Screens automatically load and display @query results with loading states

**Independent Test**: Create screen with query-bound table, verify data loads on mount

**Dependencies**: Requires US1 complete (HiveScreen, HiveApp)

### Tests for User Story 2

- [x] T030 [P] [US2] Contract test for QueryBinding execution in tests/unit/tui/test_query_binding.py
- [x] T031 [P] [US2] Integration test for data loading flow in tests/integration/test_tui_full_app.py

### Implementation for User Story 2

- [x] T032 [US2] Implement QueryBinding executor in src/hive/tui/binding.py
- [x] T033 [US2] Add load_query worker method to HiveScreen in src/hive/tui/screens.py
- [x] T034 [US2] Add refresh_data method to HiveScreen in src/hive/tui/screens.py
- [x] T035 [US2] Integrate query cache_ttl checking with loading logic in src/hive/tui/binding.py
- [x] T036 [US2] Add DataLoaded and DataError events in src/hive/tui/screens.py
- [x] T037 [US2] Add query validation at app startup (raise ConfigurationError if query not found)

**Checkpoint**: User Story 2 complete - screens load data automatically

---

## Phase 5: User Story 3 - Service Layer with Credentials (Priority: P3)

**Goal**: Define services with @service decorator, access lazily via ctx.services with credential resolution

**Independent Test**: Define service with mock credentials, access via ctx.services, verify instantiation

**Dependencies**: None (independent of TUI, works in CLI too)

### Tests for User Story 3

- [x] T038 [P] [US3] Contract test for @service decorator in tests/unit/services/test_service_decorator.py
- [x] T039 [P] [US3] Unit test for credential resolution in tests/unit/services/test_credential_resolution.py
- [x] T040 [P] [US3] Unit test for service lifecycle in tests/unit/services/test_service_lifecycle.py

### Implementation for User Story 3

- [x] T041 [US3] Implement @service decorator in src/hive/core/decorators.py
- [x] T042 [US3] Implement _resolve_credentials function in src/hive/runtime/services.py
- [x] T043 [US3] Implement ServiceProxy class with __getattr__ in src/hive/runtime/services.py
- [x] T044 [US3] Implement service caching in ServiceProxy in src/hive/runtime/services.py
- [x] T045 [US3] Implement cleanup_services method in ServiceProxy
- [x] T046 [US3] Add services property to ExecutionContext in src/hive/runtime/context.py
- [x] T047 [US3] Wire cleanup into ExecutionContext __aexit__ in src/hive/runtime/context.py
- [x] T048 [US3] Ensure credentials never appear in logs or error messages

**Checkpoint**: User Story 3 complete - services work with credential management

---

## Phase 6: User Story 4 - Command Palette (Priority: P4)

**Goal**: Open palette via Ctrl+P, search commands, execute with parameter input

**Independent Test**: Open palette, search for command, submit parameters, verify execution

**Dependencies**: Requires US1 (TUI app running)

### Tests for User Story 4

- [x] T049 [P] [US4] Unit test for CommandPalette filtering in tests/unit/tui/test_widgets.py
- [x] T050 [P] [US4] Unit test for ParameterModal form generation in tests/unit/tui/test_widgets.py
- [x] T051 [P] [US4] Integration test for command execution flow in tests/integration/test_tui_full_app.py

### Implementation for User Story 4

- [x] T052 [US4] Implement CommandPalette widget with fuzzy search in src/hive/tui/widgets/palette.py
- [x] T053 [US4] Implement ParameterModal with dynamic form generation in src/hive/tui/widgets/modal.py
- [x] T054 [US4] Add parameter type to widget mapping (str→Input, bool→Switch, etc.) in modal.py
- [x] T055 [US4] Wire CommandPalette to Ctrl+P keybinding in HiveApp
- [x] T056 [US4] Implement command execution via same path as CLI
- [x] T057 [US4] Add result display via notification in HiveApp

**Checkpoint**: User Story 4 complete - command palette fully functional

---

## Phase 7: User Story 5 - Standard Widgets (Priority: P5)

**Goal**: Provide themed, reusable widgets: HiveHeader, HiveFooter, HiveDataTable

**Independent Test**: Create screen with each widget, verify rendering and behavior

**Dependencies**: Requires US1 (basic widgets exist), US2 (query binding for DataTable)

### Tests for User Story 5

- [x] T058 [P] [US5] Unit test for HiveHeader display in tests/unit/tui/test_widgets.py
- [x] T059 [P] [US5] Unit test for HiveFooter keybinding display in tests/unit/tui/test_widgets.py
- [x] T060 [P] [US5] Unit test for HiveDataTable column generation in tests/unit/tui/test_widgets.py
- [x] T061 [P] [US5] Snapshot test for widget appearance in tests/snapshots/

### Implementation for User Story 5

- [x] T062 [US5] Enhance HiveHeader with version and screen title display in src/hive/tui/widgets/header.py
- [x] T063 [US5] Enhance HiveFooter with dynamic keybinding updates from registry in src/hive/tui/widgets/footer.py
- [x] T064 [US5] Implement HiveDataTable with auto-column generation from Pydantic schema in src/hive/tui/widgets/table.py
- [x] T065 [US5] Add sorting support to HiveDataTable
- [x] T066 [US5] Add row selection events to HiveDataTable
- [x] T067 [US5] Add loading/error/empty state display to HiveDataTable
- [x] T067b [US5] Implement minimum terminal size detection with warning in src/hive/tui/app.py
- [x] T068 [US5] Create default TCSS stylesheet for Hive widgets in src/hive/tui/default.tcss
- [x] T069 [US5] Export all widgets from src/hive/tui/widgets/__init__.py

**Checkpoint**: User Story 5 complete - all standard widgets ready

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Test utilities, documentation, and final integration

- [x] T070 [P] Implement create_test_app helper in src/hive/testing/tui.py
- [x] T071 [P] Implement TUI-specific test fixtures in src/hive/testing/tui.py
- [x] T072 [P] Add TUI testing exports to src/hive/testing/__init__.py
- [x] T073 Run all tests and verify 84%+ coverage (384 tests pass, 84.67% coverage)
- [x] T074 Run ruff check and pyright, fix any issues
- [x] T075 Validate quickstart.md examples work end-to-end (8 validation tests pass)
- [x] T076 [P] Add docstrings to all public APIs (interrogate 99.3% achieved)

### NFR Validation (Success Criteria)

- [x] T077 [P] Verify screen navigation responds within 100ms (SC-002) in tests/integration/test_tui_performance.py
- [x] T078 [P] Verify query-bound tables display within 500ms of mount (SC-003) in tests/integration/test_tui_performance.py
- [x] T079 [P] Test all widgets render correctly at 80x24 terminal minimum (SC-006) in tests/integration/test_tui_performance.py
- [x] T080 [P] Benchmark service instantiation overhead under 50ms (SC-007) in tests/integration/test_tui_performance.py
- [x] T081 [P] Performance test command palette filters 100+ commands under 100ms (SC-008) in tests/integration/test_tui_performance.py

**Checkpoint**: Phase 8 complete - All polish tasks and NFR validation complete

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup → Phase 2: Foundational → User Stories (Phase 3+)
                                         ↓
                              ┌──────────┴──────────┐
                              │                     │
                         US1 (P1)              US3 (P3)
                         MVP TUI            Service Layer
                              │              (independent)
                              ↓
                         US2 (P2)
                       Query Binding
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
               US4 (P4)            US5 (P5)
            Command Palette      Std Widgets
                    │                   │
                    └─────────┬─────────┘
                              ↓
                     Phase 8: Polish
```

### User Story Dependencies

| Story | Depends On | Can Run In Parallel With |
|-------|------------|-------------------------|
| US1 | Foundational | US3 |
| US2 | US1 | US3 |
| US3 | Foundational | US1, US2 |
| US4 | US1 | US5 |
| US5 | US1, US2 | US4 |

### Parallel Opportunities

**Phase 1 (all parallel)**:
```
T003, T004, T005, T006, T007 can all run together
```

**Phase 3 US1 Tests (parallel)**:
```
T017, T018, T019 can all run together
```

**Phase 3 US1 Widgets (parallel)**:
```
T025 (header), T026 (footer) can run together
```

**Phase 5 US3 (parallel with US1/US2)**:
```
T038, T039, T040, T041-T048 can run independently of TUI work
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test TUI generation independently
5. Deploy/demo if ready

### Recommended Order

1. Setup (T001-T008)
2. Foundational (T009-T016)
3. **US1** (T017-T029) - MVP: Basic TUI works
4. **US3** (T038-T048) - Services work (can parallel with US2)
5. **US2** (T030-T037) - Data binding works
6. **US4** (T049-T057) - Command palette works
7. **US5** (T058-T069) - Widgets polished
8. Polish (T070-T081)

### Task Counts

| Phase | Tasks | Parallel Tasks |
|-------|-------|----------------|
| Setup | 8 | 5 |
| Foundational | 8 | 0 |
| US1 (MVP) | 13 | 5 |
| US2 | 8 | 2 |
| US3 | 11 | 3 |
| US4 | 9 | 3 |
| US5 | 13 | 4 |
| Polish | 12 | 9 |
| **Total** | **82** | **31** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently completable and testable
- Verify tests fail before implementing (Test-First per Constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US3 (Services) is independent of TUI - can develop in parallel
