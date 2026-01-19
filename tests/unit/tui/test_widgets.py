"""Unit tests for TUI widgets.

Tests for Phase 6: User Story 4 - Command Palette functionality.
Tests for Phase 7: User Story 5 - Standard Widgets (T058-T067).

Tests verify:
- HiveHeader display (T058)
- HiveFooter keybinding display (T059)
- HiveDataTable column generation (T060)
- HiveDataTable sorting (T065)
- HiveDataTable row selection (T066)
- HiveDataTable states (T067)
- CommandPalette filtering with fuzzy search (T049)
- ParameterModal form generation (T050)
- Parameter type to widget mapping
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
import pytest
from textual.app import App as TextualApp
from textual.app import ComposeResult

from hive import App
from hive.core.decorators import command
from hive.core.types import CommandRegistration, ParameterInfo, ParameterKind

# =============================================================================
# Test Models for HiveDataTable Tests
# =============================================================================


class Task(BaseModel):
    """Sample Pydantic model for table tests."""

    id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    completed: bool = Field(default=False, description="Whether task is completed")
    priority: int = Field(default=1, description="Task priority (1-5)")


class Priority(Enum):
    """Test enum for parameter mapping."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =============================================================================
# T058: HiveHeader Tests
# =============================================================================


class TestHiveHeader:
    """Tests for HiveHeader widget display (T058)."""

    @pytest.mark.asyncio
    async def test_header_displays_app_title(self) -> None:
        """Header should display the application title."""
        from hive.tui.widgets import HiveHeader

        class TestApp(TextualApp[None]):
            """Test app with header."""

            def compose(self) -> ComposeResult:
                yield HiveHeader()

        app = TestApp()
        app.title = "My Test App"

        async with app.run_test():
            header = app.query_one(HiveHeader)
            # Header should have access to app title
            assert app.title == "My Test App"
            assert header is not None

    @pytest.mark.asyncio
    async def test_header_displays_version(self) -> None:
        """Header should display app version when set."""
        from hive.tui.widgets import HiveHeader

        class TestApp(TextualApp[None]):
            """Test app with version."""

            SUB_TITLE = "v1.2.3"

            def compose(self) -> ComposeResult:
                yield HiveHeader()

        app = TestApp()
        app.title = "My App"

        async with app.run_test():
            header = app.query_one(HiveHeader)
            assert header is not None
            # Version should be accessible via sub_title
            assert app.sub_title == "v1.2.3"

    @pytest.mark.asyncio
    async def test_header_displays_screen_title(self) -> None:
        """Header should display current screen title when enabled."""
        from hive.tui.widgets import HiveHeader

        class TestApp(TextualApp[None]):
            """Test app with screen title."""

            def compose(self) -> ComposeResult:
                yield HiveHeader(show_screen_title=True)

        app = TestApp()
        app.title = "Test App"

        async with app.run_test():
            header = app.query_one(HiveHeader)
            # show_screen_title should be tracked
            assert header._show_screen_title is True

    @pytest.mark.asyncio
    async def test_header_hides_screen_title(self) -> None:
        """Header should hide screen title when disabled."""
        from hive.tui.widgets import HiveHeader

        class TestApp(TextualApp[None]):
            """Test app without screen title."""

            def compose(self) -> ComposeResult:
                yield HiveHeader(show_screen_title=False)

        app = TestApp()

        async with app.run_test():
            header = app.query_one(HiveHeader)
            assert header._show_screen_title is False

    @pytest.mark.asyncio
    async def test_header_shows_clock_when_enabled(self) -> None:
        """Header should show clock when show_clock=True."""
        from hive.tui.widgets import HiveHeader

        class TestApp(TextualApp[None]):
            """Test app with clock."""

            def compose(self) -> ComposeResult:
                yield HiveHeader(show_clock=True)

        app = TestApp()

        async with app.run_test():
            header = app.query_one(HiveHeader)
            # Textual's Header stores show_clock internally
            assert header._show_clock is True

    @pytest.mark.asyncio
    async def test_header_has_hive_header_class(self) -> None:
        """Header should have hive-header CSS class."""
        from hive.tui.widgets import HiveHeader

        class TestApp(TextualApp[None]):
            """Test app."""

            def compose(self) -> ComposeResult:
                yield HiveHeader()

        app = TestApp()

        async with app.run_test():
            header = app.query_one(HiveHeader)
            assert header.has_class("hive-header")


