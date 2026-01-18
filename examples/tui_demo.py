"""Demo TUI application to manually test spec 002 features.

Run with: uv run python examples/tui_demo.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field
from textual.app import ComposeResult
from textual.widgets import Static

from hive import App
from hive.core.decorators import command, query, screen
from hive.generators.tui import generate_tui_app
from hive.tui.screens import HiveScreen
from hive.tui.widgets import HiveDataTable, HiveFooter, HiveHeader

# Create the Hive app
app = App("tui-demo")


# Define a data model
class Task(BaseModel):
    """A task item."""

    id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    completed: bool = Field(default=False, description="Completion status")


# Sample data
TASKS = [
    Task(id=1, title="Implement TUI generation", completed=True),
    Task(id=2, title="Add service layer", completed=True),
    Task(id=3, title="Create command palette", completed=True),
    Task(id=4, title="Build standard widgets", completed=True),
    Task(id=5, title="Write documentation", completed=False),
]


# Define queries
@query(app)
async def list_tasks(_ctx: Any) -> list[Task]:
    """List all tasks."""
    await asyncio.sleep(0.1)  # Simulate async operation
    return TASKS


@query(app)
async def get_stats(_ctx: Any) -> dict[str, int]:
    """Get task statistics."""
    completed = sum(1 for t in TASKS if t.completed)
    return {"total": len(TASKS), "completed": completed, "pending": len(TASKS) - completed}


# Define commands
@command(app)
async def add_task(_ctx: Any, title: str) -> str:
    """Add a new task."""
    new_id = max(t.id for t in TASKS) + 1
    TASKS.append(Task(id=new_id, title=title))
    return f"Added task {new_id}: {title}"


@command(app)
async def complete_task(_ctx: Any, task_id: int) -> str:
    """Mark a task as complete."""
    for task in TASKS:
        if task.id == task_id:
            task.completed = True
            return f"Completed task {task_id}"
    return f"Task {task_id} not found"


@command(app)
async def greet(_ctx: Any, name: str, excited: bool = False) -> str:
    """Greet someone."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting = greeting.upper()
    return greeting


# Define screens
@screen(app, default=True, keybinding="t", queries=["list_tasks"])
class TasksScreen(HiveScreen[None]):
    """Tasks screen showing all tasks."""

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield HiveHeader(show_screen_title=True)
        yield HiveDataTable[Task]()
        yield HiveFooter(show_command_palette_hint=True)

    def on_mount(self) -> None:
        """Called when screen mounts."""
        super().on_mount()
        # Set data when available
        if self.data:
            table = self.query_one(HiveDataTable)
            table.set_data(self.data)

    def watch_data(self, data: list[Any]) -> None:
        """React to data changes."""
        if data:
            table = self.query_one(HiveDataTable)
            table.set_data(data)


@screen(app, keybinding="s")
class StatsScreen(HiveScreen[None]):
    """Statistics screen."""

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield HiveHeader(show_screen_title=True)
        yield Static("Task Statistics", id="stats-title")
        yield Static("Press 't' to go to Tasks", id="stats-hint")
        yield HiveFooter()


@screen(app, keybinding="h")
class HelpScreen(HiveScreen[None]):
    """Help screen."""

    HELP_TEXT = """
    TUI Demo - Keyboard Shortcuts
    ==============================

    Navigation:
      t - Tasks screen
      s - Stats screen
      h - Help screen (this screen)
      q - Quit

    Commands:
      Ctrl+P - Open command palette
      Enter  - Select command
      Escape - Close palette

    Try these commands in the palette:
      - add_task: Add a new task
      - complete_task: Mark task as done
      - greet: Say hello
    """

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield HiveHeader(show_screen_title=True)
        yield Static(self.HELP_TEXT, id="help-text")
        yield HiveFooter()


def main() -> None:
    """Run the TUI demo."""
    tui = generate_tui_app(app)
    tui.title = "TUI Demo"
    tui.sub_title = "spec 002"
    tui.run()


if __name__ == "__main__":
    main()
