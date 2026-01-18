# Feature Specification: TUI Generation and Service Layer

**Feature Branch**: `002-tui-services`
**Created**: 2026-01-17
**Status**: Draft
**Input**: Phase 2: TUI and Services - TUI generation, service layer, and standard widgets

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate TUI Application from Decorated Code (Priority: P1)

A framework user defines screens using `@screen` decorators on Python classes and runs a generation command. The framework produces a working Textual application with header, footer, and navigation between screens.

**Why this priority**: TUI generation is the foundational capability. Without it, none of the other features (services, widgets) have value. This enables the core promise of Hive: generating interfaces from a single decorated codebase.

**Independent Test**: Can be fully tested by creating a simple app with two `@screen` decorated classes and verifying the generated TUI displays both screens with working navigation.

**Acceptance Scenarios**:

1. **Given** a Python module with two `@screen` decorated classes, **When** the framework generates the TUI, **Then** both screens are accessible via keyboard navigation
2. **Given** a screen marked with `default=True`, **When** the TUI starts, **Then** that screen is displayed first
3. **Given** a screen with `keybinding="s"`, **When** user presses "s" in the TUI, **Then** navigation switches to that screen
4. **Given** a TUI application, **When** it launches, **Then** a header displaying the app name and a footer showing available keybindings are visible

---

### User Story 2 - Bind Query Results to UI Components (Priority: P2)

A framework user creates a screen that displays data from a `@query` decorated function. The screen automatically loads and displays the query results when mounted. When the underlying data changes, the display updates.

**Why this priority**: Data binding transforms TUI from static screens to dynamic data displays. This is essential for building useful applications but depends on TUI generation (P1) being complete.

**Independent Test**: Can be fully tested by creating a screen with a query-bound component, executing the query, and verifying the results appear in the UI.

**Acceptance Scenarios**:

1. **Given** a screen with a data table bound to a query, **When** the screen mounts, **Then** the table populates with query results
2. **Given** a query with cached results, **When** the screen displays, **Then** cached data shows immediately while fresh data loads in background
3. **Given** a query that returns empty results, **When** the screen displays, **Then** an appropriate empty state message appears
4. **Given** a query that fails, **When** the screen displays, **Then** a user-friendly error message appears without crashing the application

---

### User Story 3 - Access Services with Managed Credentials (Priority: P3)

A framework user defines an external service using `@service` decorator with credential configuration. The service is instantiated lazily when first accessed via `ctx.services.<name>` and credentials are securely retrieved from the system keyring.

**Why this priority**: Services enable integration with external APIs, expanding what Hive apps can do. However, basic TUI and data display (P1, P2) provide standalone value first.

**Independent Test**: Can be fully tested by defining a service with mock credentials, accessing it in a command, and verifying the service client is properly instantiated with credentials.

**Acceptance Scenarios**:

1. **Given** a service decorated with `@service(app, credentials="keyring:myservice")`, **When** `ctx.services.myservice` is first accessed, **Then** the service is instantiated with credentials from keyring
2. **Given** credentials are not stored in keyring, **When** service is accessed, **Then** user is prompted to enter credentials (in TUI mode) or receives a clear error (in CLI mode)
3. **Given** a service has been instantiated, **When** accessed again in the same context, **Then** the same instance is returned (no re-instantiation)
4. **Given** a service with cleanup requirements, **When** the execution context exits, **Then** service cleanup methods are called

---

### User Story 4 - Use Command Palette for Command Execution (Priority: P4)

A user opens a command palette in the TUI using a keyboard shortcut. The palette displays all available commands from the application. The user can search, select, and execute commands with parameter input.

**Why this priority**: Command palette provides efficient keyboard-driven interaction but requires TUI generation and commands to already work. It's an enhancement to the core experience.

**Independent Test**: Can be fully tested by opening the command palette, searching for a specific command, providing parameters, and verifying execution.

**Acceptance Scenarios**:

1. **Given** a running TUI application, **When** user presses the command palette shortcut, **Then** a searchable list of all registered commands appears
2. **Given** the command palette is open, **When** user types a search term, **Then** commands are filtered to match the search
3. **Given** a command requiring parameters is selected, **When** user confirms selection, **Then** a parameter input modal appears with fields for each required parameter
4. **Given** valid parameters are entered, **When** user submits, **Then** the command executes and results display appropriately

---

### User Story 5 - Use Standard Widgets for Common Patterns (Priority: P5)

A framework user builds screens using framework-provided widgets (themed Header, Footer, CommandPalette, ParameterModal, DataTable). These widgets follow consistent styling and integrate with the Hive runtime.

**Why this priority**: Standard widgets reduce boilerplate and ensure consistency, but developers can build functional apps with basic Textual widgets first.

**Independent Test**: Can be fully tested by creating a screen using each standard widget and verifying proper rendering and behavior.

**Acceptance Scenarios**:

