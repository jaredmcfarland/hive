# Widget API Contract

**Feature**: 002-tui-services
**Version**: 1.0.0

## HiveHeader

### Signature

```python
class HiveHeader(textual.widgets.Header):
    def __init__(
        self,
        *,
        show_clock: bool = False,
        show_screen_title: bool = True,
        id: str | None = None,
        classes: str | None = None,
    ) -> None
```

### Behavior

- Displays app name from `app.title`
- Displays app version if set
- Displays current screen title when `show_screen_title=True`
- Optional clock display

### CSS Classes

| Class | Description |
|-------|-------------|
| `.hive-header` | Base header styling |
| `.hive-header--title` | App title area |
| `.hive-header--screen` | Screen title area |
| `.hive-header--clock` | Clock area |

---

## HiveFooter

### Signature

```python
class HiveFooter(textual.widgets.Footer):
    def __init__(
        self,
        *,
        show_command_palette_hint: bool = True,
        id: str | None = None,
        classes: str | None = None,
    ) -> None
```

### Behavior

- Displays keybindings from current screen
- Includes global keybindings (screen navigation)
- Shows command palette hint (Ctrl+P) when enabled
- Updates dynamically on screen change

### CSS Classes

| Class | Description |
|-------|-------------|
| `.hive-footer` | Base footer styling |
| `.hive-footer--key` | Keybinding display |
| `.hive-footer--hint` | Command palette hint |

---

## CommandPalette

### Signature

```python
class CommandPalette(textual.screen.ModalScreen[CommandResult | None]):
    def __init__(
        self,
        registry: ApplicationRegistry,
        *,
        placeholder: str = "Search commands...",
    ) -> None
```

### Behavior

1. Opens as modal overlay
2. Displays all commands from registry
3. Fuzzy filters as user types
4. Shows command descriptions
5. On selection:
   - If command has parameters → show `ParameterModal`
   - If no parameters → execute immediately
6. Returns `CommandResult` or `None` if cancelled

### Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Select highlighted command |
| `Escape` | Close palette |
| `Up/Down` | Navigate list |
| `Ctrl+P` | Close palette (toggle) |

### CSS Classes

| Class | Description |
|-------|-------------|
| `.command-palette` | Modal container |
| `.command-palette--search` | Search input |
| `.command-palette--list` | Command list |
| `.command-palette--item` | Individual command |
| `.command-palette--item-selected` | Selected command |
| `.command-palette--description` | Command description |

---

## ParameterModal

### Signature

```python
class ParameterModal(textual.screen.ModalScreen[dict[str, Any] | None]):
    def __init__(
        self,
        command: CommandRegistration,
        *,
        title: str | None = None,
    ) -> None
```

### Behavior

1. Generates form fields from `command.parameters`
2. Applies validation from refinement types
3. Shows validation errors inline
4. Returns parameter dict or `None` if cancelled

### Field Generation

| Parameter Type | Widget |
|---------------|--------|
| `str` | `Input` |
| `int`, `float` | `Input` with numeric validation |
| `bool` | `Switch` |
| `Literal[...]` | `Select` |
| `list[...]` | Multi-value input |
| `Path` | `Input` with path completion |

### CSS Classes

| Class | Description |
|-------|-------------|
| `.parameter-modal` | Modal container |
| `.parameter-modal--title` | Modal title |
| `.parameter-modal--field` | Field container |
| `.parameter-modal--label` | Field label |
| `.parameter-modal--input` | Input widget |
| `.parameter-modal--error` | Validation error |
| `.parameter-modal--actions` | Submit/Cancel buttons |

---

## HiveDataTable

### Signature

```python
class HiveDataTable(textual.widgets.DataTable, Generic[T]):
    data: reactive[list[T]]
    loading: reactive[bool]
    error: reactive[str | None]

    def __init__(
        self,
        *,
        query: str | None = None,
        columns: list[str] | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None
```

### Behavior

1. If `query` specified, auto-binds to screen's query
2. Auto-generates columns from Pydantic model schema if not specified
3. Shows loading indicator while `loading=True`
4. Shows error message if `error` is set
5. Supports sorting by clicking column headers
6. Supports row selection

### Column Generation

For a Pydantic model:
```python
class Task(BaseModel):
    id: int
    title: str
    completed: bool
```

Generates columns:
| Column | Type | Width |
|--------|------|-------|
| `id` | `int` | auto |
| `title` | `str` | 1fr |
| `completed` | `bool` | auto |

### Events

| Event | Trigger | Data |
|-------|---------|------|
| `DataTable.RowSelected` | Row clicked/entered | `row_key`, `row_data` |
| `DataTable.ColumnSorted` | Column header clicked | `column`, `ascending` |

### CSS Classes

| Class | Description |
|-------|-------------|
| `.hive-data-table` | Table container |
| `.hive-data-table--loading` | Loading overlay |
| `.hive-data-table--error` | Error display |
| `.hive-data-table--empty` | Empty state |

---

## Common Widget Features

### Theming

All widgets support Textual CSS theming via:
- Component classes (documented above)
- Theme variables (`$primary`, `$secondary`, etc.)
- Inline `styles` parameter

### Accessibility

All widgets MUST:
- Be keyboard navigable
- Support screen readers (ARIA attributes)
- Have visible focus indicators
- Work at 80x24 minimum terminal size

### Example Theme Override

```css
.hive-header {
    background: $primary;
    color: $foreground;
}

.command-palette--item-selected {
    background: $primary-lighten-1;
}
```