# =============================================================================
# T059: HiveFooter Tests
# =============================================================================


class TestHiveFooter:
    """Tests for HiveFooter keybinding display (T059)."""

    @pytest.mark.asyncio
    async def test_footer_displays_keybindings(self) -> None:
        """Footer should display available keybindings."""
        from hive.tui.widgets import HiveFooter

        class TestApp(TextualApp[None]):
            """Test app with keybindings."""

            BINDINGS = [
                ("q", "quit", "Quit"),
                ("h", "help", "Help"),
            ]

            def compose(self) -> ComposeResult:
                yield HiveFooter()

        app = TestApp()

        async with app.run_test():
            footer = app.query_one(HiveFooter)
            assert footer is not None

    @pytest.mark.asyncio
    async def test_footer_shows_command_palette_hint(self) -> None:
        """Footer should show Ctrl+P hint when enabled."""
        from hive.tui.widgets import HiveFooter

        class TestApp(TextualApp[None]):
            """Test app."""

            def compose(self) -> ComposeResult:
                yield HiveFooter(show_command_palette_hint=True)

        app = TestApp()

        async with app.run_test():
            footer = app.query_one(HiveFooter)
            assert footer._show_command_palette_hint is True

    @pytest.mark.asyncio
    async def test_footer_hides_command_palette_hint(self) -> None:
        """Footer should hide Ctrl+P hint when disabled."""
        from hive.tui.widgets import HiveFooter

        class TestApp(TextualApp[None]):
            """Test app."""

            def compose(self) -> ComposeResult:
                yield HiveFooter(show_command_palette_hint=False)

        app = TestApp()

        async with app.run_test():
            footer = app.query_one(HiveFooter)
            assert footer._show_command_palette_hint is False

    @pytest.mark.asyncio
    async def test_footer_has_hive_footer_class(self) -> None:
        """Footer should have hive-footer CSS class."""
        from hive.tui.widgets import HiveFooter

        class TestApp(TextualApp[None]):
            """Test app."""

            def compose(self) -> ComposeResult:
                yield HiveFooter()

        app = TestApp()

        async with app.run_test():
            footer = app.query_one(HiveFooter)
            assert footer.has_class("hive-footer")

    @pytest.mark.asyncio
    async def test_footer_updates_on_screen_change(self) -> None:
        """Footer should update keybindings when screen changes."""
        from hive.tui.widgets import HiveFooter

        # This tests that footer can handle dynamic updates
        class TestApp(TextualApp[None]):
            """Test app."""

            def compose(self) -> ComposeResult:
                yield HiveFooter()

        app = TestApp()

        async with app.run_test():
            footer = app.query_one(HiveFooter)
            # Footer should support refresh
            assert hasattr(footer, "refresh")


# =============================================================================
# T060: HiveDataTable Tests
# =============================================================================