1. **Given** an app using `HiveHeader`, **When** the TUI renders, **Then** the header displays app name, version, and current screen title
2. **Given** an app using `HiveFooter`, **When** the TUI renders, **Then** the footer displays active keybindings for the current screen
3. **Given** a `HiveDataTable` bound to a query, **When** data loads, **Then** the table displays with proper columns derived from query result schema
4. **Given** a `ParameterModal` for a command, **When** displayed, **Then** input fields match command parameter types with appropriate validation

---

### Edge Cases

- What happens when a screen's `@query` dependency is not registered? Framework raises a clear configuration error at startup.
- How does the system handle keyring access in headless/CI environments? Falls back to environment variables or configuration file with appropriate warnings.
- What happens when two screens have conflicting keybindings? Framework raises a configuration error listing the conflict.
- How does the TUI behave when terminal is too small? Graceful degradation with minimum size warning.
- What happens when a service factory function raises an exception? Error is caught, logged, and surfaced as a user-friendly message without crashing the application.

## Requirements *(mandatory)*

### Functional Requirements

**TUI Generation (Milestone 2.1)**

- **FR-001**: System MUST generate a Textual application from `@screen` decorated classes in the registry
- **FR-002**: Generated TUI MUST include a header widget displaying application name
- **FR-003**: Generated TUI MUST include a footer widget displaying available keybindings
- **FR-004**: System MUST support screen navigation via configurable keybindings
- **FR-005**: System MUST render the screen marked `default=True` on application launch
- **FR-006**: Screens MUST receive an execution context (`ctx`) with access to database, services, and output
- **FR-007**: System MUST support command palette activation via keyboard shortcut (default: Ctrl+P)

**Query Data Binding (Milestone 2.1)**

- **FR-008**: Screens MUST be able to declare query dependencies that load automatically on mount
- **FR-009**: Query results MUST be bindable to reactive widget properties
- **FR-010**: System MUST display loading indicators while queries execute
- **FR-011**: System MUST handle query errors gracefully with user-friendly messages
- **FR-012**: Cached query results MUST display immediately while background refresh occurs

**Service Layer (Milestone 2.2)**

- **FR-013**: System MUST support `@service(app, credentials="keyring:<service>")` decorator for service registration
- **FR-014**: Services MUST be lazily instantiated on first access via `ctx.services.<name>`
- **FR-015**: System MUST retrieve credentials from system keyring using the specified key pattern
- **FR-016**: System MUST support credential fallback to environment variables when keyring unavailable
- **FR-017**: Service instances MUST be cached within an execution context (singleton per context)
- **FR-018**: System MUST call service cleanup methods when execution context exits
- **FR-019**: System MUST provide clear error messages when credentials are missing

**Standard Widgets (Milestone 2.3)**

- **FR-020**: Framework MUST provide `HiveHeader` widget with app name, version, and current screen display
- **FR-021**: Framework MUST provide `HiveFooter` widget with dynamic keybinding display
- **FR-022**: Framework MUST provide `CommandPalette` widget with search and command execution
- **FR-023**: Framework MUST provide `ParameterModal` widget for command parameter input
- **FR-024**: Framework MUST provide `HiveDataTable` widget with automatic column generation from query schemas
- **FR-025**: All standard widgets MUST be themeable via Textual CSS

### Key Entities

- **Screen**: A TUI view registered via `@screen` decorator. Has name, keybinding, default flag, and compose method.
- **Service**: An external API client registered via `@service` decorator. Has name, credential key, factory function, and optional cleanup method.
- **ScreenContext**: Extension of ExecutionContext providing TUI-specific capabilities (reactive state, navigation methods).
- **QueryBinding**: Association between a screen and a query, specifying how results map to widget properties.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can generate a working TUI application from decorated code in under 5 lines of configuration
- **SC-002**: Screen-to-screen navigation responds to keypresses within 100ms perceived latency
- **SC-003**: Query-bound data tables display results within 500ms of screen mount (excluding network latency)
- **SC-004**: Service credentials are never logged or exposed in error messages
- **SC-005**: 100% of standard widgets pass accessibility testing for keyboard navigation
- **SC-006**: Applications built with Hive TUI work correctly in terminals supporting 80x24 minimum resolution
- **SC-007**: Service instantiation overhead adds less than 50ms to first access
- **SC-008**: Command palette search filters 100+ commands with no perceptible delay

## Assumptions

- Textual framework (v0.50+) is the TUI foundation; CSS-like styling applies
- System keyring access via `keyring` library is available on target platforms (macOS Keychain, Windows Credential Locker, Linux Secret Service)
- Screens are defined as classes inheriting from a base `HiveScreen` that extends Textual's Screen
- Query binding uses Textual's reactive system; queries return Pydantic models or dataclass instances
- Default command palette keybinding (Ctrl+P) can be overridden in app configuration
- Service decorator accepts a factory function that receives credentials and returns a configured client
