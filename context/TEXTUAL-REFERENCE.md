# Textual Development Reference

A comprehensive guide for building TUI applications with Textual. Optimized for AI-assisted development.

---

## 1. Mental Models

### App Architecture

Textual apps follow a reactive lifecycle:

1. **Compose Phase**: `compose()` yields widgets, creating the DOM tree
2. **Mount Phase**: `on_mount()` fires for initialization after widgets exist
3. **Event Phase**: User input and state changes trigger handlers
4. **Render Phase**: Widgets render via `render()` or respond to reactive changes
5. **Exit Phase**: `app.exit(result)` returns data to caller

```python
from textual.app import App, ComposeResult
from textual.widgets import Static, Button

class MyApp(App):
    CSS_PATH = "app.tcss"  # External stylesheet

    def compose(self) -> ComposeResult:
        yield Static("Hello")
        yield Button("Click me", id="btn")

    def on_mount(self) -> None:
        self.query_one("#btn").focus()
```

### DOM & Widget Hierarchy

Widgets form a tree structure rooted at `Screen`. CSS cascades down parent-child relationships.

**Selectors** (in order of specificity):
- Type: `Button` matches all buttons
- Class: `.active` matches widgets with `classes="active"`
- ID: `#submit` matches `id="submit"`
- Pseudo-class: `:focus`, `:hover`, `:disabled`
- Combinators: `#form Button` (descendant), `#form > Button` (direct child)

### Message/Event Flow

Messages bubble **up** the DOM tree (child → parent → app) until handled or stopped:

```python
# Child widget posts message
self.post_message(MyMessage(data))

# Parent handles it
def on_my_message(self, message: MyMessage) -> None:
    message.stop()  # Prevent further bubbling
```

**Golden rule**: Attributes flow down (parent sets child properties), messages flow up.

### Reactivity System

Reactive attributes automatically trigger UI updates when changed:

```python
from textual.reactive import reactive, var

class Counter(Static):
    count = reactive(0)      # Triggers refresh on change
    label = var("inactive")  # No refresh, but watchers work

    def watch_count(self, new_value: int) -> None:
        """Called when count changes."""
        self.update(f"Count: {new_value}")

    def compute_doubled(self) -> int:
        """Derived value, auto-recalculates."""
        return self.count * 2
```

| Feature | `reactive` | `var` |
|---------|-----------|-------|
| Auto-refresh | Yes | No |
| Watchers | Yes | Yes |
| Compute methods | Yes | Yes |
| Use case | UI state | Internal state |

### CSS Integration

Textual CSS (TCSS) applies to widgets via external files or inline:

```python
class MyApp(App):
    CSS_PATH = "styles.tcss"  # External file
    # OR
    CSS = """
    Screen { layout: vertical; }
    Button { width: 100%; }
    """
```

```css
/* styles.tcss */
$primary: #88C0D0;

Screen {
    layout: vertical;
    background: $background;
}

Button {
    width: 1fr;
    &:focus { background: $primary; }
}
```

---

## 2. Core Patterns

### Widget Creation

**Static widget with render**:
```python
class Greeting(Static):
    def render(self) -> str:
        return "[bold]Hello[/] World"
```

**Compound widget with compose**:
```python
class InputWithLabel(Static):
    def compose(self) -> ComposeResult:
        yield Label("Name:")
        yield Input(id="name-input")
```

**Custom widget with reactive state**:
```python
class Counter(Widget):
    count = reactive(0)

    def render(self) -> str:
        return str(self.count)

    def increment(self) -> None:
        self.count += 1  # Auto-refresh via reactive
```

### Event Handling

**@on decorator** targets specific widgets via CSS selectors:

```python
from textual import on
from textual.widgets import Button

class MyApp(App):
    @on(Button.Pressed, "#save")
    def handle_save(self) -> None:
        self.save_data()

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        self.app.exit()

    # Multiple selectors
    @on(Button.Pressed, "#red,#green,#blue")
    def handle_color(self, event: Button.Pressed) -> None:
        color = event.button.id
        self.apply_color(color)
```

