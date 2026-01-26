"""TUI screens for Trakr.

Provides rich terminal interface with keyboard navigation.
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from hive.core.decorators import screen
from hive.tui.screens import HiveScreen
from hive.tui.widgets import HiveDataTable, HiveFooter, HiveHeader
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, Vertical
from textual.timer import Timer
from textual.widgets import Static

from trakr.app import app
from trakr.entities import TimeEntry


@screen(app, default=True, keybinding="d", queries=["get_time_summary"])
class DashboardScreen(HiveScreen[None]):
    """Main dashboard showing current status and quick actions.

    Keybinding: d
    """

    DEFAULT_CSS: ClassVar[str] = """
    DashboardScreen {
        layout: vertical;
    }

    DashboardScreen #dashboard {
        padding: 1 2;
    }

    DashboardScreen .section {
        padding: 1;
        margin-bottom: 1;
        border: tall $primary;
        background: $surface;
    }

    DashboardScreen .section-title {
        text-style: bold;
        margin-bottom: 1;
    }

    DashboardScreen #current-timer {
        height: auto;
        min-height: 2;
    }

    DashboardScreen #timer-hint {
        color: $text-muted;
        text-style: italic;
    }

    DashboardScreen #summary-stats {
        height: auto;
    }

    DashboardScreen #actions {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
    }

    DashboardScreen.loading #dashboard {
        opacity: 0.5;
    }

    DashboardScreen.error .section {
        border: solid $error;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("s", "start_timer", "Start Timer"),
        Binding("x", "stop_timer", "Stop Timer"),
        Binding("p", "go_projects", "Projects"),
        Binding("t", "go_time", "Time Entries"),
        Binding("r", "refresh", "Refresh"),
    ]

    _timer_interval: Timer | None = None

    @override
    def compose(self) -> ComposeResult:
        """Build the dashboard layout."""
        yield HiveHeader(show_screen_title=True)

        with Container(id="dashboard"):
            # Current timer section
            with Vertical(id="timer-section", classes="section"):
                yield Static("Current Timer", classes="section-title")
                yield Static("No timer running", id="current-timer")
                yield Static("Press 's' to start", id="timer-hint")

            # Summary section
            with Vertical(id="summary-section", classes="section"):
                yield Static("This Week", classes="section-title")
                yield Static("Loading...", id="summary-stats")

            # Quick actions
            with Horizontal(id="actions"):
                yield Static("[s] Start  [x] Stop  [p] Projects  [t] Time  [r] Refresh")

        yield HiveFooter(show_command_palette_hint=True)

    @override
    async def on_mount(self) -> None:
        """Load initial data and start timer refresh."""
        await super().on_mount()
        # Initial timer display update
        self.run_worker(self._update_timer_display(), exclusive=True, name="timer_update")
        # Set up 1-second interval for timer updates
        self._timer_interval = self.set_interval(1.0, self._tick_timer)

    def on_unmount(self) -> None:
        """Clean up timer interval when screen is unmounted."""
        if self._timer_interval:
            self._timer_interval.stop()
            self._timer_interval = None

    def _tick_timer(self) -> None:
        """Periodic callback to update timer display."""
        self.run_worker(self._update_timer_display(), exclusive=True, name="timer_update")

    def watch_data(self, data: list[Any]) -> None:
        """Update display when data changes."""
        if data:
            summary = data[0] if data else None
            if summary:
                stats = self.query_one("#summary-stats", Static)
                stats.update(
                    f"Total: {summary.total_hours:.1f}h | "
                    f"Billable: {summary.billable_hours:.1f}h (${summary.billable_amount})"
                )

    def watch_is_loading(self, loading: bool) -> None:
        """Update visual state when loading changes."""
        if loading:
            self.add_class("loading")
        else:
            self.remove_class("loading")

    def watch_error(self, error: str | None) -> None:
        """Update visual state when error changes."""
        if error:
            self.add_class("error")
            self.ctx.notify(f"Error: {error}", severity="error")
        else:
            self.remove_class("error")

    async def _update_timer_display(self) -> None:
        """Update the current timer display with running timer info."""
        timer_display = self.query_one("#current-timer", Static)
        timer_hint = self.query_one("#timer-hint", Static)

        if self._registry is None:
            timer_display.update("No timer running")
            timer_hint.update("Press 's' to start")
            return

        cmd = self._registry.get_command("current")
        if cmd is None:
            timer_display.update("No timer running")
            timer_hint.update("Press 's' to start")
            return

        from hive.runtime.context import ExecutionContext  # noqa: PLC0415
        from hive.runtime.output import OutputFormat  # noqa: PLC0415

        try:
            async with ExecutionContext(
                registry=self._registry,
                output_format=OutputFormat.TABLE,
                command_name="current",
                allow_concurrent=True,
            ) as ctx:
                entry = await cmd.func(ctx)

                if entry is None:
                    timer_display.update("No timer running")
                    timer_hint.update("Press 's' to start")
                else:
                    hours = entry.duration_hours
                    mins = int((hours % 1) * 60)
                    whole_hours = int(hours)
                    desc = entry.description[:30] if entry.description else "Working..."
                    timer_display.update(
                        f"[bold green]RUNNING[/bold green] {desc}\n"
                        + f"Duration: {whole_hours}h {mins}m"
                    )
                    timer_hint.update("Press 'x' to stop")
        except Exception as e:  # noqa: BLE001
            timer_display.update(f"Error: {e}")
            timer_hint.update("Press 's' to start")

    async def action_start_timer(self) -> None:
        """Open timer start dialog."""
        from hive.tui.widgets.modal import ParameterModal  # noqa: PLC0415

        if self._registry is None:
            self.ctx.notify("Registry not available", severity="error")
            return

        cmd = self._registry.get_command("start_timer")
        if cmd is None:
            self.ctx.notify("start_timer command not found", severity="error")
            return

        modal = ParameterModal(cmd)
        await self.app.push_screen(modal)

    async def action_stop_timer(self) -> None:
        """Stop the current timer."""
        if self._registry is None:
            self.ctx.notify("Registry not available", severity="error")
            return

        cmd = self._registry.get_command("stop_timer")
        if cmd is None:
            self.ctx.notify("stop_timer command not found", severity="error")
            return

        from hive.runtime.context import ExecutionContext  # noqa: PLC0415
        from hive.runtime.output import OutputFormat  # noqa: PLC0415

        try:
            async with ExecutionContext(
                registry=self._registry,
                output_format=OutputFormat.TABLE,
                command_name="stop_timer",
                allow_concurrent=True,
            ) as ctx:
                entry = await cmd.func(ctx)

                if entry is None:
                    self.ctx.notify("No timer running", severity="warning")
                else:
                    self.ctx.notify(
                        f"Timer stopped: {entry.duration_hours:.2f}h",
                        severity="information",
                    )
        except Exception as e:  # noqa: BLE001
            self.ctx.notify(f"Error stopping timer: {e}", severity="error")

    async def action_go_projects(self) -> None:
        """Navigate to projects screen."""
        await self.ctx.navigate("ProjectsScreen")

    async def action_go_time(self) -> None:
        """Navigate to time entries screen."""
        await self.ctx.navigate("TimeScreen")

    async def action_refresh(self) -> None:
        """Refresh dashboard data."""
        await self.refresh_data()


