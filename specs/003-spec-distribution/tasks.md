# Tasks: Specification and Distribution

**Input**: Design documents from `/specs/003-spec-distribution/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included per `--include-tests` flag. Tests follow Red-Green-Refactor pattern (Constitution III).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and directory structure

- [x] T001 Create directory structure per plan.md: `src/hive/spec/`, `src/hive/cli/`, `src/hive/templates/default/`
- [x] T002 Add new dependencies to pyproject.toml: fastmcp>=2.0,<3, fastapi>=0.100.0, uvicorn>=0.23.0, deepdiff>=8.0.0, watchfiles>=1.0.0, tomli-w>=1.0.0
- [x] T003 [P] Create `src/hive/spec/__init__.py` with public API exports
- [x] T004 [P] Create `src/hive/cli/__init__.py` with CLI module structure
- [x] T005 [P] Create `src/hive/templates/__init__.py` for template loading
- [x] T006 [P] Create test directory structure: `tests/contract/`, `tests/integration/`, `tests/unit/` (already exists)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Foundational Tests (RED - must fail initially)

- [x] T007 [P] Create contract test for Specification model validation in `tests/contract/test_spec_models.py`
- [x] T008 [P] Create contract test for HiveSchemaGenerator in `tests/contract/test_schema_generator.py`
- [x] T009 [P] Create unit test for type mapping (Python → JSON Schema) in `tests/unit/test_type_mapping.py`

### Foundational Implementation (GREEN - make tests pass)

- [x] T010 [P] Create SpecificationMetadata model in `src/hive/spec/models.py`
- [x] T011 [P] Create ParameterSchema model in `src/hive/spec/models.py`
- [x] T012 [P] Create CommandSchema model in `src/hive/spec/models.py`
- [x] T013 [P] Create QuerySchema model in `src/hive/spec/models.py`
- [x] T014 [P] Create FieldSchema and RelationshipSchema models in `src/hive/spec/models.py`
- [x] T015 [P] Create EntitySchema model in `src/hive/spec/models.py`
- [x] T016 Create Specification container model in `src/hive/spec/models.py` (depends on T010-T015)
- [x] T017 Create CLI entrypoint in `src/hive/cli/main.py` with Typer app structure
- [x] T018 [P] Create HiveSchemaGenerator extending Pydantic's GenerateJsonSchema in `src/hive/generators/schema.py`
- [x] T019 Implement type mapping (Python → JSON Schema) in `src/hive/generators/schema.py` (depends on T018)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Export Specification for Cross-Language Consumption (Priority: P1) 🎯 MVP

**Goal**: Developers can export command/query specs as JSON Schema with constraint metadata and compare specifications

**Independent Test**: Run `hive spec export --format json`, verify output contains all types, constraints, descriptions

### Tests for User Story 1 (RED - must fail initially)

- [x] T020 [P] [US1] Contract test for `build_specification()` registry→Specification conversion in `tests/contract/test_spec_export.py`
- [x] T021 [P] [US1] Contract test for JSON Schema output validation against Draft 2020-12 in `tests/contract/test_spec_export.py`
- [x] T022 [P] [US1] Contract test for `diff_specifications()` in `tests/contract/test_spec_diff.py`
- [x] T023 [P] [US1] Contract test for breaking change detection in `tests/contract/test_spec_diff.py`
- [x] T024 [P] [US1] Unit test for constraint extraction (PositiveInt→minimum:1, Email→format:email) in `tests/unit/test_constraints.py`
- [x] T025 [P] [US1] Integration test for `hive spec export --format json` CLI in `tests/integration/test_spec_workflow.py`
- [x] T026 [P] [US1] Integration test for `hive spec diff` CLI in `tests/integration/test_spec_workflow.py`

### Implementation for User Story 1 (GREEN - make tests pass)

- [x] T027 [P] [US1] Create constraint extraction utility in `src/hive/spec/constraints.py` using `hive.types.introspection.extract_constraints()`
- [x] T028 [P] [US1] Create DiffItem model in `src/hive/spec/models.py`
- [x] T029 [P] [US1] Create SpecificationDiff model in `src/hive/spec/models.py`
- [x] T030 [US1] Implement `build_specification()` to convert registry to Specification model in `src/hive/spec/export.py`
- [x] T031 [US1] Implement JSON Schema export in `src/hive/spec/export.py` using HiveSchemaGenerator (depends on T019, T030)
- [x] T032 [US1] Implement specification diff using DeepDiff in `src/hive/spec/diff.py` (depends on T028, T029)
- [x] T033 [US1] Implement breaking change detection in `src/hive/spec/diff.py` (depends on T032)
- [x] T034 [US1] Create `hive spec export` CLI command in `src/hive/cli/spec.py` with --format, -o, --include-internal options
- [x] T035 [US1] Create `hive spec diff` CLI command in `src/hive/cli/spec.py` with --format, --fail-on-breaking options
- [x] T036 [US1] Register spec commands in CLI entrypoint `src/hive/cli/main.py`
- [x] T037 [US1] Add JSON output support (--json flag) to spec commands per CLI-first architecture

**Checkpoint**: User Story 1 complete - JSON Schema export and diff functional ✅

---

## Phase 4: User Story 2 - Expose Commands to AI Agents via MCP (Priority: P2)

**Goal**: AI agents (Claude, Cursor) can discover and invoke Hive commands as MCP tools

**Independent Test**: Run `hive mcp serve`, connect via Claude Desktop, verify tools appear and execute correctly

### Tests for User Story 2 (RED - must fail initially)

- [x] T038 [P] [US2] Contract test for MCPGenerator.generate() in `tests/contract/test_mcp_generation.py`
- [x] T039 [P] [US2] Contract test for command→tool conversion in `tests/contract/test_mcp_generation.py`
- [x] T040 [P] [US2] Contract test for MCP tool input schema generation in `tests/contract/test_mcp_generation.py`
- [x] T041 [P] [US2] Contract test for MCP error response format in `tests/contract/test_mcp_generation.py`
- [x] T042 [P] [US2] Unit test for optional FastMCP dependency guard in `tests/unit/test_mcp_optional.py`
- [x] T043 [P] [US2] Integration test for `hive mcp serve --transport stdio` in `tests/integration/test_mcp_workflow.py`
- [x] T044 [P] [US2] Integration test for `hive mcp serve --transport sse` in `tests/integration/test_mcp_workflow.py`

### Implementation for User Story 2 (GREEN - make tests pass)

- [x] T045 [P] [US2] Create MCPToolSchema model in `src/hive/spec/models.py`
- [x] T046 [P] [US2] Create MCPTool model in `src/hive/spec/models.py`
- [x] T047 [P] [US2] Create MCPServerConfig model in `src/hive/spec/models.py`
- [x] T048 [US2] Implement optional FastMCP import guard with graceful fallback in `src/hive/generators/mcp.py`
- [x] T049 [US2] Create MCPGenerator class in `src/hive/generators/mcp.py`
- [x] T050 [US2] Implement command-to-MCP-tool conversion in `src/hive/generators/mcp.py` (depends on T049)
- [x] T051 [US2] Implement tool input schema generation from command parameters in `src/hive/generators/mcp.py`
- [x] T052 [US2] Implement FastMCP server generation with @mcp.tool decorators in `src/hive/generators/mcp.py`
- [x] T053 [US2] Implement stdio transport support in `src/hive/generators/mcp.py`
- [x] T054 [US2] Implement SSE transport support with host/port config in `src/hive/generators/mcp.py`
- [x] T055 [US2] Implement MCP error handling (tool execution errors → MCP error responses) in `src/hive/generators/mcp.py`
- [x] T056 [US2] Create `hive mcp serve` CLI command in `src/hive/cli/mcp.py` with --transport, --host, --port, --include-queries options
- [x] T057 [US2] Register mcp commands in CLI entrypoint `src/hive/cli/main.py`

**Checkpoint**: User Story 2 complete - MCP server exposes commands as tools ✅

---

## Phase 5: User Story 3 - Generate REST API for Web Clients (Priority: P3)

**Goal**: Web clients can interact with Hive app via generated REST API with OpenAPI docs

**Independent Test**: Run `hive serve`, access /docs for Swagger UI, POST to /commands/{name}, GET /queries/{name}

**Dependency**: Requires US1 for /spec endpoint (JSON Schema export)

### Tests for User Story 3 (RED - must fail initially)

- [x] T058 [P] [US3] Contract test for RESTGenerator.generate() in `tests/contract/test_rest_generation.py`
- [x] T059 [P] [US3] Contract test for command→POST endpoint in `tests/contract/test_rest_generation.py`
- [x] T060 [P] [US3] Contract test for query→GET endpoint in `tests/contract/test_rest_generation.py`
- [x] T061 [P] [US3] Contract test for ValidationError response (HTTP 400) in `tests/contract/test_rest_generation.py`
- [x] T062 [P] [US3] Contract test for ExecutionError response (HTTP 500) in `tests/contract/test_rest_generation.py`
- [x] T063 [P] [US3] Unit test for optional FastAPI dependency guard in `tests/unit/test_rest_optional.py`
- [x] T064 [P] [US3] Unit test for authentication middleware (none, api_key, bearer) in `tests/unit/test_rest_auth.py`
- [x] T065 [P] [US3] Integration test for `hive serve` with OpenAPI docs at /docs in `tests/integration/test_rest_workflow.py`
- [x] T066 [P] [US3] Integration test for /health and /spec endpoints in `tests/integration/test_rest_workflow.py`

### Implementation for User Story 3 (GREEN - make tests pass)

- [x] T067 [P] [US3] Create RESTEndpoint model in `src/hive/spec/models.py`
- [x] T068 [P] [US3] Create RESTAPIConfig model in `src/hive/spec/models.py`
- [x] T069 [US3] Implement optional FastAPI import guard with graceful fallback in `src/hive/generators/rest.py`
- [x] T070 [US3] Create RESTGenerator class in `src/hive/generators/rest.py`
- [x] T071 [US3] Implement dynamic request model generation using `pydantic.create_model()` in `src/hive/generators/rest.py`
- [x] T072 [US3] Implement command → POST endpoint generation in `src/hive/generators/rest.py` (depends on T071)
- [x] T073 [US3] Implement query → GET endpoint generation in `src/hive/generators/rest.py` (depends on T071)
- [x] T074 [US3] Implement /health endpoint in `src/hive/generators/rest.py`
- [x] T075 [US3] Implement /spec endpoint returning JSON Schema in `src/hive/generators/rest.py` (depends on US1)
- [x] T076 [US3] Implement ValidationError response handling (HTTP 400) in `src/hive/generators/rest.py`
- [x] T077 [US3] Implement ExecutionError response handling (HTTP 500) in `src/hive/generators/rest.py`
- [x] T078 [US3] Implement configurable authentication middleware (none, api_key, bearer) in `src/hive/generators/rest.py` - bearer mode validates OAuth2 access tokens
- [x] T079 [US3] Create `hive serve` CLI command in `src/hive/cli/serve.py` with --host, --port, --reload, --workers, --auth options
- [x] T080 [US3] Register serve command in CLI entrypoint `src/hive/cli/main.py`

**Checkpoint**: User Story 3 complete - REST API with OpenAPI docs functional ✅

---

## Phase 6: User Story 4 - Scaffold and Manage Projects via CLI (Priority: P4)

**Goal**: Developers can scaffold new projects and manage development lifecycle via CLI

**Independent Test**: Run `hive new myapp`, verify structure created, run `hive dev` to start development server

### Tests for User Story 4 (RED - must fail initially)

- [x] T081 [P] [US4] Contract test for `hive new` project creation in `tests/contract/test_project_tooling.py`
- [x] T082 [P] [US4] Contract test for template variable substitution in `tests/contract/test_project_tooling.py`
- [x] T083 [P] [US4] Contract test for `hive build` artifact creation in `tests/contract/test_project_tooling.py`
- [x] T084 [P] [US4] Unit test for hot reload file watching in `tests/unit/test_hot_reload.py`
- [x] T085 [P] [US4] Integration test for `hive new myapp` project scaffolding in `tests/integration/test_project_workflow.py`
- [x] T086 [P] [US4] Integration test for `hive dev` development server in `tests/integration/test_project_workflow.py`

### Implementation for User Story 4 (GREEN - make tests pass)

- [x] T087 [P] [US4] Create TemplateFile model in `src/hive/spec/models.py`
- [x] T088 [P] [US4] Create ProjectTemplate model in `src/hive/spec/models.py`
- [x] T089 [US4] Create default project template files in `src/hive/templates/default/` (pyproject.toml.j2, README.md.j2, app.py.j2, etc.)
- [x] T090 [US4] Implement template variable substitution ({{name}}, {{author}}, etc.) in `src/hive/cli/project.py`
- [x] T091 [US4] Implement `hive new` command in `src/hive/cli/project.py` with --features, --template, --force options
- [x] T092 [US4] Implement hot reload using watchfiles in `src/hive/cli/project.py`
- [x] T093 [US4] Implement `hive dev` command in `src/hive/cli/project.py` with --interfaces, --rest-port, --mcp-port options
- [x] T094 [US4] Implement `hive build` command in `src/hive/cli/project.py` with --format, --clean options (wraps uv build)
- [x] T095 [US4] Implement `hive publish` command in `src/hive/cli/project.py` with --repository, --dry-run options (wraps uv publish)
- [x] T096 [US4] Register project commands in CLI entrypoint `src/hive/cli/main.py`

**Checkpoint**: User Story 4 complete - Full project lifecycle management via CLI

---

## Phase 7: User Story 5 - Export Specification in TOML Format (Priority: P5)

**Goal**: Developers can export specifications as human-readable TOML

**Independent Test**: Run `hive spec export --format toml`, verify valid TOML output with equivalent content to JSON

**Dependency**: Extends US1 export functionality

### Tests for User Story 5 (RED - must fail initially)

- [x] T097 [P] [US5] Contract test for TOML serialization output in `tests/contract/test_spec_export.py`
- [x] T098 [P] [US5] Contract test for TOML/JSON equivalence in `tests/contract/test_spec_export.py`
- [x] T099 [P] [US5] Integration test for `hive spec export --format toml` CLI in `tests/integration/test_spec_workflow.py`

### Implementation for User Story 5 (GREEN - make tests pass)

- [x] T100 [US5] Implement TOML serialization in `src/hive/spec/export.py` using tomli-w
- [x] T101 [US5] Add --format toml support to `hive spec export` in `src/hive/cli/spec.py`
- [x] T102 [US5] Ensure TOML/JSON equivalence (same data, different format) in export logic

**Checkpoint**: User Story 5 complete - TOML export functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, validation, and cleanup

- [x] T103 [P] Update `src/hive/__init__.py` to export new public APIs (export_specification, diff_specifications, MCPGenerator, RESTGenerator)
- [x] T104 [P] Add docstrings to all public functions per 95% coverage requirement
- [x] T105 Run pyright strict mode and fix any type errors
- [x] T106 Run ruff check and format, fix any issues
- [x] T107 Run interrogate docstring coverage check
- [x] T108 Run quickstart.md validation scenarios
- [x] T109 Update CLAUDE.md with new CLI commands and module structure

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational (can run parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Foundational AND User Story 1 (needs schema export for /spec endpoint)
- **User Story 4 (Phase 6)**: Depends on Foundational (can run parallel with US1-US3)
- **User Story 5 (Phase 7)**: Depends on User Story 1 (extends export functionality)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

```
Foundational (Phase 2)
    ├── US1 (P1): JSON Schema Export ─────────┬──> US3 (P3): REST API
    │                                         │
    ├── US2 (P2): MCP Server (independent) ───┤
    │                                         │
    ├── US4 (P4): Project Tooling (independent)
    │
    └── US5 (P5): TOML Export (extends US1) ──┘