**Custom messages** for child→parent communication:

```python
class ColorPicker(Widget):
    class ColorSelected(Message):
        def __init__(self, color: str) -> None:
            self.color = color
            super().__init__()

    def select_color(self, color: str) -> None:
        self.post_message(self.ColorSelected(color))

# Parent handles it
class MyApp(App):
    def on_color_picker_color_selected(self, message: ColorPicker.ColorSelected) -> None:
        self.background = message.color
```

### Layout Patterns

**Vertical stack** (default for Screen):
```css
Screen { layout: vertical; }
.content { height: 1fr; }  /* Fills remaining space */
```

**Horizontal split**:
```css
.container { layout: horizontal; }
#sidebar { width: 20; }
#main { width: 1fr; }
```

**Grid layout**:
```css
.grid {
    layout: grid;
    grid-size: 3 2;           /* 3 columns, 2 rows */
    grid-columns: 1fr 2fr 1fr; /* Flexible widths */
    grid-gutter: 1 2;          /* Vertical horizontal spacing */
}
```

**Docking** for fixed headers/footers:
```css
Header { dock: top; height: 3; }
Footer { dock: bottom; height: 1; }
```

### Screen Navigation

**Push/pop screens**:
```python
# Push a screen (stacks on current)
self.app.push_screen(SettingsScreen())

# Pop back
self.app.pop_screen()

# Replace current screen
self.app.switch_screen(NewScreen())
```

**Modal screens with return values**:
```python
class ConfirmDialog(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        yield Label("Are you sure?")
        yield Button("Yes", id="yes")
        yield Button("No", id="no")

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

# Usage with callback
def confirm_action(self) -> None:
    self.app.push_screen(ConfirmDialog(), self.on_confirm)

def on_confirm(self, result: bool) -> None:
    if result:
        self.do_action()
```

**Modes** for independent screen stacks:
```python
class MyApp(App):
    MODES = {
        "main": MainScreen,
        "settings": SettingsScreen,
    }

    BINDINGS = [("s", "switch_mode('settings')", "Settings")]
```

### Concurrency Patterns

**Async workers** (for HTTP, async I/O):
```python
from textual.work import work

@work(exclusive=True)  # Cancels previous if still running
async def fetch_data(self, url: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    self.display_data(response.json())
```

**Thread workers** (for blocking I/O):
```python
@work(thread=True, exclusive=True)
def load_file(self, path: str) -> None:
    with open(path) as f:
        data = f.read()
    # Must use call_from_thread for UI updates
    self.app.call_from_thread(self.display_data, data)
```

### Testing Pattern

```python
import pytest

async def test_button_click():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.click("#submit")
        assert app.query_one("#result").renderable == "Success"

async def test_keyboard():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.press("tab", "enter")
        assert app.submitted
```

### Query Pattern

```python
# Single widget (raises if not found)
button = self.query_one("#submit", Button)

# Multiple widgets
for btn in self.query("Button.active"):
    btn.disabled = True

# Bulk operations (no loops needed)
self.query("Button").add_class("disabled")
self.query(".hidden").remove()
```

---

## 3. Canonical Examples

### Minimal App Template

```python
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Static

class MinimalApp(App):
    CSS = """
    Screen { layout: vertical; }
    #content { height: 1fr; padding: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Content here", id="content")
        yield Footer()

if __name__ == "__main__":
    MinimalApp().run()
```

### Custom Widget with State

```python
from textual.reactive import reactive
from textual.widgets import Static
from textual import on

class ClickCounter(Static):
    """A widget that counts clicks."""

    count = reactive(0)

    def render(self) -> str:
        return f"Clicked {self.count} times"

    def on_click(self) -> None:
        self.count += 1
```

### Modal Dialog Pattern

