# Screens

Screens are Textual TUI views that provide interactive terminal interfaces. They enable rich, keyboard-driven user experiences with reactive data binding and automatic query loading.

## Basic Usage

Use the `@screen` decorator to register a Textual screen class:

```python
from hive import App, screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static

app = App("tasks")

@screen(app, default=True)
class DashboardScreen(HiveScreen):
    """Main dashboard view."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Welcome to Tasks!")
        yield Footer()
```

## Decorator Parameters

### default

Mark a screen as the startup screen:

```python
@screen(app, default=True)
class HomeScreen(HiveScreen):
    """This screen shows on app launch."""
    ...
```

!!! note "Single Default"
    Only one screen should be marked as `default=True`. If multiple screens
    have `default=True`, the last registered one wins.

### keybinding

Assign a global keyboard shortcut to navigate to the screen:

```python
@screen(app, keybinding="d")
class DashboardScreen(HiveScreen):
    """Press 'd' anywhere to jump to dashboard."""
    ...

@screen(app, keybinding="t")
class TasksScreen(HiveScreen):
    """Press 't' anywhere to jump to tasks."""
    ...
```

### queries

Specify queries to automatically load when the screen mounts:

```python
@screen(app, queries=["list_tasks", "task_stats"])
class TasksScreen(HiveScreen):
    """Auto-loads task data on mount."""

    def on_mount(self) -> None:
        # self.data["list_tasks"] contains query results
        tasks = self.data.get("list_tasks", [])
        self.query_one(DataTable).add_rows(
            [(t.id, t.title) for t in tasks]
        )
```

### name

Override the screen name (defaults to class name):

```python
@screen(app, name="home")
class MainDashboardScreen(HiveScreen):
    """Registered as 'home' for navigation."""
    ...
```

## Building Screens

### Basic Structure

```python
from textual.app import ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.containers import Container

@screen(app, default=True, keybinding="h", queries=["list_tasks"])
class HomeScreen(HiveScreen):
    """Home screen with task list."""

    CSS = """
    DataTable {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            DataTable(id="tasks"),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        table = self.query_one("#tasks", DataTable)
        table.add_columns("ID", "Title", "Status")

        tasks = self.data.get("list_tasks", [])
        for task in tasks:
            status = "Done" if task.completed else "Pending"
            table.add_row(task.id, task.title, status)
```

### Handling User Input

```python
from textual.widgets import Input, Button
from textual.containers import Horizontal

@screen(app, keybinding="a")
class AddTaskScreen(HiveScreen):
    """Screen for adding new tasks."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Task title", id="title")
        yield Horizontal(
            Button("Add", id="add", variant="primary"),
            Button("Cancel", id="cancel"),
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            title = self.query_one("#title", Input).value
            if title:
                # Execute command through context
                await self.ctx.execute("add", title=title)
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()
```

### Reactive Data

Use Textual's reactive attributes for automatic UI updates:

```python
from textual.reactive import reactive

@screen(app, queries=["task_stats"])
class StatsScreen(HiveScreen):
    """Statistics screen with reactive updates."""

    total_tasks: reactive[int] = reactive(0)
    completed_tasks: reactive[int] = reactive(0)

    def on_mount(self) -> None:
        stats = self.data.get("task_stats", {})
        self.total_tasks = stats.get("total", 0)
        self.completed_tasks = stats.get("completed", 0)

    def watch_total_tasks(self, value: int) -> None:
        """Called when total_tasks changes."""
        self.query_one("#total", Static).update(f"Total: {value}")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="total")
        yield Static(id="completed")
        yield Footer()
```

## Navigation

### Push and Pop

```python
@screen(app)
class DetailScreen(HiveScreen):
    """Task detail view."""

    def __init__(self, task_id: int) -> None:
        super().__init__()
        self.task_id = task_id

    async def on_mount(self) -> None:
        task = await self.ctx.execute("get_task", task_id=self.task_id)
        # Display task details...

# Navigate to detail screen
@screen(app, keybinding="t")
class TaskListScreen(HiveScreen):
    """Task list with navigation."""

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        task_id = event.row_key.value
        self.app.push_screen(DetailScreen(task_id))
```

### Screen Switching

```python
@screen(app, keybinding="1")
class Screen1(HiveScreen):
    BINDINGS = [("2", "switch_screen", "Go to Screen 2")]

    def action_switch_screen(self) -> None:
        self.app.switch_screen("Screen2")
```

## Styling with CSS

Textual uses CSS for styling:

```python
@screen(app)
class StyledScreen(HiveScreen):
    """Screen with custom styles."""

    CSS = """
    Screen {
        background: $surface;
    }

    #header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
    }

    #content {
        padding: 1 2;
    }

    Button {
        margin: 1;
    }

    Button.primary {
        background: $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("My App", id="header")
        yield Container(
            Static("Content here"),
            id="content"
        )
        yield Button("Primary", classes="primary")
        yield Button("Secondary")
```

## Common Patterns

### Data Table with Actions

```python
@screen(app, queries=["list_tasks"])
class TaskTableScreen(HiveScreen):
    """Interactive task table."""

    BINDINGS = [
        ("a", "add_task", "Add"),
        ("d", "delete_task", "Delete"),
        ("enter", "view_task", "View"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="tasks", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#tasks", DataTable)
        table.add_columns("ID", "Title", "Priority", "Status")

        for task in self.data.get("list_tasks", []):
            table.add_row(
                task.id,
                task.title,
                task.priority,
                "Done" if task.completed else "Pending",
                key=task.id,
            )

    def action_add_task(self) -> None:
        self.app.push_screen(AddTaskScreen())

    async def action_delete_task(self) -> None:
        table = self.query_one("#tasks", DataTable)
        if table.cursor_row is not None:
            task_id = table.get_row_at(table.cursor_row)[0]
            await self.ctx.execute("delete", task_id=task_id)
            table.remove_row(task_id)

    def action_view_task(self) -> None:
        table = self.query_one("#tasks", DataTable)
        if table.cursor_row is not None:
            task_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(TaskDetailScreen(task_id))
```

### Modal Dialogs

```python
from textual.screen import ModalScreen

@screen(app)
class ConfirmDialog(ModalScreen[bool]):
    """Confirmation dialog."""

    CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #dialog {
        width: 40;
        height: 10;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.message),
            Horizontal(
                Button("Yes", id="yes", variant="primary"),
                Button("No", id="no"),
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")
```

## Best Practices

!!! success "Do"
    - Use `queries` parameter for automatic data loading
    - Define keyboard bindings for common actions
    - Use Textual's reactive system for UI updates
    - Keep screens focused on a single responsibility
    - Use CSS for consistent styling

!!! failure "Don't"
    - Block the event loop with synchronous operations
    - Store mutable state in class attributes without reactive
    - Create deeply nested screen hierarchies
    - Ignore keyboard accessibility