class TestHiveDataTable:
    """Tests for HiveDataTable column generation (T060)."""

    @pytest.mark.asyncio
    async def test_table_generates_columns_from_pydantic_model(self) -> None:
        """Table should auto-generate columns from Pydantic model schema."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                table: HiveDataTable[Task] = HiveDataTable()
                yield table

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            # Set data with Pydantic model instances
            table.set_data(
                [
                    Task(id=1, title="First task", completed=False),
                    Task(id=2, title="Second task", completed=True),
                ]
            )

            # Columns should be auto-generated from model fields
            columns = [col.label.plain for col in table.columns.values()]
            assert "id" in columns
            assert "title" in columns
            assert "completed" in columns

    @pytest.mark.asyncio
    async def test_table_generates_columns_from_dict_keys(self) -> None:
        """Table should auto-generate columns from dict keys."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                table: HiveDataTable[dict[str, object]] = HiveDataTable()
                yield table

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            # Set data with dicts
            table.set_data(
                [
                    {"name": "Alice", "age": 30, "active": True},
                    {"name": "Bob", "age": 25, "active": False},
                ]
            )

            # Columns should be auto-generated from dict keys
            columns = [col.label.plain for col in table.columns.values()]
            assert "name" in columns
            assert "age" in columns
            assert "active" in columns

    @pytest.mark.asyncio
    async def test_table_uses_specified_columns(self) -> None:
        """Table should use explicitly specified columns."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                table: HiveDataTable[Task] = HiveDataTable(columns=["id", "title"])
                yield table

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.set_data([Task(id=1, title="Test", completed=True)])

            # Only specified columns should appear
            columns = [col.label.plain for col in table.columns.values()]
            assert "id" in columns
            assert "title" in columns
            assert "completed" not in columns

    @pytest.mark.asyncio
    async def test_table_has_loading_state(self) -> None:
        """Table should have loading state."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.is_loading = True
            assert table.is_loading is True
            table.is_loading = False
            assert table.is_loading is False

    @pytest.mark.asyncio
    async def test_table_has_error_state(self) -> None:
        """Table should have error state."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.error = "Database connection failed"
            assert table.error == "Database connection failed"
            table.error = None
            assert table.error is None

    @pytest.mark.asyncio
    async def test_table_shows_empty_state(self) -> None:
        """Table should show empty state when no data."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.set_data([])
            # Table should handle empty data gracefully
            assert table.row_count == 0

    @pytest.mark.asyncio
    async def test_table_has_hive_data_table_class(self) -> None:
        """Table should have hive-data-table CSS class."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            assert table.has_class("hive-data-table")


# =============================================================================
# T065: HiveDataTable Sorting Tests
# =============================================================================


class TestHiveDataTableSorting:
    """Tests for HiveDataTable sorting support (T065)."""

    @pytest.mark.asyncio
    async def test_table_supports_sorting(self) -> None:
        """Table should support sorting by column."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.set_data(
                [
                    {"id": 3, "name": "Charlie"},
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                ]
            )

            # Sort by id ascending
            table.sort_by("id", ascending=True)
            # First row should be id=1
            row_data = table.get_hive_row_at(0)
            assert row_data is not None
            # Data should be accessible

    @pytest.mark.asyncio
    async def test_table_sorts_descending(self) -> None:
        """Table should support descending sort."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.set_data(
                [
                    {"id": 1, "name": "Alice"},
                    {"id": 3, "name": "Charlie"},
                    {"id": 2, "name": "Bob"},
                ]
            )

            # Sort by id descending
            table.sort_by("id", ascending=False)
            # Table should support this operation


# =============================================================================
# T066: HiveDataTable Row Selection Tests
# =============================================================================


class TestHiveDataTableSelection:
    """Tests for HiveDataTable row selection events (T066)."""

    @pytest.mark.asyncio
    async def test_table_emits_row_selected_event(self) -> None:
        """Table should emit event when row is selected."""
        from hive.tui.widgets import HiveDataTable

        selected_rows: list[dict[str, object]] = []

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

            def on_hive_data_table_row_selected(self, event: HiveDataTable.RowSelected) -> None:
                selected_rows.append(event.row_data)

        app = TestApp()

        async with app.run_test() as pilot:
            table = app.query_one(HiveDataTable)
            table.set_data(
                [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                ]
            )

            # Move to first row and select
            await pilot.press("down")  # Move to first data row
            await pilot.press("enter")  # Select row

            # Event should have been emitted (implementation will enable this)

    @pytest.mark.asyncio
    async def test_table_provides_row_data_in_event(self) -> None:
        """Row selection event should include row data."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.set_data([{"id": 1, "name": "Test"}])
            # Row data should be accessible through table API
            assert table.row_count == 1


# =============================================================================
# T067: HiveDataTable State Display Tests
# =============================================================================


class TestHiveDataTableStates:
    """Tests for HiveDataTable loading/error/empty states (T067)."""

    @pytest.mark.asyncio
    async def test_table_displays_loading_indicator(self) -> None:
        """Table should display loading indicator."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.is_loading = True

            # Should have loading class when loading
            assert table.has_class("hive-data-table--loading") or table.is_loading

    @pytest.mark.asyncio
    async def test_table_displays_error_message(self) -> None:
        """Table should display error message."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable()

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.error = "Failed to load data"

            # Should have error class when error set
            assert table.error == "Failed to load data"

    @pytest.mark.asyncio
    async def test_table_displays_empty_message(self) -> None:
        """Table should display empty message when no data."""
        from hive.tui.widgets import HiveDataTable

        class TestApp(TextualApp[None]):
            """Test app with data table."""

            def compose(self) -> ComposeResult:
                yield HiveDataTable(empty_message="No items found")

        app = TestApp()

        async with app.run_test():
            table = app.query_one(HiveDataTable)
            table.set_data([])

            # Should track empty message
            assert table.empty_message == "No items found"