```python
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical
from textual import on

class InputDialog(ModalScreen[str]):
    """Modal that returns user input."""

    CSS = """
    InputDialog { align: center middle; }
    #dialog { width: 50; height: auto; padding: 1; border: thick $primary; }
    """

    def __init__(self, prompt: str) -> None:
        self.prompt = prompt
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.prompt)
            yield Input(id="input")
            yield Button("OK", id="ok")
            yield Button("Cancel", id="cancel")

    @on(Button.Pressed, "#ok")
    @on(Input.Submitted)
    def submit(self) -> None:
        self.dismiss(self.query_one("#input", Input).value)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss("")

# Usage
def get_input(self) -> None:
    self.app.push_screen(InputDialog("Enter name:"), self.handle_input)

def handle_input(self, value: str) -> None:
    if value:
        self.process_name(value)
```

### Data Loading Pattern

```python
from textual.app import App, ComposeResult
from textual.widgets import Static, LoadingIndicator
from textual.work import work

class DataApp(App):
    def compose(self) -> ComposeResult:
        yield LoadingIndicator(id="loader")
        yield Static(id="content")

    def on_mount(self) -> None:
        self.load_data()

    @work(exclusive=True)
    async def load_data(self) -> None:
        self.query_one("#loader").display = True
        self.query_one("#content").display = False

        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com/data")

        self.query_one("#loader").display = False
        self.query_one("#content").display = True
        self.query_one("#content").update(response.text)
```

### Data Binding Pattern (Advanced)

```python
from textual.reactive import reactive

class MainScreen(Screen):
    theme = reactive("dark")

    def compose(self) -> ComposeResult:
        # Child widgets bind to parent's reactive
        yield ThemeSelector().data_bind(MainScreen.theme)
        yield ContentPane().data_bind(theme=MainScreen.theme)
```

---

## 4. Gotchas & Anti-Patterns

### Common Mistakes

1. **Centering with `align`**: Applies to *children*, not the element itself
   ```css
   /* Wrong: align on the widget to center */
   MyWidget { align: center middle; }

   /* Right: align on the parent */
   Screen { align: center middle; }
   ```

2. **Thread worker UI updates**: Can't call widget methods from threads
   ```python
   # Wrong
   @work(thread=True)
   def load(self):
       self.label.update("Done")  # Crashes!

   # Right
   @work(thread=True)
   def load(self):
       self.app.call_from_thread(self.label.update, "Done")
   ```

3. **Forgetting `thread=True`**: Since v0.31.0, sync workers require explicit flag
   ```python
   # Wrong (WorkerDeclarationError)
   @work()
   def blocking_call(self): ...

   # Right
   @work(thread=True)
   def blocking_call(self): ...
   ```

4. **Lost asyncio tasks**: Store references to prevent garbage collection
   ```python
   # Wrong - task may be garbage collected
   asyncio.create_task(self.background_work())

   # Right - keep reference
   self._task = asyncio.create_task(self.background_work())
   ```

### Performance Tips

- **Cache tree-sitter queries**: Recreating Query objects per keystroke causes 94% slowdown
- **Use tuples over NamedTuples** in hot loops: 40% faster creation
- **Lazy load screens**: `SCREENS = {"settings": get_settings_screen}` defers imports
- **Use `exclusive=True`** for workers: Prevents out-of-order responses

### Terminal Compatibility

- **macOS Terminal.app**: Poor rendering. Use iTerm2, Kitty, or WezTerm
- **Key limitations**: Cmd/Option (macOS), Windows key don't pass through. Use `textual keys` to test
- **No ANSI colors**: By design; use theme system for consistent cross-platform appearance

---

## 5. Testing

Textual provides robust testing support through async test patterns, a Pilot simulation API, and visual snapshot testing.

### Test Framework Setup

Use **pytest** with **pytest-asyncio** for async test support:

```bash
pip install pytest pytest-asyncio pytest-textual-snapshot
```

Configure pytest to auto-detect async tests in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
```

### Core Testing Pattern

The `run_test()` async context manager runs apps in headless mode and returns a `Pilot` for simulating interactions:

```python
async def test_button_click():
    app = MyApp()
    async with app.run_test() as pilot:
        # Simulate user interactions
        await pilot.click("#submit")
        # Assert on state
        assert app.query_one("#result").renderable == "Success"
