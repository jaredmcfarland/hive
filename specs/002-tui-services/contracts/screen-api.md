# Screen API Contract

**Feature**: 002-tui-services
**Version**: 1.0.0

## @screen Decorator

### Signature

```python
def screen(
    app: App,
    *,
    default: bool = False,
    keybinding: str | None = None,
    name: str | None = None,
    queries: list[str] | None = None,
) -> Callable[[type[T]], type[T]]
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | Application instance |
| `default` | `bool` | `False` | If True, this screen shows on app launch |
| `keybinding` | `str \| None` | `None` | Global key to navigate to screen |
| `name` | `str \| None` | `None` | Override screen name (defaults to class name) |
| `queries` | `list[str] \| None` | `None` | Query names to auto-load on mount |

### Behavior

1. Registers screen class with application registry
2. Validates keybinding uniqueness (raises `RegistrationError` if duplicate)
3. Validates at most one default screen per app
4. Returns decorated class unchanged

### Example

```python
@screen(app, default=True, keybinding="d", queries=["list_tasks"])
class DashboardScreen(HiveScreen):
    """Main dashboard showing task overview."""

    def compose(self) -> ComposeResult:
        yield HiveHeader()
        yield HiveDataTable(id="tasks")
        yield HiveFooter()
```

## HiveScreen Base Class

### Signature

```python
class HiveScreen(textual.Screen, Generic[T]):
    data: reactive[list[T]]
    loading: reactive[bool]
    error: reactive[str | None]
    ctx: ScreenContext

    async def on_mount(self) -> None: ...
    async def refresh_data(self) -> None: ...
```

### Lifecycle

```
┌────────────────┐
│   __init__     │
└───────┬────────┘
        ▼
┌────────────────┐
│   on_mount     │──────► Load bound queries
└───────┬────────┘
        ▼
┌────────────────┐
│  compose       │──────► Yield widgets
└───────┬────────┘
        ▼
┌────────────────┐
│  Event Loop    │◄─────► Handle user input
└───────┬────────┘
        ▼
┌────────────────┐
│  on_unmount    │──────► Cleanup
└────────────────┘
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Query not found | Raise `ConfigurationError` at app startup |
| Query execution fails | Set `error` reactive, display in UI |
| Keybinding conflict | Raise `RegistrationError` at decoration time |

## Screen Navigation

### Methods

```python
# Navigate to named screen
await self.ctx.navigate("settings")

# Navigate with parameters
await self.ctx.navigate("task_detail", task_id=123)

# Go back to previous screen
await self.ctx.go_back()
```

### Events

| Event | Trigger | Handler |
|-------|---------|---------|
| `ScreenEnter` | Screen becomes active | `on_screen_enter` |
| `ScreenLeave` | Screen becomes inactive | `on_screen_leave` |
| `DataLoaded` | Query completes | `on_data_loaded` |
| `DataError` | Query fails | `on_data_error` |