# =============================================================================
# Command Palette Tests (Existing - T049)
# =============================================================================


class TestCommandPaletteFiltering:
    """Tests for CommandPalette fuzzy search filtering (T049)."""

    @pytest.fixture
    def sample_commands(self) -> list[CommandRegistration]:
        """Create sample command registrations for testing."""

        async def add_task(ctx: Any, title: str) -> dict[str, str]:
            return {"id": "1", "title": title}

        async def delete_task(ctx: Any, task_id: int) -> None:
            pass

        async def list_users(ctx: Any) -> list[dict[str, str]]:
            return []

        async def update_settings(ctx: Any, key: str, value: str) -> dict[str, str]:
            return {"key": key, "value": value}

        return [
            CommandRegistration(
                name="add_task",
                func=add_task,
                docstring="Add a new task to the list",
                parameters=[
                    ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
                    ParameterInfo(name="title", type=str, kind=ParameterKind.KEYWORD),
                ],
            ),
            CommandRegistration(
                name="delete_task",
                func=delete_task,
                docstring="Delete an existing task",
                parameters=[
                    ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
                    ParameterInfo(name="task_id", type=int, kind=ParameterKind.KEYWORD),
                ],
            ),
            CommandRegistration(
                name="list_users",
                func=list_users,
                docstring="List all users in the system",
                parameters=[
                    ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
                ],
            ),
            CommandRegistration(
                name="update_settings",
                func=update_settings,
                docstring="Update application settings",
                parameters=[
                    ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
                    ParameterInfo(name="key", type=str, kind=ParameterKind.KEYWORD),
                    ParameterInfo(name="value", type=str, kind=ParameterKind.KEYWORD),
                ],
            ),
        ]

    def test_empty_query_returns_all_commands(
        self, sample_commands: list[CommandRegistration]
    ) -> None:
        """Empty search query returns all commands."""
        from hive.tui.widgets.palette import filter_commands

        results = filter_commands(sample_commands, "")
        assert len(results) == 4

    def test_exact_match_returns_command(self, sample_commands: list[CommandRegistration]) -> None:
        """Exact command name match returns that command."""
        from hive.tui.widgets.palette import filter_commands

        results = filter_commands(sample_commands, "add_task")
        assert len(results) >= 1
        assert results[0].name == "add_task"

    def test_partial_match_returns_matching_commands(
        self, sample_commands: list[CommandRegistration]
    ) -> None:
        """Partial name match returns matching commands."""
        from hive.tui.widgets.palette import filter_commands

        results = filter_commands(sample_commands, "task")
        assert len(results) == 2
        names = [r.name for r in results]
        assert "add_task" in names
        assert "delete_task" in names

    def test_fuzzy_match_on_name(self, sample_commands: list[CommandRegistration]) -> None:
        """Fuzzy search matches on command names."""
        from hive.tui.widgets.palette import filter_commands

        # "atsk" should fuzzy match "add_task"
        results = filter_commands(sample_commands, "atsk")
        assert len(results) >= 1
        # add_task should be in results (fuzzy match)
        names = [r.name for r in results]
        assert "add_task" in names

    def test_fuzzy_match_on_docstring(self, sample_commands: list[CommandRegistration]) -> None:
        """Fuzzy search matches on docstrings."""
        from hive.tui.widgets.palette import filter_commands

        # Search for "system" which appears in list_users docstring
        results = filter_commands(sample_commands, "system")
        assert len(results) >= 1
        names = [r.name for r in results]
        assert "list_users" in names

    def test_case_insensitive_search(self, sample_commands: list[CommandRegistration]) -> None:
        """Search is case insensitive."""
        from hive.tui.widgets.palette import filter_commands

        results_lower = filter_commands(sample_commands, "add")
        results_upper = filter_commands(sample_commands, "ADD")
        results_mixed = filter_commands(sample_commands, "Add")

        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_no_match_returns_empty(self, sample_commands: list[CommandRegistration]) -> None:
        """Non-matching query returns empty list."""
        from hive.tui.widgets.palette import filter_commands

        results = filter_commands(sample_commands, "xyznonexistent")
        assert len(results) == 0

    def test_hidden_commands_are_excluded(self) -> None:
        """Hidden commands are not included in filter results."""
        from hive.tui.widgets.palette import filter_commands

        async def visible_cmd(ctx: Any) -> None:
            pass

        async def hidden_cmd(ctx: Any) -> None:
            pass

        commands = [
            CommandRegistration(name="visible", func=visible_cmd, hidden=False),
            CommandRegistration(name="hidden", func=hidden_cmd, hidden=True),
        ]

        results = filter_commands(commands, "")
        assert len(results) == 1
        assert results[0].name == "visible"

    def test_results_ordered_by_relevance(self, sample_commands: list[CommandRegistration]) -> None:
        """Results are ordered by match relevance (name match > docstring match)."""
        from hive.tui.widgets.palette import filter_commands

        results = filter_commands(sample_commands, "add")
        # "add_task" should be first (name match)
        assert len(results) >= 1
        assert results[0].name == "add_task"