```

### Pilot API Reference

**Keyboard simulation**:
```python
# Single key
await pilot.press("enter")

# Multiple keys in sequence
await pilot.press("tab", "tab", "enter")

# Type text (spread string into chars)
await pilot.press(*"Hello, World!")

# Modifier combinations
await pilot.press("ctrl+s", "shift+tab", "ctrl+shift+z")
```

**Mouse simulation**:
```python
# Click by CSS selector
await pilot.click("#submit")

# Click by widget type
await pilot.click(Button)

# Click with offset (relative to widget)
await pilot.click("#canvas", offset=(10, 5))

# Double-click
await pilot.click(Button, times=2)

# Click with modifier
await pilot.click("#item", control=True)

# Hover (triggers :hover pseudo-class)
await pilot.hover(Button)
```

**Timing control**:
```python
# Wait for pending messages to process
await pilot.pause()

# Custom terminal size for test
async with app.run_test(size=(100, 50)) as pilot:
    ...
```

### Widget Queries in Tests

```python
async with app.run_test() as pilot:
    # Query single widget (raises if not found)
    button = app.query_one("#submit", Button)

    # Query multiple widgets
    inputs = app.query("Input.validated")

    # Access via pilot
    result = pilot.app.query_one("#output")
```

### Assertion Patterns

```python
# Widget state
assert button.disabled is False
assert input.value == "expected text"

# Pseudo-classes
assert "focus" in widget.pseudo_classes
assert "hover" in button.pseudo_classes

# Styles
assert widget.styles.background == Color.parse("blue")
assert widget.styles.display == "block"

# DOM structure
assert len(app.query("Button")) == 3

# Screen state
assert app.screen.id == "main"
```

### Message/Event Testing

Track messages with a collection in your test app:

```python
class TestApp(App):
    def __init__(self):
        super().__init__()
        self.messages: list[str] = []

    def compose(self) -> ComposeResult:
        yield Input()
        yield Button("Submit")

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        self.messages.append(f"Changed: {event.value}")

    @on(Button.Pressed)
    def on_button_pressed(self) -> None:
        self.messages.append("Pressed")

async def test_message_flow():
    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.press(*"test")
        await pilot.click(Button)

        assert app.messages == [
            "Changed: t",
            "Changed: te",
            "Changed: tes",
            "Changed: test",
            "Pressed"
        ]
```

### Snapshot Testing

The **pytest-textual-snapshot** plugin captures SVG screenshots for visual regression testing.

**Basic snapshot test**:
```python
def test_app_appearance(snap_compare):
    assert snap_compare("path/to/app.py")

def test_with_app_instance(snap_compare):
    assert snap_compare(MyApp())
```

**With key simulation**:
```python
def test_after_interaction(snap_compare):
    press = ["tab", "enter", "down", "down"]
    assert snap_compare("path/to/app.py", press=press)
```

**With async setup via `run_before`**:
```python
def test_with_setup(snap_compare):
    async def run_before(pilot):
        # Disable cursor blink for deterministic screenshots
        pilot.app.query(Input).first().cursor_blink = False
        await pilot.press("tab")

    assert snap_compare(MyApp(), run_before=run_before)
```

**Custom terminal size**:
```python
def test_small_terminal(snap_compare):
    assert snap_compare(MyApp(), terminal_size=(40, 20))
```

**snap_compare parameters**:
| Parameter | Description |
|-----------|-------------|
| `app_path` | Path to app file or App instance |
| `press` | List of keys to simulate (supports `"wait:N"` for delays) |
| `run_before` | Async callback `(pilot) -> None` executed before screenshot |
| `terminal_size` | Tuple `(width, height)` for custom dimensions |

**Updating snapshots**:
```bash
# Only run after verifying output looks correct
pytest --snapshot-update
```

### Test Organization Patterns

**Dedicated test apps** (inline for focused tests):
```python
async def test_specific_behavior():
    class TestApp(App):
        CSS = "Button { width: 100%; }"

        def compose(self) -> ComposeResult:
            yield Button("Test", id="btn")

    async with TestApp().run_test() as pilot:
        await pilot.click("#btn")
        # assertions...