```

### Test-First Execution Order (Within Each Story)

1. **Write tests** (all [P] tests can run in parallel)
2. **Verify tests FAIL** (Red phase)
3. **Implement models** ([P] models can run in parallel)
4. **Implement services/logic** (sequential where dependencies exist)
5. **Implement CLI commands**
6. **Verify tests PASS** (Green phase)
7. **Refactor if needed** (tests must still pass)

### Parallel Opportunities

**Within Setup (Phase 1)**:
```
T003, T004, T005, T006 can run in parallel
```

**Within Foundational (Phase 2)**:
```
Tests: T007, T008, T009 can run in parallel
Models: T010, T011, T012, T013, T014, T015, T018 can run in parallel
Then T016, T019 after their dependencies
```

**Across User Stories** (after Foundational):
```
US1 and US2 and US4 can run in parallel
US3 waits for US1 (/spec endpoint depends on schema export)
US5 waits for US1 (extends export)
```

**Within User Story 1**:
```
Tests: T020-T026 can ALL run in parallel (RED phase)
Then: T027, T028, T029 can run in parallel (models/utilities)
Then: T030 -> T031, T032 -> T033 (sequential logic)
Then: T034-T037 (CLI commands)
```

**Within User Story 2**:
```
Tests: T038-T044 can ALL run in parallel (RED phase)
Then: T045, T046, T047 can run in parallel (models)
Then: T048 -> T049 -> T050-T055 (sequential generator)
Then: T056, T057 (CLI commands)
```

---

## Parallel Execution Example

**After Foundational Phase Completes**:

```bash
# Launch User Stories 1, 2, and 4 in parallel (different files, no conflicts)

