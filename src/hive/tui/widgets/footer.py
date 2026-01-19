"""HiveFooter widget for TUI applications.

Displays keybinding hints and command palette trigger.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from textual.reactive import reactive
from textual.widgets import Footer

if TYPE_CHECKING:
    from hive.core.registry import ApplicationRegistry


class HiveFooter(Footer):
    """Application footer with keybinding hints.

    Extends Textual Footer to display:
    - Available keybindings from current screen
    - Global keybindings (screen navigation)
    - Command palette hint (Ctrl+P) when enabled

    Updates dynamically when the screen changes.

    CSS Classes:
        .hive-footer: Base footer styling
        .hive-footer--key: Keybinding display
        .hive-footer--hint: Command palette hint

    Attributes:
        show_command_palette_hint: Whether to show the Ctrl+P hint.
    """

    DEFAULT_CSS = """
    HiveFooter {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
    }

    HiveFooter .hive-footer--key {
        text-style: bold;
    }

    HiveFooter .hive-footer--hint {
        text-style: italic;
    }
    """

    # Track keybindings reactively for dynamic updates
    _keybindings_version: reactive[int] = reactive(0)

    def __init__(
        self,
        *,
        show_command_palette_hint: bool = True,
        registry: ApplicationRegistry | None = None,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize the footer.

        Args:
            show_command_palette_hint: Show Ctrl+P hint for command palette.
            registry: Optional application registry for screen keybindings.
            name: Optional widget name.
            id: Optional widget ID for CSS.
            classes: Optional CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._show_command_palette_hint = show_command_palette_hint
        self._registry = registry
        self.add_class("hive-footer")

    @property
    def show_command_palette_hint(self) -> bool:
        """Get whether to show the command palette hint.

        Returns:
            True if the Ctrl+P hint should be shown.
        """
        return self._show_command_palette_hint

    @override
    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        super().on_mount()
        self._refresh_keybindings()

    def on_screen_resume(self) -> None:
        """Called when the screen is resumed."""
        self._refresh_keybindings()

    def _refresh_keybindings(self) -> None:
        """Refresh the keybinding display.

        Increments the reactive version to trigger a refresh.
        """
        self._keybindings_version += 1

    def _watch__keybindings_version(self, _version: int) -> None:
        """Watch for keybinding version changes.

        Args:
            _version: The new version number.
        """
        self.refresh()

    def set_registry(self, registry: ApplicationRegistry) -> None:
        """Set the application registry.

        Args:
            registry: The application registry.
        """
        self._registry = registry
        self._refresh_keybindings()

    def get_screen_keybindings(self) -> list[tuple[str, str]]:
        """Get keybindings for the current screen.

        Returns:
            List of (key, description) tuples.
        """
        bindings: list[tuple[str, str]] = []

        if self._registry and self.app:
            screen = self.app.screen
            screen_name = screen.__class__.__name__

            # Get screen-specific keybindings from registry
            screen_reg = self._registry.get_screen(screen_name)
            if screen_reg and screen_reg.keybinding:
                bindings.append((screen_reg.keybinding, screen_reg.docstring or screen_name))

            # Add navigation keybindings for other screens
            bindings.extend(
                (other_screen.keybinding, other_screen.docstring or other_screen.name)
                for other_screen in self._registry.list_screens()
                if other_screen.name != screen_name and other_screen.keybinding
            )

        # Add command palette hint
        if self._show_command_palette_hint:
            bindings.append(("ctrl+p", "Command Palette"))

        return bindings