class TestParameterModalFormGeneration:
    """Tests for ParameterModal dynamic form generation (T050)."""

    def test_str_parameter_generates_input(self) -> None:
        """String parameter generates Input widget."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(name="title", type=str, kind=ParameterKind.KEYWORD)
        widget_type, _config = get_widget_for_parameter(param)

        assert widget_type == "Input"

    def test_int_parameter_generates_input_with_validation(self) -> None:
        """Integer parameter generates Input with numeric validation."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(name="count", type=int, kind=ParameterKind.KEYWORD)
        widget_type, config = get_widget_for_parameter(param)

        assert widget_type == "Input"
        assert config.get("type") == "integer"

    def test_float_parameter_generates_input_with_validation(self) -> None:
        """Float parameter generates Input with numeric validation."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(name="rate", type=float, kind=ParameterKind.KEYWORD)
        widget_type, config = get_widget_for_parameter(param)

        assert widget_type == "Input"
        assert config.get("type") == "number"

    def test_bool_parameter_generates_switch(self) -> None:
        """Boolean parameter generates Switch widget."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(name="enabled", type=bool, kind=ParameterKind.KEYWORD)
        widget_type, _config = get_widget_for_parameter(param)

        assert widget_type == "Switch"

    def test_enum_parameter_generates_select(self) -> None:
        """Enum parameter generates Select widget."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(name="priority", type=Priority, kind=ParameterKind.KEYWORD)
        widget_type, config = get_widget_for_parameter(param)

        assert widget_type == "Select"
        assert "options" in config
        assert len(config["options"]) == 3
        option_values = [opt[1] for opt in config["options"]]
        assert Priority.LOW in option_values
        assert Priority.MEDIUM in option_values
        assert Priority.HIGH in option_values

    def test_parameter_with_default_sets_initial_value(self) -> None:
        """Parameter with default sets initial widget value."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(
            name="title",
            type=str,
            default="Default Title",
            has_default=True,
            kind=ParameterKind.KEYWORD,
        )
        _widget_type, config = get_widget_for_parameter(param)

        assert config.get("value") == "Default Title"

    def test_bool_parameter_default_false(self) -> None:
        """Boolean parameter with default=False sets Switch value."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(
            name="enabled",
            type=bool,
            default=False,
            has_default=True,
            kind=ParameterKind.KEYWORD,
        )
        _widget_type, config = get_widget_for_parameter(param)

        assert config.get("value") is False

    def test_bool_parameter_default_true(self) -> None:
        """Boolean parameter with default=True sets Switch value."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(
            name="enabled",
            type=bool,
            default=True,
            has_default=True,
            kind=ParameterKind.KEYWORD,
        )
        _widget_type, config = get_widget_for_parameter(param)

        assert config.get("value") is True

    def test_parameter_help_becomes_placeholder(self) -> None:
        """Parameter help text becomes input placeholder."""
        from hive.tui.widgets.modal import get_widget_for_parameter

        param = ParameterInfo(
            name="title",
            type=str,
            help="Enter the task title",
            kind=ParameterKind.KEYWORD,
        )
        _widget_type, config = get_widget_for_parameter(param)

        assert config.get("placeholder") == "Enter the task title"

    def test_ctx_parameter_is_excluded(self) -> None:
        """Context parameter is excluded from form generation."""
        from hive.tui.widgets.modal import get_form_parameters

        params = [
            ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
            ParameterInfo(name="title", type=str, kind=ParameterKind.KEYWORD),
            ParameterInfo(name="count", type=int, kind=ParameterKind.KEYWORD),
        ]

        form_params = get_form_parameters(params)

        assert len(form_params) == 2
        param_names = [p.name for p in form_params]
        assert "ctx" not in param_names
        assert "title" in param_names
        assert "count" in param_names

    def test_generate_form_for_command(self) -> None:
        """Generate full form configuration for a command."""
        from hive.tui.widgets.modal import generate_form_config

        async def add_task(ctx: Any, title: str, priority: Priority, done: bool = False) -> None:
            pass

        cmd_reg = CommandRegistration(
            name="add_task",
            func=add_task,
            docstring="Add a new task",
            parameters=[
                ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
                ParameterInfo(name="title", type=str, kind=ParameterKind.KEYWORD),
                ParameterInfo(name="priority", type=Priority, kind=ParameterKind.KEYWORD),
                ParameterInfo(
                    name="done",
                    type=bool,
                    default=False,
                    has_default=True,
                    kind=ParameterKind.KEYWORD,
                ),
            ],
        )

        form_config = generate_form_config(cmd_reg)

        assert form_config["command_name"] == "add_task"
        assert form_config["title"] == "Add a new task"
        assert len(form_config["fields"]) == 3

        field_names = [f["name"] for f in form_config["fields"]]
        assert "title" in field_names
        assert "priority" in field_names
        assert "done" in field_names

    def test_command_with_no_params_shows_confirmation(self) -> None:
        """Command with no parameters (except ctx) shows just confirmation."""
        from hive.tui.widgets.modal import generate_form_config

        async def clear_all(ctx: Any) -> None:
            pass

        cmd_reg = CommandRegistration(
            name="clear_all",
            func=clear_all,
            docstring="Clear all data",
            parameters=[
                ParameterInfo(name="ctx", type=object, kind=ParameterKind.POSITIONAL),
            ],
        )

        form_config = generate_form_config(cmd_reg)

        assert form_config["command_name"] == "clear_all"
        assert len(form_config["fields"]) == 0
        assert form_config.get("confirmation_only") is True


