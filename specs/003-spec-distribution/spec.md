# Feature Specification: Specification and Distribution

**Feature Branch**: `003-spec-distribution`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "Phase 3: Specification and Distribution - JSON Schema export, TOML export, MCP server generation, REST API generation, and project tooling CLI"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Specification for Cross-Language Consumption (Priority: P1)

As a developer building a Hive application, I want to export my command and query specifications as JSON Schema so that I can share the schema with other teams, validate data in other languages, and document my API contract.

**Why this priority**: JSON Schema export is foundational - it enables specification diffing, drives MCP tool schema generation, and supports OpenAPI generation. All other milestones depend on accurate schema export with constraint metadata.

**Independent Test**: Can be fully tested by decorating commands/queries, running `hive spec export --format json`, and verifying the output contains all type constraints and descriptions.

**Acceptance Scenarios**:

1. **Given** a Hive app with decorated commands and queries, **When** I run `hive spec export --format json`, **Then** I receive a valid JSON Schema document containing all commands, queries, their parameters, return types, and constraint metadata from refinement types.

2. **Given** a Hive app with refinement types like `PositiveInt` and `Email`, **When** I export to JSON Schema, **Then** the schema includes validation constraints (`minimum: 1`, `format: email`) that match the runtime enforcement.

3. **Given** a Hive app with Pydantic models as return types, **When** I export to JSON Schema, **Then** nested model definitions are included with all field descriptions and constraints.

4. **Given** two versions of a specification export, **When** I run `hive spec diff v1.json v2.json`, **Then** I see a summary of added, removed, and modified commands/queries with breaking change detection.

---

### User Story 2 - Expose Commands to AI Agents via MCP (Priority: P2)

As a developer building AI-integrated applications, I want Hive to generate an MCP server from my command registry so that AI agents (Claude, Cursor, etc.) can discover and invoke my commands as tools.

**Why this priority**: MCP integration is a primary differentiator for Hive - enabling "terminal-agent-native" applications. This requires P1's JSON Schema export for tool input schemas.

**Independent Test**: Can be fully tested by running the generated MCP server with `hive mcp serve`, connecting via Claude Desktop, and verifying tools appear with correct schemas and can be invoked.

**Acceptance Scenarios**:

1. **Given** a Hive app with commands decorated `@command(app)`, **When** I run `hive mcp serve`, **Then** an MCP server starts exposing each command as a callable tool with auto-generated descriptions.

2. **Given** an MCP client (Claude Desktop), **When** I configure it to connect to my Hive MCP server, **Then** the client discovers all tools and displays their input schemas correctly.

3. **Given** an AI agent invokes a Hive command via MCP with valid parameters, **When** the command executes, **Then** the result is returned in the MCP response format with appropriate success/error handling.

4. **Given** a Hive app requiring stdio transport, **When** I run `hive mcp serve --transport stdio`, **Then** the server communicates via stdin/stdout for subprocess integration.

5. **Given** a Hive app requiring network access, **When** I run `hive mcp serve --transport sse`, **Then** the server listens on a configurable port using Server-Sent Events transport.

---

### User Story 3 - Generate REST API for Web Clients (Priority: P3)

As a developer building web applications, I want Hive to generate a REST API from my commands and queries so that web clients can interact with my application without writing boilerplate endpoint code.

**Why this priority**: REST API generation extends Hive's reach beyond CLI/TUI to web and mobile clients. Depends on P1's specification export for OpenAPI generation.

**Independent Test**: Can be fully tested by running `hive serve` and verifying POST/GET endpoints work correctly with Swagger UI at `/docs`.

**Acceptance Scenarios**:

1. **Given** a Hive app with commands and queries, **When** I run `hive serve`, **Then** a REST API starts with POST endpoints for commands and GET endpoints for queries.

2. **Given** a running REST API, **When** I visit `/docs`, **Then** I see interactive OpenAPI documentation with all endpoints, schemas, and example requests.