# Agent 1: User Story 1 - Tests (RED phase)
Task: "Contract test for build_specification() in tests/contract/test_spec_export.py"
Task: "Contract test for JSON Schema output validation in tests/contract/test_spec_export.py"
Task: "Contract test for diff_specifications() in tests/contract/test_spec_diff.py"

# Agent 2: User Story 2 - Tests (RED phase)
Task: "Contract test for MCPGenerator.generate() in tests/contract/test_mcp_generation.py"
Task: "Contract test for command→tool conversion in tests/contract/test_mcp_generation.py"

# Agent 3: User Story 4 - Tests (RED phase)
Task: "Contract test for hive new project creation in tests/contract/test_project_tooling.py"
Task: "Contract test for template variable substitution in tests/contract/test_project_tooling.py"

# After tests written (all RED), continue with implementation in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - JSON Schema Export
4. **STOP and VALIDATE**: Test with `hive spec export --format json`
5. Deploy/demo if ready - this alone provides significant value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP: JSON Schema Export**
3. Add User Story 2 → Test independently → **MCP Integration**
4. Add User Story 3 → Test independently → **REST API**
5. Add User Story 4 → Test independently → **Full Project Tooling**
6. Add User Story 5 → Test independently → **TOML Export**
7. Each story adds value without breaking previous stories

### Recommended Execution Order

For a single developer (sequential with test-first):
1. Setup (T001-T006)
2. Foundational Tests (T007-T009) → verify RED
3. Foundational Implementation (T010-T019) → verify GREEN
4. US1 Tests (T020-T026) → verify RED
5. US1 Implementation (T027-T037) → verify GREEN
6. US2 Tests (T038-T044) → verify RED
7. US2 Implementation (T045-T057) → verify GREEN
8. US3 Tests (T058-T066) → verify RED
9. US3 Implementation (T067-T080) → verify GREEN
10. US4 Tests (T081-T086) → verify RED
11. US4 Implementation (T087-T096) → verify GREEN
12. US5 Tests (T097-T099) → verify RED
13. US5 Implementation (T100-T102) → verify GREEN
14. Polish (T103-T109)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Tests MUST fail before implementation** (Constitution III: Test-First Development)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Models can be added to same file (models.py) if they're in different sections
- src/hive/spec/models.py will contain all data models - coordinate to avoid conflicts
