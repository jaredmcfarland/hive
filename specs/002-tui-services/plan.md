# Implementation Plan: TUI Generation and Service Layer

**Branch**: `002-tui-services` | **Date**: 2026-01-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-tui-services/spec.md`

## Summary

Implement Phase 2 of Hive: TUI application generation from `@screen` decorated classes, service layer with keyring credential management, and standard Textual widgets. Technical approach uses Textual's reactive system for query binding, lazy service instantiation via descriptor protocol, and CSS-themeable widgets.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Textual (TUI), keyring (credentials), httpx (HTTP client), existing: Typer, Rich, SQLModel, Pydantic
**Storage**: SQLite via SQLModel (existing infrastructure from Phase 1)
**Testing**: pytest + pytest-asyncio + pytest-textual-snapshot (new dependency for TUI testing)
**Target Platform**: macOS, Linux, Windows (terminals supporting 80x24+)
**Project Type**: Single project (src/hive layout)
**Performance Goals**: <100ms navigation latency, <500ms query display, <50ms service instantiation
**Constraints**: Keyboard-navigable, 80x24 minimum terminal, credentials never logged
**Scale/Scope**: 10-20 screens typical, 100+ commands in palette, multiple services

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First ✅

- TUI generation reads from existing registry (`@screen` decorator already exists)
- All interfaces (CLI, TUI, API) derive from same decorated source
- Service layer uses `@service` decorator following established pattern

### II. CLI-First Architecture ✅

- TUI is complementary interface, not replacement for CLI
- Commands executed via palette use same execution path as CLI
- All operations remain accessible headlessly via CLI

### III. Test-First Development ✅

- Tests will be written before implementation
- Contract tests verify screen registration matches spec
- Snapshot tests verify TUI rendering consistency
- Integration tests verify query binding and service access

### IV. Triple Interface Consistency ✅

- Commands exposed in palette are identical to CLI commands
- Query results display identically (TUI data tables = CLI JSON/table output)
- Service access via `ctx.services.*` works identically in CLI and TUI contexts

### V. Simplicity & YAGNI ✅

- Minimal widget set (5 widgets): Header, Footer, CommandPalette, ParameterModal, DataTable
- No custom theming system—use Textual's built-in CSS
- Service decorator follows existing decorator patterns exactly
- No speculative features (e.g., no drag-and-drop, no multi-window)

## Project Structure

### Documentation (this feature)

```text
specs/002-tui-services/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── screen-api.md
│   ├── service-api.md
│   └── widget-api.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/hive/
├── core/
│   ├── decorators.py    # Add @service decorator
│   ├── registry.py      # Add service registration
│   └── types.py         # Add ServiceRegistration type
├── generators/
│   ├── cli.py           # Existing CLI generator
│   └── tui.py           # NEW: TUI application generator
├── runtime/
│   ├── context.py       # Extend with services access
│   └── services.py      # NEW: Service instantiation and credentials
├── tui/                  # NEW: TUI components
│   ├── __init__.py
│   ├── app.py           # HiveApp (generated app base)
│   ├── screens.py       # HiveScreen base class
│   ├── binding.py       # Query data binding utilities
│   └── widgets/         # Standard widgets
│       ├── __init__.py
│       ├── header.py    # HiveHeader
│       ├── footer.py    # HiveFooter
│       ├── palette.py   # CommandPalette
│       ├── modal.py     # ParameterModal
│       └── table.py     # HiveDataTable
└── testing/
    └── tui.py           # NEW: TUI test utilities

tests/
├── unit/
│   ├── tui/
│   │   ├── test_app_generation.py
│   │   ├── test_screen_registration.py
│   │   ├── test_query_binding.py
│   │   └── test_widgets.py
│   └── services/
│       ├── test_service_decorator.py
│       ├── test_credential_resolution.py
│       └── test_service_lifecycle.py
├── integration/
│   └── test_tui_full_app.py
└── snapshots/           # TUI snapshot tests
    └── test_*.svg
```

**Structure Decision**: Single project layout maintained. New `src/hive/tui/` package for TUI components follows existing pattern (generators/, runtime/, etc.). Service layer integrated into existing runtime/ and core/ packages.

## Complexity Tracking

> No violations requiring justification. Design follows constitution strictly.