```

**Fixtures for reusable test setup**:
```python
@pytest.fixture
def app_with_data():
    app = MyApp()
    app.load_test_data()
    return app

async def test_with_fixture(app_with_data):
    async with app_with_data.run_test() as pilot:
        # test code...
```

**Parametrized tests**:
```python
@pytest.mark.parametrize("theme", ["dark", "light", "nord"])
async def test_themes(theme):
    app = MyApp()
    app.theme = theme
    async with app.run_test() as pilot:
        # verify theme-specific behavior
```

### Best Practices

1. **Use `pilot.pause()`** after interactions before assertions to ensure messages are processed

2. **Disable animations** for deterministic tests:
   ```python
   async def run_before(pilot):
       pilot.app.query(Input).first().cursor_blink = False
   ```

3. **Test both keyboard and mouse paths** - users interact differently

4. **Snapshot test critical UI states** - ensures visual consistency across releases

5. **Keep test apps minimal** - include only widgets relevant to the test

6. **Name snapshots descriptively** - test function names become snapshot filenames

7. **Run snapshot tests in CI** - catch visual regressions before merge

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_myapp.py

# Run tests matching pattern
pytest -k "test_button"

# Run with verbose output
pytest -v

# Update snapshots (after visual verification)
pytest --snapshot-update

# Parallel execution
pytest -n auto
```

---

## 6. Quick Reference

### Widget Gallery

| Category | Widgets |
|----------|---------|
| **Input** | Button, Input, TextArea, Checkbox, RadioButton, Switch, Select, OptionList |
| **Display** | Label, Static, Markdown, Pretty, Digits, RichLog, Rule, Sparkline |
| **Container** | Container, Horizontal, Vertical, Grid, ScrollableContainer, Collapsible |
| **Data** | DataTable, ListView, Tree, DirectoryTree |
| **Navigation** | Header, Footer, Tabs, TabbedContent |
| **Feedback** | ProgressBar, LoadingIndicator, Toast |

### CSS Property Cheatsheet

| Property | Common Values | Description |
|----------|---------------|-------------|
| `layout` | vertical, horizontal, grid | Child arrangement |
| `dock` | top, bottom, left, right | Fixed position |
| `width/height` | auto, N, N%, Nfr | Sizing (fr=fractional) |
| `margin/padding` | N or (top right bottom left) | Spacing |
| `background` | color, $variable | Background color |
| `color` | color, auto | Text color |
| `border` | style color | Widget border |
| `align` | horizontal vertical | Child alignment |
| `overflow` | auto, hidden, scroll | Scrollbar behavior |
| `display` | block, none | Show/hide |

### Theme Variables

```css
$primary       /* Branding color */
$secondary     /* Alternative brand */
$background    /* Screen background */
$surface       /* Widget background */
$foreground    /* Default text */
$success       /* Success states */
$warning       /* Warning states */
$error         /* Error states */

/* Shades: add -lighten-1/2/3 or -darken-1/2/3 */
$primary-lighten-2
$error-darken-1
```

### Key Imports

```python
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widget import Widget
from textual.widgets import Static, Button, Input, Label, DataTable
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.reactive import reactive, var
from textual.work import work
from textual.binding import Binding
from textual import on
```

### Common Events

| Event | Fires When |
|-------|------------|
| `Button.Pressed` | Button clicked |
| `Input.Changed` | Input text changes |
| `Input.Submitted` | Enter pressed in input |
| `Key` | Any key pressed |
| `Click` | Widget clicked |
| `Mount` | Widget added to DOM |
| `Unmount` | Widget removed from DOM |
| `Focus` | Widget gains focus |
| `Blur` | Widget loses focus |

---

*Generated from Textual v7.3.0 documentation and example applications.*