@screen(app, keybinding="p", queries=["list_projects"])
class ProjectsScreen(HiveScreen[None]):
    """Project list with status and budget info.

    Keybinding: p
    """

    DEFAULT_CSS: ClassVar[str] = """
    ProjectsScreen {
        layout: vertical;
    }

    ProjectsScreen #projects-table {
        height: 1fr;
        margin: 1 2;
    }

    ProjectsScreen.loading #projects-table {
        opacity: 0.5;
    }

    ProjectsScreen.error #projects-table {
        border: solid $error;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("n", "new_project", "New Project"),
        Binding("enter", "view_project", "View Details"),
        Binding("a", "filter_active", "Active Only"),
        Binding("escape", "go_back", "Back"),
    ]

    _client_cache: dict[int, str] = {}

    @override
    def compose(self) -> ComposeResult:
        """Build the projects list."""
        yield HiveHeader(show_screen_title=True)
        yield HiveDataTable[Any](id="projects-table")
        yield HiveFooter()

    @override
    async def on_mount(self) -> None:
        """Set up the table."""
        await super().on_mount()
        table = self.query_one("#projects-table", HiveDataTable)
        table.add_columns("ID", "Name", "Client", "Status", "Budget")
        # Load clients for name resolution
        if self._registry:
            self.run_worker(self._load_clients(), exclusive=False, name="load_clients")

    def watch_data(self, data: list[Any]) -> None:
        """Populate table when data loads."""
        if not data:
            return

        table = self.query_one("#projects-table", HiveDataTable)
        table.clear()

        for project in data:
            budget = f"{project.budget_hours}h" if project.budget_hours else "-"
            client_name = self._client_cache.get(project.client_id, f"Client #{project.client_id}")
            table.add_row(
                str(project.id),
                project.name,
                client_name,
                project.status.value,
                budget,
            )

    def watch_is_loading(self, loading: bool) -> None:
        """Update visual state when loading changes."""
        if loading:
            self.add_class("loading")
        else:
            self.remove_class("loading")

    def watch_error(self, error: str | None) -> None:
        """Update visual state when error changes."""
        if error:
            self.add_class("error")
            self.ctx.notify(f"Error: {error}", severity="error")
        else:
            self.remove_class("error")

    async def _load_clients(self) -> None:
        """Load all clients into the cache for name resolution."""
        if self._registry is None:
            return

        query = self._registry.get_query("list_clients")
        if query is None:
            return

        from hive.runtime.context import ExecutionContext  # noqa: PLC0415
        from hive.runtime.output import OutputFormat  # noqa: PLC0415

        try:
            async with ExecutionContext(
                registry=self._registry,
                output_format=OutputFormat.TABLE,
                command_name="list_clients",
                allow_concurrent=True,
            ) as ctx:
                clients = await query.func(ctx)

                for client in clients:
                    self._client_cache[client.id] = client.name

            # Re-trigger data display to update client names
            if self.data:
                self.watch_data(self.data)
        except Exception:  # noqa: BLE001, S110
            pass  # Silently fail - just show IDs

    async def action_new_project(self) -> None:
        """Open new project dialog."""
        from hive.tui.widgets.modal import ParameterModal  # noqa: PLC0415

        if self._registry is None:
            self.ctx.notify("Registry not available", severity="error")
            return

        cmd = self._registry.get_command("create_project")
        if cmd is None:
            self.ctx.notify("create_project command not found", severity="error")
            return

        modal = ParameterModal(cmd)
        await self.app.push_screen(modal)

    async def action_view_project(self) -> None:
        """View selected project details."""
        table = self.query_one("#projects-table", HiveDataTable)
        if table.row_count == 0:
            self.ctx.notify("No project selected", severity="warning")
            return
        cursor_row = table.cursor_row

        row_data = table.get_row_at(cursor_row)
        if not row_data:
            return

        project_id = int(row_data[0])

        if self._registry is None:
            self.ctx.notify("Registry not available", severity="error")
            return

        query = self._registry.get_query("get_project_summary")
        if query is None:
            self.ctx.notify("Project details not available", severity="warning")
            return

        from hive.runtime.context import ExecutionContext  # noqa: PLC0415
        from hive.runtime.output import OutputFormat  # noqa: PLC0415

        try:
            async with ExecutionContext(
                registry=self._registry,
                output_format=OutputFormat.TABLE,
                command_name="get_project_summary",
                allow_concurrent=True,
            ) as ctx:
                summary = await query.func(ctx, project_id=project_id)

                if summary:
                    details = (
                        f"[bold]{summary.project_name}[/bold]\n"
                        f"Client: {summary.client_name}\n"
                        f"Total Hours: {summary.total_hours:.1f}h\n"
                        f"Billable: {summary.billable_hours:.1f}h\n"
                        f"Rate: ${summary.effective_rate}/hr"
                    )
                    if summary.budget_remaining is not None:
                        details += f"\nBudget Remaining: {summary.budget_remaining:.1f}h"
                    self.ctx.notify(details, title="Project Details", timeout=10.0)
                else:
                    self.ctx.notify("Project not found", severity="warning")
        except Exception as e:  # noqa: BLE001
            self.ctx.notify(f"Error loading project: {e}", severity="error")

    async def action_filter_active(self) -> None:
        """Toggle active-only filter."""
        self.ctx.notify("Filtering to active projects")
        await self.refresh_data()

    async def action_go_back(self) -> None:
        """Return to dashboard."""
        await self.ctx.go_back()


@screen(app, keybinding="t", queries=["list_time_entries"])
class TimeScreen(HiveScreen[None]):
    """Time entries list with filtering.

    Keybinding: t
    """

    DEFAULT_CSS: ClassVar[str] = """
    TimeScreen {
        layout: vertical;
    }

    TimeScreen #time-container {
        padding: 1 2;
    }

    TimeScreen .section-title {
        text-style: bold;
        margin-bottom: 1;
    }

    TimeScreen #time-table {
        height: 1fr;
    }

    TimeScreen.loading #time-container {
        opacity: 0.5;
    }

    TimeScreen.error #time-container {
        border: solid $error;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("s", "start_timer", "Start"),
        Binding("x", "stop_timer", "Stop"),
        Binding("b", "mark_billable", "Toggle Billable"),
        Binding("7", "filter_week", "This Week"),
        Binding("m", "filter_month", "This Month"),
        Binding("escape", "go_back", "Back"),
    ]

    @override
    def compose(self) -> ComposeResult:
        """Build the time entries list."""
        yield HiveHeader(show_screen_title=True)

        with Container(id="time-container"):
            yield Static("Recent Time Entries", classes="section-title")
            yield HiveDataTable[TimeEntry](id="time-table")

        yield HiveFooter()

    @override
    async def on_mount(self) -> None:
        """Set up the table."""
        await super().on_mount()
        table = self.query_one("#time-table", HiveDataTable)
        table.add_columns("Date", "Project", "Description", "Hours", "Status")

    def watch_data(self, data: list[Any]) -> None:
        """Populate table when data loads."""
        if not data:
            return

        table = self.query_one("#time-table", HiveDataTable)
        table.clear()
        for entry in data:
            status = "RUNNING" if entry.is_running else entry.status.value
            table.add_row(
                entry.started_at.strftime("%m/%d %H:%M"),
                str(entry.project_id),
                entry.description[:40] if entry.description else "",
                f"{entry.duration_hours:.2f}",
                status,
            )

    def watch_is_loading(self, loading: bool) -> None:
        """Update visual state when loading changes."""
        if loading:
            self.add_class("loading")
        else:
            self.remove_class("loading")

    def watch_error(self, error: str | None) -> None:
        """Update visual state when error changes."""
        if error:
            self.add_class("error")
            self.ctx.notify(f"Error: {error}", severity="error")
        else:
            self.remove_class("error")

    async def action_start_timer(self) -> None:
        """Start a new timer."""
        from hive.tui.widgets.modal import ParameterModal  # noqa: PLC0415

        if self._registry is None:
            self.ctx.notify("Registry not available", severity="error")
            return

        cmd = self._registry.get_command("start_timer")
        if cmd is None:
            self.ctx.notify("start_timer command not found", severity="error")
            return

        modal = ParameterModal(cmd)
        await self.app.push_screen(modal)

    async def action_stop_timer(self) -> None:
        """Stop current timer."""
        if self._registry is None:
            self.ctx.notify("Registry not available", severity="error")
            return

        cmd = self._registry.get_command("stop_timer")
        if cmd is None:
            self.ctx.notify("stop_timer command not found", severity="error")
            return

        from hive.runtime.context import ExecutionContext  # noqa: PLC0415
        from hive.runtime.output import OutputFormat  # noqa: PLC0415

        try:
            async with ExecutionContext(
                registry=self._registry,
                output_format=OutputFormat.TABLE,
                command_name="stop_timer",
                allow_concurrent=True,
            ) as ctx:
                entry = await cmd.func(ctx)

                if entry is None:
                    self.ctx.notify("No timer running", severity="warning")
                else:
                    self.ctx.notify(
                        f"Timer stopped: {entry.duration_hours:.2f}h",
                        severity="information",
                    )
            await self.refresh_data()
        except Exception as e:  # noqa: BLE001
            self.ctx.notify(f"Error stopping timer: {e}", severity="error")

    async def action_mark_billable(self) -> None:
        """Toggle billable status on selected entry."""
        table = self.query_one("#time-table", HiveDataTable)
        if table.row_count == 0:
            self.ctx.notify("No entry selected", severity="warning")
            return
        cursor_row = table.cursor_row

        row_data = table.get_row_at(cursor_row)
        if not row_data:
            return

        # For now, show info - full implementation would use mark_billable command
        self.ctx.notify(f"Entry at row {cursor_row} - use command palette to toggle billable")

    async def action_filter_week(self) -> None:
        """Filter to this week."""
        self.ctx.notify("Showing this week")
        await self.refresh_data()

    async def action_filter_month(self) -> None:
        """Filter to this month."""
        self.ctx.notify("Showing this month")
        await self.refresh_data()

    async def action_go_back(self) -> None:
        """Return to dashboard."""
        await self.ctx.go_back()


# Register all screens by importing them
__all__ = ["DashboardScreen", "ProjectsScreen", "TimeScreen"]
