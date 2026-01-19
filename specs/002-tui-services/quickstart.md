# Quickstart: TUI Generation and Service Layer

**Feature**: 002-tui-services
**Date**: 2026-01-17

## Prerequisites

- Python 3.12+
- Hive framework installed
- Terminal supporting 80x24 minimum

## Installation

```bash
# Install with TUI support (includes textual, keyring)
pip install hive-framework[tui]
```

## 1. Define Screens

Create screens using the `@screen` decorator:

```python
# myapp/screens.py
from hive import App, screen
from hive.tui import HiveScreen, HiveHeader, HiveFooter, HiveDataTable

app = App("myapp")

@screen(app, default=True, keybinding="d", queries=["list_tasks"])
class DashboardScreen(HiveScreen):
    """Main dashboard showing tasks."""

    def compose(self):
        yield HiveHeader()
        yield HiveDataTable(id="tasks")
        yield HiveFooter()

@screen(app, keybinding="s")
class SettingsScreen(HiveScreen):
    """Application settings."""

    def compose(self):
        yield HiveHeader()
        yield Static("Settings go here")
        yield HiveFooter()
```

## 2. Define Queries for Data Binding

```python
# myapp/queries.py
from hive import query
from myapp.models import Task

@query(app, entities=[Task])
async def list_tasks(ctx, completed: bool | None = None) -> list[Task]:
    """List all tasks."""
    query = ctx.db.query(Task)
    if completed is not None:
        query = query.filter(Task.completed == completed)
    return await query.all()
```

## 3. Define Services (Optional)

```python
# myapp/services.py
from hive import service
import httpx

@service(app, credentials="keyring:github")
def github_client(token: str) -> httpx.AsyncClient:
    """GitHub API client."""
    return httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={"Authorization": f"Bearer {token}"}
    )
```

Store credentials:
```bash
# Using hive CLI
hive credentials set github

# Or manually via keyring
python -c "import keyring; keyring.set_password('hive', 'github', 'your-token')"
```

## 4. Run the TUI

```bash
# Start TUI application
hive tui

# Or programmatically
from hive.generators.tui import generate_tui_app

app = generate_tui_app(myapp.app)
app.run()
```

## 5. Navigation

| Key | Action |
|-----|--------|
| `d` | Go to Dashboard |
| `s` | Go to Settings |
| `Ctrl+P` | Open Command Palette |
| `q` | Quit |

## 6. Using Command Palette

1. Press `Ctrl+P` to open
2. Type to search commands
3. Press `Enter` to select
4. Fill parameters if prompted
5. View result in notification

## 7. Query Data Binding

Screens automatically load bound queries:

```python
@screen(app, queries=["list_tasks"])
class TaskScreen(HiveScreen):
    def compose(self):
        # HiveDataTable auto-binds to 'list_tasks' query result
        yield HiveDataTable(id="tasks")

    def watch_data(self, data: list[Task]):
        # React to data changes
        self.notify(f"Loaded {len(data)} tasks")
```

## 8. Service Access in Commands

```python
@command(app)
async def sync_repos(ctx) -> list[Repo]:
    """Sync repositories from GitHub."""
    client = ctx.services.github_client  # Lazy instantiation
    response = await client.get("/user/repos")
    return [Repo(**r) for r in response.json()]
```

## 9. Testing TUI

```python
# tests/test_screens.py
from hive.testing.tui import create_test_app

async def test_dashboard_loads_tasks():
    app = create_test_app()
    async with app.run_test() as pilot:
        # Dashboard is default screen
        assert app.screen.name == "DashboardScreen"

        # Wait for data to load
        await pilot.pause()

        # Verify table has data
        table = app.query_one("#tasks", HiveDataTable)
        assert len(table.data) > 0

async def test_navigation():
    app = create_test_app()
    async with app.run_test() as pilot:
        await pilot.press("s")  # Settings keybinding
        assert app.screen.name == "SettingsScreen"
```

## Common Patterns

### Custom Data Table Columns

```python
class TaskScreen(HiveScreen):
    def compose(self):
        yield HiveDataTable(
            id="tasks",
            columns=["title", "completed", "due_date"]  # Explicit columns
        )
```

### Manual Query Refresh

```python
@on(Button.Pressed, "#refresh")
async def refresh_data(self):
    await self.refresh_data()  # Re-executes bound queries
```

### Service with Cleanup

```python
@service(app, credentials="keyring:db", cleanup=lambda p: p.close())
def db_pool(connection_string: str) -> Pool:
    return create_pool(connection_string)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Credentials not found | Run `hive credentials set <service>` |
| Screen not showing | Check `@screen` decorator is applied |
| Query not loading | Verify query name in `queries=[]` matches |
| Keybinding conflict | Check for duplicate keybindings in registry |