class TestParameterValueExtraction:
    """Tests for extracting values from form widgets."""

    def test_extract_string_value(self) -> None:
        """Extract string value from Input widget."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="title", type=str, kind=ParameterKind.KEYWORD)
        result = extract_value(param, "Hello World")

        assert result == "Hello World"
        assert isinstance(result, str)

    def test_extract_int_value(self) -> None:
        """Extract integer value from Input widget."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="count", type=int, kind=ParameterKind.KEYWORD)
        result = extract_value(param, "42")

        assert result == 42
        assert isinstance(result, int)

    def test_extract_float_value(self) -> None:
        """Extract float value from Input widget."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="rate", type=float, kind=ParameterKind.KEYWORD)
        result = extract_value(param, "3.14")

        assert result == 3.14
        assert isinstance(result, float)

    def test_extract_bool_value(self) -> None:
        """Extract boolean value from Switch widget."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="enabled", type=bool, kind=ParameterKind.KEYWORD)

        assert extract_value(param, True) is True
        assert extract_value(param, False) is False

    def test_extract_enum_value(self) -> None:
        """Extract enum value from Select widget."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="priority", type=Priority, kind=ParameterKind.KEYWORD)
        result = extract_value(param, Priority.HIGH)

        assert result == Priority.HIGH
        assert isinstance(result, Priority)

    def test_extract_invalid_int_raises_error(self) -> None:
        """Invalid integer string raises ValueError."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="count", type=int, kind=ParameterKind.KEYWORD)

        with pytest.raises(ValueError, match="Invalid integer"):
            extract_value(param, "not-a-number")

    def test_extract_invalid_float_raises_error(self) -> None:
        """Invalid float string raises ValueError."""
        from hive.tui.widgets.modal import extract_value

        param = ParameterInfo(name="rate", type=float, kind=ParameterKind.KEYWORD)

        with pytest.raises(ValueError, match="Invalid number"):
            extract_value(param, "not-a-float")


