"""CommandPalette widget for Hive TUI applications.

Provides a searchable command palette that opens via Ctrl+P,
allowing users to fuzzy-search and execute registered commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Vertical
from textual.message import Message
from textual.widgets import Input, ListItem, ListView, Static

if TYPE_CHECKING:
    from hive.core.registry import ApplicationRegistry
    from hive.core.types import CommandRegistration


def filter_commands(
    commands: list[CommandRegistration],
    query: str,
) -> list[CommandRegistration]:
    """Filter commands using fuzzy search.

    Performs case-insensitive fuzzy matching on command names and docstrings.
    Hidden commands are excluded from results.

    Args:
        commands: List of command registrations to filter.
        query: Search query string.

    Returns:
        Filtered and sorted list of matching commands.
    """
    # Exclude hidden commands
    visible_commands = [cmd for cmd in commands if not cmd.hidden]

    if not query:
        return visible_commands

    query_lower = query.lower()
    scored_results: list[tuple[CommandRegistration, int]] = []

    for cmd in visible_commands:
        score = _calculate_match_score(cmd, query_lower)
        if score > 0:
            scored_results.append((cmd, score))

    # Sort by score descending (higher is better)
    scored_results.sort(key=lambda x: x[1], reverse=True)

    return [cmd for cmd, _score in scored_results]


def _calculate_match_score(cmd: CommandRegistration, query_lower: str) -> int:
    """Calculate match score for a command against a query.

    Higher scores indicate better matches.

    Args:
        cmd: Command registration to score.
        query_lower: Lowercase query string.

    Returns:
        Match score (0 = no match, higher = better match).
    """
    name_lower = cmd.name.lower()
    docstring_lower = (cmd.docstring or "").lower()

    score = 0

    # Exact name match (highest priority)
    if name_lower == query_lower:
        score += 1000

    # Name starts with query
    elif name_lower.startswith(query_lower):
        score += 500

    # Name contains query as substring
    elif query_lower in name_lower:
        score += 300

    # Fuzzy match on name
    elif _fuzzy_match(name_lower, query_lower):
        score += 100

    # Docstring contains query
    if query_lower in docstring_lower:
        score += 50

    # Fuzzy match on docstring
    elif _fuzzy_match(docstring_lower, query_lower):
        score += 25

    return score


def _fuzzy_match(text: str, pattern: str) -> bool:
    """Check if pattern characters appear in order within text.

    Args:
        text: Text to search within.
        pattern: Pattern to match (characters in order).

    Returns:
        True if all pattern characters appear in order in text.
    """
    if not pattern:
        return True

    pattern_idx = 0
    for char in text:
        if char == pattern[pattern_idx]:
            pattern_idx += 1
            if pattern_idx == len(pattern):
                return True

    return False


class CommandSelected(Message):
    """Message posted when a command is selected from the palette.

    Attributes:
        command: The selected command registration.
    """

    def __init__(self, command: CommandRegistration) -> None:
        """Initialize the message.

        Args:
            command: The selected command registration.
        """
        super().__init__()
        self.command = command


class CommandPaletteClosed(Message):
    """Message posted when the command palette is closed."""


class CommandPalette(Container, can_focus=True):
    """Command palette widget for searching and executing commands.

    Opens via Ctrl+P, allows fuzzy searching of registered commands,
    and posts a CommandSelected message when a command is chosen.

    Attributes:
        BINDINGS: Key bindings for palette navigation.
        DEFAULT_CSS: Default styling for the palette.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close_palette", "Close", show=False, priority=True),
        Binding("enter", "select_command", "Select", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]

    DEFAULT_CSS: ClassVar[str] = """
    CommandPalette {
        dock: top;
        width: 100%;
        max-height: 50%;
        background: $surface;
        border: tall $primary;
        padding: 0 1;
        display: none;
    }

    CommandPalette.visible {
        display: block;
    }

    CommandPalette > #palette-search {
        dock: top;
        width: 100%;
        margin-bottom: 1;
    }

    CommandPalette > #palette-list {
        height: auto;
        max-height: 100%;
    }

    CommandPalette > #palette-list > ListItem {
        padding: 0 1;
    }

    CommandPalette > #palette-list > ListItem.--highlight {
        background: $accent;
    }

    CommandPalette .command-name {
        text-style: bold;
    }

    CommandPalette .command-doc {
        color: $text-muted;
    }
    """

    def __init__(
        self,
        registry: ApplicationRegistry | None = None,
        *,
        name: str | None = None,
        widget_id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the CommandPalette.

        Args:
            registry: Application registry containing commands.
            name: Widget name.
            widget_id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=widget_id, classes=classes)
        self._registry = registry
        self._commands: list[CommandRegistration] = []
        self._filtered_commands: list[CommandRegistration] = []
        self._search_input: Input | None = None
        self._command_list: ListView | None = None

    @override
    def compose(self) -> ComposeResult:
        """Compose the palette layout.

        Returns:
            Widget composition.
        """
        yield Input(
            placeholder="Search commands...",
            id="palette-search",
        )
        yield ListView(id="palette-list")

    async def on_mount(self) -> None:
        """Handle mount event to initialize widgets."""
        self._search_input = self.query_one("#palette-search", Input)
        self._command_list = self.query_one("#palette-list", ListView)

        # Load commands if registry is set
        if self._registry:
            await self._load_commands()

    async def set_registry(self, registry: ApplicationRegistry) -> None:
        """Set the application registry and load commands.

        Args:
            registry: Application registry containing commands.
        """
        self._registry = registry
        await self._load_commands()

    async def _load_commands(self) -> None:
        """Load commands from registry and update display."""
        if self._registry is None:
            return

        self._commands = self._registry.list_commands()
        self._filtered_commands = filter_commands(self._commands, "")
        await self._update_list()

    async def _update_list(self) -> None:
        """Update the command list display."""
        if self._command_list is None:
            return

        # Remove all existing items first
        await self._command_list.clear()

        for idx, cmd in enumerate(self._filtered_commands):
            item = self._create_list_item(cmd, idx)
            self._command_list.append(item)

        # Select first item if available
        if self._filtered_commands:
            self._command_list.index = 0

    def _create_list_item(self, cmd: CommandRegistration, index: int) -> ListItem:
        """Create a list item for a command.

        Args:
            cmd: Command registration.
            index: Position in the filtered list (for unique ID).

        Returns:
            ListItem widget for the command.
        """
        content = Vertical(
            Static(cmd.name, classes="command-name"),
            Static(cmd.docstring or "", classes="command-doc"),
            classes="command-item",
        )
        # Use index for unique ID, store command name as data attribute
        item = ListItem(content, id=f"palette-item-{index}")
        item.set_class(True, f"cmd-{cmd.name.replace('_', '-')}")
        return item

    @on(Input.Changed, "#palette-search")
    async def _on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes.

        Args:
            event: Input changed event.
        """
        query = event.value
        self._filtered_commands = filter_commands(self._commands, query)
        await self._update_list()

    def action_close_palette(self) -> None:
        """Close the command palette."""
        self.display = False
        self.remove_class("visible")
        self.post_message(CommandPaletteClosed())

    def action_select_command(self) -> None:
        """Select the currently highlighted command."""
        if self._command_list is None:
            return

        index = self._command_list.index
        if index is not None and 0 <= index < len(self._filtered_commands):
            selected_cmd = self._filtered_commands[index]
            self.post_message(CommandSelected(selected_cmd))
            self.action_close_palette()

    def action_cursor_up(self) -> None:
        """Move cursor up in the command list."""
        if self._command_list:
            self._command_list.action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down in the command list."""
        if self._command_list:
            self._command_list.action_cursor_down()

    def on_key(self, event: events.Key) -> None:
        """Handle key events for escape and enter.

        Args:
            event: Key event.
        """
        if event.key == "escape":
            self.action_close_palette()
            event.stop()
        elif event.key == "enter":
            self.action_select_command()
            event.stop()
        elif event.key == "up":
            self.action_cursor_up()
            event.stop()
        elif event.key == "down":
            self.action_cursor_down()
            event.stop()

    @on(ListView.Selected)
    def _on_list_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection via click.

        Args:
            event: List selection event.
        """
        # Extract index from item id (format: palette-item-{index})
        item_id = event.item.id
        if item_id and item_id.startswith("palette-item-"):
            try:
                index = int(item_id[13:])  # Remove "palette-item-" prefix
                if 0 <= index < len(self._filtered_commands):
                    selected_cmd = self._filtered_commands[index]
                    self.post_message(CommandSelected(selected_cmd))
                    self.action_close_palette()
            except ValueError:
                pass  # Invalid index format, ignore

    async def open(self) -> None:
        """Open the command palette and focus search input."""
        self.display = True
        self.add_class("visible")

        # Clear previous search
        if self._search_input:
            self._search_input.value = ""
            self._search_input.focus()

        # Reset filter to show all commands
        self._filtered_commands = filter_commands(self._commands, "")
        await self._update_list()

    @property
    def visible_command_count(self) -> int:
        """Get the number of currently visible (filtered) commands.

        Returns:
            Number of commands in the filtered list.
        """
        return len(self._filtered_commands)