3. **Given** a command that requires authentication, **When** I configure authentication options, **Then** the REST API enforces authentication before command execution.

4. **Given** a query with parameters, **When** I call the GET endpoint with query parameters, **Then** the query executes with the provided parameters and returns JSON results.

5. **Given** a command execution fails with a validation error, **When** the REST API responds, **Then** it returns a structured error response with appropriate HTTP status code and error details.

---

### User Story 4 - Scaffold and Manage Projects via CLI (Priority: P4)

As a developer starting a new Hive project, I want CLI commands to scaffold projects, run development servers, and build distributions so that I can focus on business logic instead of project setup.

**Why this priority**: Project tooling improves developer experience but depends on the core generators (P1-P3) being functional first.

**Independent Test**: Can be fully tested by running `hive new myapp`, verifying project structure, and running `hive dev` to start development mode.

**Acceptance Scenarios**:

1. **Given** I want to create a new Hive project, **When** I run `hive new myproject`, **Then** a project directory is created with standard structure, configuration files, and example code.

2. **Given** a scaffolded project, **When** I run `hive dev`, **Then** a development server starts with hot reload for code changes.

3. **Given** a completed project, **When** I run `hive build`, **Then** a distributable package is created ready for deployment.

4. **Given** a project I want to share, **When** I run `hive publish`, **Then** the package is published to a configured package registry.

5. **Given** I want to develop the REST API specifically, **When** I run `hive serve --reload`, **Then** the REST API server starts with automatic reload on code changes.

---

### User Story 5 - Export Specification in TOML Format (Priority: P5)

As a developer who prefers human-readable configuration, I want to export my specification as TOML so that I can review and edit specifications in a more readable format than JSON.

**Why this priority**: TOML export provides an alternative format for developers who prefer it. Lower priority than JSON Schema which is the primary machine-readable format.

**Independent Test**: Can be fully tested by running `hive spec export --format toml` and verifying valid TOML output.

**Acceptance Scenarios**:

1. **Given** a Hive app with commands and queries, **When** I run `hive spec export --format toml`, **Then** I receive a valid TOML document with all specification information.

2. **Given** exported TOML and JSON specifications from the same app, **When** I compare their content, **Then** both formats contain equivalent information.

---

### Edge Cases

- What happens when exporting a specification with circular type references?
  - System detects cycles and uses JSON Schema `$ref` to handle recursive types.

- How does the MCP server handle commands that have long execution times?
  - Commands execute asynchronously; MCP server reports progress and supports cancellation where the underlying command allows.

- What happens when REST API receives malformed JSON in request body?
  - Returns HTTP 400 with structured validation error listing all issues.

- How does `hive new` handle an existing directory with the same name?
  - Prompts for confirmation before overwriting; `--force` flag skips confirmation.

- What happens when specification diff encounters incompatible schema versions?
  - Reports schema version mismatch and lists changes that could not be compared.

- How does authentication work across MCP and REST interfaces?
  - MCP relies on transport-level security (process isolation for stdio, network auth for SSE). REST supports configurable authentication middleware.

## Requirements *(mandatory)*

### Functional Requirements

#### Specification Export (Milestone 3.1)

- **FR-001**: System MUST export command and query specifications as JSON Schema.
- **FR-002**: System MUST include constraint metadata from refinement types (min/max, patterns, formats) in JSON Schema output.
- **FR-003**: System MUST export command and query specifications as TOML.
- **FR-004**: System MUST provide specification diff tooling that identifies added, removed, and modified elements.
- **FR-005**: Specification diff MUST detect breaking changes (removed commands, changed parameter types, removed required parameters).
- **FR-006**: System MUST export descriptions from docstrings and Field descriptions.

#### MCP Server Generation (Milestone 3.2)

