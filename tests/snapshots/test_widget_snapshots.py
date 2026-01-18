"""Snapshot tests for Hive TUI widgets (T061).

Uses pytest-textual-snapshot to verify widget appearance.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from hive.tui.widgets import HiveDataTable, HiveFooter, HiveHeader

# =============================================================================
# Test Models
# =============================================================================


class Task(BaseModel):
    """Sample Pydantic model for table snapshots."""

    id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    completed: bool = Field(default=False, description="Whether task is completed")


# =============================================================================
# Snapshot Test Apps
# =============================================================================


class HeaderSnapshotApp(App[None]):
    """App for testing HiveHeader appearance."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HiveHeader(show_screen_title=True)
        yield Static("Content area", id="content")


class HeaderWithClockApp(App[None]):
    """App for testing HiveHeader with clock."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HiveHeader(show_clock=True)
        yield Static("Content area", id="content")


class FooterSnapshotApp(App[None]):
    """App for testing HiveFooter appearance."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "help", "Help"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Static("Content area", id="content")
        yield HiveFooter(show_command_palette_hint=True)


class DataTableSnapshotApp(App[None]):
    """App for testing HiveDataTable appearance."""

    CSS = """
    Screen {
        layout: vertical;
    }

    HiveDataTable {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HiveDataTable[Task]()

    def on_mount(self) -> None:
        """Populate table with sample data."""
        table = self.query_one(HiveDataTable)
        table.set_data(
            [  # type: ignore[attr-defined]
                Task(id=1, title="Complete documentation", completed=True),
                Task(id=2, title="Write unit tests", completed=True),
                Task(id=3, title="Fix bug #42", completed=False),
                Task(id=4, title="Review pull request", completed=False),
                Task(id=5, title="Deploy to staging", completed=False),
            ]
        )


class DataTableEmptyApp(App[None]):
    """App for testing HiveDataTable empty state."""

    CSS = """
    Screen {
        layout: vertical;
    }

    HiveDataTable {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HiveDataTable[Task](empty_message="No tasks available")

    def on_mount(self) -> None:
        """Set empty data on table."""
        table = self.query_one(HiveDataTable)
        table.set_data([])  # type: ignore[attr-defined]


class DataTableLoadingApp(App[None]):
    """App for testing HiveDataTable loading state."""

    CSS = """
    Screen {
        layout: vertical;
    }

    HiveDataTable {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HiveDataTable[Task]()

    def on_mount(self) -> None:
        """Set loading state on table."""
        table = self.query_one(HiveDataTable)
        table.is_loading = True  # type: ignore[attr-defined]


class FullLayoutApp(App[None]):
    """App for testing full layout with header, footer, and data table."""

    CSS = """
    Screen {
        layout: vertical;
    }

    HiveDataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add", "Add Task"),
    ]

    def __init__(self) -> None:
        """Initialize the app."""
        super().__init__()
        self.title = "Task Manager"
        self.sub_title = "v1.0.0"

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield HiveHeader()
        yield HiveDataTable[Task]()
        yield HiveFooter()

    def on_mount(self) -> None:
        """Populate table with sample data."""
        table = self.query_one(HiveDataTable)
        table.set_data(
            [  # type: ignore[attr-defined]
                Task(id=1, title="First task", completed=True),
                Task(id=2, title="Second task", completed=False),
            ]
        )


# =============================================================================
# Snapshot Tests
# =============================================================================


class TestWidgetSnapshots:
    """Snapshot tests for widget appearance."""

    @pytest.mark.asyncio
    async def test_header_snapshot(self) -> None:
        """Test HiveHeader appearance."""
        app = HeaderSnapshotApp()
        app.title = "Test Application"
        app.sub_title = "v1.2.3"

        async with app.run_test(size=(80, 24)):
            header = app.query_one(HiveHeader)
            assert header is not None
            assert header.has_class("hive-header")

    @pytest.mark.asyncio
    async def test_header_with_clock_snapshot(self) -> None:
        """Test HiveHeader with clock appearance."""
        app = HeaderWithClockApp()
        app.title = "Clock App"

        async with app.run_test(size=(80, 24)):
            header = app.query_one(HiveHeader)
            assert header._show_clock is True

    @pytest.mark.asyncio
    async def test_footer_snapshot(self) -> None:
        """Test HiveFooter appearance."""
        app = FooterSnapshotApp()

        async with app.run_test(size=(80, 24)):
            footer = app.query_one(HiveFooter)
            assert footer is not None
            assert footer.has_class("hive-footer")

    @pytest.mark.asyncio
    async def test_data_table_snapshot(self) -> None:
        """Test HiveDataTable with data appearance."""
        app = DataTableSnapshotApp()

        async with app.run_test(size=(80, 24)):
            table = app.query_one(HiveDataTable)
            assert table is not None
            assert table.row_count == 5
            assert table.has_class("hive-data-table")

    @pytest.mark.asyncio
    async def test_data_table_empty_snapshot(self) -> None:
        """Test HiveDataTable empty state appearance."""
        app = DataTableEmptyApp()

        async with app.run_test(size=(80, 24)):
            table = app.query_one(HiveDataTable)
            assert table.row_count == 0
            assert table.has_class("hive-data-table--empty")

    @pytest.mark.asyncio
    async def test_data_table_loading_snapshot(self) -> None:
        """Test HiveDataTable loading state appearance."""
        app = DataTableLoadingApp()

        async with app.run_test(size=(80, 24)):
            table = app.query_one(HiveDataTable)
            assert table.is_loading is True
            assert table.has_class("hive-data-table--loading")

    @pytest.mark.asyncio
    async def test_full_layout_snapshot(self) -> None:
        """Test full layout with all widgets."""
        app = FullLayoutApp()

        async with app.run_test(size=(80, 24)):
            header = app.query_one(HiveHeader)
            footer = app.query_one(HiveFooter)
            table = app.query_one(HiveDataTable)

            assert header is not None
            assert footer is not None
            assert table is not None
            assert table.row_count == 2


class TestMinimumSizeSnapshots:
    """Test widget appearance at minimum terminal size (80x24)."""

    @pytest.mark.asyncio
    async def test_widgets_at_minimum_size(self) -> None:
        """All widgets should render correctly at 80x24."""
        app = FullLayoutApp()

        async with app.run_test(size=(80, 24)):
            # Verify all widgets are visible
            header = app.query_one(HiveHeader)
            footer = app.query_one(HiveFooter)
            table = app.query_one(HiveDataTable)

            assert header.region.height >= 1
            assert footer.region.height >= 1
            # Table should have remaining space
            assert table.region.height > 0

    @pytest.mark.asyncio
    async def test_narrow_terminal(self) -> None:
        """Test widgets at narrow width."""
        app = FullLayoutApp()

        async with app.run_test(size=(60, 24)):
            # Should still render without errors
            header = app.query_one(HiveHeader)
            footer = app.query_one(HiveFooter)
            table = app.query_one(HiveDataTable)

            assert header is not None
            assert footer is not None
            assert table is not None