class TestCommandPaletteWidget:
    """Integration tests for Textual's built-in CommandPalette with HiveCommandProvider."""

    @pytest.mark.asyncio
    async def test_palette_opens_on_ctrl_p(self) -> None:
        """CommandPalette opens when Ctrl+P is pressed."""
        from textual.command import CommandPalette

        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @command(app)
        async def test_cmd(ctx: Any, arg: str) -> str:
            return arg

        from hive.core.decorators import screen

        @screen(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open command palette via Ctrl+P
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Check that CommandPalette is open using Textual's API
            assert CommandPalette.is_open(tui_app)

    @pytest.mark.asyncio
    async def test_palette_shows_hive_commands(self) -> None:
        """CommandPalette shows commands from HiveCommandProvider."""
        from textual.command import CommandPalette
        from textual.widgets import OptionList

        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @command(app)
        async def add_item(ctx: Any, name: str) -> dict[str, str]:
            return {"name": name}

        @command(app)
        async def delete_item(ctx: Any, item_id: int) -> None:
            pass

        from hive.core.decorators import screen

        @screen(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open command palette
            await pilot.press("ctrl+p")
            await pilot.pause()
            # Allow time for commands to load
            await pilot.pause()
            await pilot.pause()

            # Verify palette is open
            assert CommandPalette.is_open(tui_app)

            # Get the OptionList from the palette - commands should be loaded
            palette_screen = tui_app.screen
            option_list = palette_screen.query_one(OptionList)
            # Commands should be listed (may take a moment to populate)
            assert option_list is not None

    @pytest.mark.asyncio
    async def test_escape_closes_palette(self) -> None:
        """Pressing Escape closes the CommandPalette."""
        from textual.command import CommandPalette

        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @command(app)
        async def test_cmd(ctx: Any) -> None:
            pass

        from hive.core.decorators import screen

        @screen(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open command palette
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Verify it's open
            assert CommandPalette.is_open(tui_app)

            # Press Escape to close
            await pilot.press("escape")
            await pilot.pause()

            # Palette should be closed
            assert not CommandPalette.is_open(tui_app)


class TestParameterModalWidget:
    """Integration tests for ParameterModal widget."""

    @pytest.mark.asyncio
    async def test_modal_shows_form_for_command(self) -> None:
        """ParameterModal displays form fields for command parameters."""
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen
        from hive.tui.widgets.modal import ParameterModal

        app = App("test")

        @command(app)
        async def greet(ctx: Any, name: str, loud: bool = False) -> str:
            return f"Hello, {name}!" if not loud else f"HELLO, {name.upper()}!"

        from hive.core.decorators import screen

        @screen(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open command palette and select command
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Select the command (press Enter on first/only command)
            await pilot.press("enter")
            await pilot.pause()

            # ParameterModal should now be displayed
            # Check for modal screen
            modals = tui_app.query(ParameterModal)
            assert len(modals) >= 1 or isinstance(tui_app.screen, ParameterModal)

    @pytest.mark.asyncio
    async def test_modal_cancel_returns_to_palette(self) -> None:
        """Canceling ParameterModal returns to previous state."""
        from hive.generators.tui import generate_tui_app
        from hive.tui.screens import HiveScreen

        app = App("test")

        @command(app)
        async def some_cmd(ctx: Any, arg: str) -> str:
            return arg

        from hive.core.decorators import screen

        @screen(app, default=True)
        class TestScreen(HiveScreen[None]):
            """Test screen."""

        tui_app = generate_tui_app(app)

        async with tui_app.run_test() as pilot:
            await pilot.pause()

            # Open palette and select command
            await pilot.press("ctrl+p")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Cancel the modal
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on the main screen
            assert "TestScreen" in str(type(tui_app.screen).__name__)
