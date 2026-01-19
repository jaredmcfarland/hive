# Research: TUI Generation and Service Layer

**Feature**: 002-tui-services
**Date**: 2026-01-17

## 1. Textual Application Generation

### Decision: Subclass-based generation with runtime binding

**Rationale**: Generate a `HiveApp` class that subclasses `textual.app.App` and dynamically binds screens from the registry at instantiation. This preserves Textual's architecture while enabling specification-driven generation.

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| Code generation (emit Python source) | Harder to debug, doesn't integrate with IDE tooling, version control noise |
| Metaclass manipulation | Overly complex, breaks standard Textual patterns |
| Standalone factory function | Loses type hints and IDE support for the generated app |

### Implementation Pattern

```python
class HiveApp(textual.App):
    def __init__(self, registry: ApplicationRegistry):
        super().__init__()
        self._registry = registry
        self._bind_screens()

    def _bind_screens(self):
        for screen_reg in self._registry.list_screens():
            self.install_screen(screen_reg.cls, name=screen_reg.name)
            if screen_reg.keybinding:
                self.bind(screen_reg.keybinding, f"switch_screen('{screen_reg.name}')")
```

**Key Dependencies**:
- `textual>=0.50.0` (required for stable `install_screen` API)
- Textual CSS variables for theming

---

## 2. Query Data Binding

### Decision: Reactive properties with async workers

**Rationale**: Use Textual's `reactive` attributes combined with `@work` decorators to bind query results to widgets. This leverages Textual's built-in reactivity system rather than inventing a custom binding mechanism.

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| Manual refresh via `watch_*` methods | More boilerplate, doesn't leverage reactive system |
| Custom pub/sub system | Reinvents what Textual already provides |
| Polling-based refresh | Wasteful, poor UX for static data |

### Implementation Pattern

```python
class HiveScreen(textual.Screen):
    data = reactive(list, init=False)  # Query results
    loading = reactive(False)
    error = reactive(None)

    async def on_mount(self):
        if self._query_binding:
            self.load_query()

    @work(exclusive=True)
    async def load_query(self):
        self.loading = True
        self.error = None
        try:
            ctx = await self._get_context()
            self.data = await self._query_binding.execute(ctx)
        except Exception as e:
            self.error = str(e)
        finally:
            self.loading = False
```

**Caching Integration**: Query results respect `cache_ttl` from `@query` decorator. If cached data exists, display immediately and refresh in background.

---

## 3. Service Layer Credential Management

### Decision: Keyring with environment variable fallback

**Rationale**: Use `keyring` library for secure credential storage with automatic fallback to environment variables for CI/headless environments. This follows the principle of least surprise—credentials work like other credential managers (macOS Keychain, etc.).

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| Plain config files | Security risk, credentials in plaintext |
| Custom encrypted storage | Reinvents keyring, platform-specific complexity |
| Only environment variables | Poor UX for interactive use |

### Credential Resolution Order

1. Keyring: `keyring.get_password("hive", service_name)`
2. Environment: `{SERVICE_NAME}_API_KEY` or `{SERVICE_NAME}_TOKEN`
3. Config file: `~/.config/hive/credentials.toml` (optional)
4. Prompt (TUI only): Modal dialog for credential entry

### Implementation Pattern

```python
@dataclass
class ServiceRegistration:
    name: str
    factory: Callable[[str], Any]  # Receives credentials
    credential_key: str | None
    cleanup: Callable[[Any], None] | None = None

class ServiceProxy:
    """Lazy service accessor via descriptor protocol."""

    def __getattr__(self, name: str) -> Any:
        if name not in self._cache:
            self._cache[name] = self._instantiate(name)
        return self._cache[name]

    def _resolve_credentials(self, key: str) -> str:
        # 1. Try keyring
        cred = keyring.get_password("hive", key)
        if cred:
            return cred
        # 2. Try environment
        env_key = f"{key.upper().replace('-', '_')}_API_KEY"
        cred = os.environ.get(env_key)
        if cred:
            return cred
        # 3. Raise with helpful message
        raise CredentialError(f"No credentials found for '{key}'")
```

**Security Constraint**: Credentials MUST NOT appear in logs, error messages, or stack traces. Use `SecretStr` from Pydantic where appropriate.

---

## 4. Standard Widgets Design

### Decision: Minimal, composable widgets extending Textual base classes

**Rationale**: Create thin wrapper widgets that add Hive-specific functionality (registry integration, context awareness) while delegating rendering to Textual's battle-tested components.

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| Complete custom rendering | Loses Textual's styling, accessibility features |
| Heavy abstraction layer | YAGNI, adds complexity without clear benefit |
| No standard widgets | Forces users to reimplement common patterns |

### Widget Specifications

| Widget | Extends | Key Features |
|--------|---------|--------------|
| `HiveHeader` | `textual.widgets.Header` | Auto-displays app name, version, screen title |
| `HiveFooter` | `textual.widgets.Footer` | Dynamic keybinding display from registry |
| `CommandPalette` | `textual.widgets.OptionList` + Modal | Fuzzy search, command execution, parameter prompt |
| `ParameterModal` | `textual.screen.ModalScreen` | Dynamic form generation from `ParameterInfo` |
| `HiveDataTable` | `textual.widgets.DataTable` | Auto-columns from Pydantic schema, query binding |

### CommandPalette Behavior

1. `Ctrl+P` opens palette (configurable)
2. Type to fuzzy-filter commands from registry
3. Select command → if parameters required, show `ParameterModal`
4. Submit → execute command via same path as CLI
5. Display result in notification or dedicated panel

---

## 5. Testing Strategy

### Decision: Pilot-based unit tests + snapshot regression tests

**Rationale**: Use Textual's `run_test()` context manager for unit tests and `pytest-textual-snapshot` for visual regression. This catches both behavioral bugs and unintended UI changes.

**New Dependency**: `pytest-textual-snapshot>=1.0.0`

### Test Categories

| Category | Focus | Example |
|----------|-------|---------|
| Unit | Individual widget behavior | `test_header_displays_app_name` |
| Integration | Screen→Query→Display flow | `test_data_table_loads_query_results` |
| Snapshot | Visual consistency | `test_dashboard_screen_appearance` |
| Contract | API signatures match spec | `test_service_decorator_signature` |

### Testing Pattern for TUI

```python
async def test_screen_navigation():
    app = create_test_app()  # From hive.testing.tui
    async with app.run_test() as pilot:
        await pilot.press("d")  # Dashboard keybinding
        assert app.screen.name == "DashboardScreen"
```

---

## 6. Architecture Decisions Summary

| Decision | Approach | Constitution Principle |
|----------|----------|----------------------|
| App generation | Subclass + runtime binding | Specification-First (I) |
| Query binding | Textual reactive + workers | Simplicity (V) |
| Credentials | Keyring with fallback chain | CLI-First (II) |
| Widgets | Thin wrappers, composable | YAGNI (V) |
| Testing | Pilot + snapshots | Test-First (III) |

---

## 7. Dependency Additions

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "textual>=0.50.0",
    "keyring>=25.0.0",
]

[project.optional-dependencies]
dev = [
    # ... existing ...
    "pytest-textual-snapshot>=1.0.0",
]
```