- **FR-007**: System MUST generate an MCP server from the command registry.
- **FR-008**: Each Hive command MUST be exposed as an MCP tool with auto-generated description from docstrings.
- **FR-009**: MCP tool input schemas MUST be derived from command parameter types and constraints.
- **FR-010**: System MUST support stdio transport for subprocess integration.
- **FR-011**: System MUST support SSE (Server-Sent Events) transport for network access.
- **FR-012**: MCP server MUST handle command execution errors and return appropriate error responses.
- **FR-013**: MCP server MUST be optional - only generated when explicitly requested or dependencies installed.

#### REST API Generation (Milestone 3.3)

- **FR-014**: System MUST generate REST API endpoints from command and query registry.
- **FR-015**: Commands MUST be exposed as POST endpoints at `/commands/{command_name}`.
- **FR-016**: Queries MUST be exposed as GET endpoints at `/queries/{query_name}`.
- **FR-017**: System MUST generate OpenAPI documentation accessible at `/docs`.
- **FR-018**: System MUST support configurable authentication for protected endpoints.
- **FR-019**: REST API MUST return structured error responses with appropriate HTTP status codes.
- **FR-020**: REST API MUST be optional - only generated when explicitly requested or dependencies installed.

#### Project Tooling (Milestone 3.4)

- **FR-021**: `hive new <name>` MUST create a new project with standard directory structure.
- **FR-022**: `hive dev` MUST start a development server with hot reload capability.
- **FR-023**: `hive build` MUST create a distributable package.
- **FR-024**: `hive publish` MUST publish the package to a configured registry.
- **FR-025**: `hive serve` MUST start the REST API server for development.
- **FR-026**: `hive spec export` MUST support `--format` flag with values `json` and `toml`.
- **FR-027**: `hive spec diff` MUST compare two specification files and report differences.
- **FR-028**: `hive mcp serve` MUST start the MCP server with configurable transport.

### Key Entities

- **Specification**: The complete description of an application's commands, queries, and types - exportable in multiple formats.
- **SpecificationDiff**: A comparison between two specifications showing additions, removals, modifications, and breaking changes.
- **MCPTool**: A command exposed as an MCP tool with name, description, and input schema.
- **RESTEndpoint**: A command or query exposed as a REST endpoint with method, path, and schema.
- **ProjectTemplate**: A scaffolding template for new Hive projects containing directory structure and starter files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can export a specification in under 5 seconds for applications with up to 100 commands/queries.
- **SC-002**: JSON Schema exports pass validation against JSON Schema Draft 2020-12 specification.
- **SC-003**: MCP servers are discoverable by Claude Desktop and other MCP-compatible clients with minimal configuration:
  - stdio transport: Only `command` and `args` in client config
  - SSE transport: Only `url` (host:port) in client config
  - No tool-specific configuration required; all tools auto-discovered
- **SC-004**: REST API endpoints MUST handle 100 concurrent requests without errors when:
  - Request payload ≤ 1KB JSON
  - Response payload ≤ 10KB JSON
  - Command execution time ≤ 100ms (excluding I/O)
  - System resources: 2 CPU cores, 2GB available RAM
  - Measured via 10-second sustained load using `locust` or `work`
- **SC-005**: New project scaffolding completes in under 10 seconds and produces a runnable application.
- **SC-006**: Specification diff correctly identifies 100% of breaking changes (removed commands, changed required parameters).
- **SC-007**: Generated OpenAPI documentation accurately reflects all endpoints, parameters, and response schemas.
- **SC-008**: Development server detects code changes and reloads within 2 seconds.

## Assumptions

- FastMCP library is used for MCP server generation (specified in project requirements).
- FastAPI is used for REST API generation (specified in project requirements).
- Developers have Python 3.12+ installed (project requirement).
- MCP clients support both stdio and SSE transports.
- Project uses uv as package manager (established in project setup).
- Authentication configuration supports three modes:
  - `none`: No authentication (development only)
  - `api_key`: X-API-Key header validation against HIVE_API_KEY env var
  - `bearer`: Bearer token validation (supports OAuth2 access tokens)
  - Custom OAuth2 flows (authorization code, client credentials) are out of scope for Phase 3; bearer token validation covers typical OAuth2 resource server patterns.
