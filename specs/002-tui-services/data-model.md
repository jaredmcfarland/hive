# Data Model: TUI Generation and Service Layer

**Feature**: 002-tui-services
**Date**: 2026-01-17

## Core Types

### ServiceRegistration

Extends the existing registration pattern for services.

```
ServiceRegistration
├── name: str                           # Unique service identifier
├── factory: Callable[[str], Any]       # Factory function receiving credentials
├── credential_key: str | None          # Key for credential lookup (e.g., "github")
├── cleanup: Callable[[Any], None] | None  # Optional cleanup function
└── docstring: str | None               # Service description
```

**Validation Rules**:
- `name` must be a valid Python identifier
- `factory` must be callable with single string argument
- `credential_key` follows pattern: `keyring:{service}` or `env:{VAR_NAME}`

### ScreenRegistration (existing, extended)

Already exists in `hive.core.types`. Extended with query binding.

```
ScreenRegistration
├── name: str                    # Screen identifier
├── cls: type[Screen]            # Screen class
├── default: bool                # Is default screen?
├── keybinding: str | None       # Navigation keybinding
├── docstring: str | None        # Screen description
└── queries: list[str]           # NEW: Bound query names
```

### QueryBinding

Associates a screen with a query for automatic data loading.

```
QueryBinding
├── screen_name: str              # Target screen
├── query_name: str               # Query to execute
├── target_property: str          # Reactive property to update
├── transform: Callable | None    # Optional result transformer
└── refresh_on: list[str]         # Events that trigger refresh
```

**State Transitions**:
```
QueryBinding States:
  idle → loading → loaded
           ↓
         error
```

### CredentialSpec

Specification for credential resolution.

```
CredentialSpec
├── source: Literal["keyring", "env", "prompt"]
├── key: str                      # Service name or env var
├── required: bool                # Fail if not found?
└── mask_in_logs: bool = True     # Always mask in output
```

## Runtime Types

### ServiceProxy

Lazy accessor for registered services.

```
ServiceProxy
├── _registry: ApplicationRegistry
├── _context: ExecutionContext
├── _cache: dict[str, Any]        # Instantiated services
└── __getattr__(name) → Any       # Lazy instantiation
```

**Invariants**:
- Services are instantiated at most once per context
- Cleanup is called for all cached services on context exit
- Credentials are never stored in the proxy

### HiveApp

Generated Textual application.

```
HiveApp
├── registry: ApplicationRegistry
├── ctx: ExecutionContext | None
├── BINDINGS: list[Binding]       # Generated from screens
└── SCREENS: dict[str, Screen]    # Installed from registry
```

### ScreenContext

TUI-specific execution context extension.

```
ScreenContext (extends ExecutionContext)
├── app: HiveApp                  # Parent application
├── screen: Screen                # Current screen
├── navigate(screen_name: str)    # Screen navigation
└── notify(message: str, severity)# Toast notifications
```

## Widget State

### CommandPaletteState

```
CommandPaletteState
├── visible: bool
├── search_text: str
├── filtered_commands: list[CommandRegistration]
├── selected_index: int
└── parameter_values: dict[str, Any]
```

### DataTableState

```
DataTableState
├── data: list[BaseModel]        # Query results
├── columns: list[ColumnDef]     # Auto-generated from schema
├── loading: bool
├── error: str | None
├── sort_column: str | None
├── sort_ascending: bool
└── selected_row: int | None
```

## Relationships

```
┌─────────────────┐     ┌──────────────────┐
│ ApplicationRegistry │───────│ ServiceRegistration │
└─────────────────┘     └──────────────────┘
         │                        │
         │                        ▼
         │              ┌──────────────────┐
         │              │   ServiceProxy   │
         │              └──────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│ ScreenRegistration│────│ ExecutionContext │
└─────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│  QueryBinding   │     │   ScreenContext  │
└─────────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│ DataTableState  │
└─────────────────┘
```

## Type Definitions (Python)

```python
# src/hive/core/types.py additions

@dataclass(frozen=True)
class ServiceRegistration:
    """Registration data for a service."""
    name: str
    factory: Callable[[str], Any]
    credential_key: str | None = None
    cleanup: Callable[[Any], None] | None = None
    docstring: str | None = None

@dataclass(frozen=True)
class QueryBinding:
    """Binding between a screen and a query."""
    screen_name: str
    query_name: str
    target_property: str = "data"
    transform: Callable[[Any], Any] | None = None
    refresh_on: tuple[str, ...] = ()

@dataclass
class CredentialSpec:
    """Specification for credential resolution."""
    source: Literal["keyring", "env", "prompt"]
    key: str
    required: bool = True
```
