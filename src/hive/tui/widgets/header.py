"""HiveHeader widget for TUI applications.

Displays application title, version, and current screen title.
"""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Header


class HiveHeader(Header):
    """Application header with title and navigation.

    Extends Textual Header to display:
    - Application name (from app.title)
    - Application version (from app.sub_title)
    - Current screen title (if enabled)

    CSS Classes:
        .hive-header: Base header styling
        .hive-header--title: App title area
        .hive-header--screen: Screen title area
        .hive-header--clock: Clock area (if enabled)

    Attributes:
        screen_title: The current screen's title to display.
    """

    DEFAULT_CSS = """
    HiveHeader {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
    }

    HiveHeader .hive-header--title {
        text-style: bold;
    }

    HiveHeader .hive-header--screen {
        text-style: italic;
    }
    """

    # Track the current screen title reactively (use _hive_screen_title to avoid conflict)
    _hive_screen_title: reactive[str] = reactive("")

    def __init__(
        self,
        *,
        show_clock: bool = False,
        show_screen_title: bool = True,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize the header.

        Args:
            show_clock: Whether to show clock in header.
            show_screen_title: Whether to show current screen title.
            name: Optional widget name.
            id: Optional widget ID for CSS.
            classes: Optional CSS classes.
        """
        super().__init__(show_clock=show_clock, name=name, id=id, classes=classes)
        self._show_screen_title = show_screen_title
        self._show_clock = show_clock
        self.add_class("hive-header")

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Subscribe to screen changes
        self._update_hive_screen_title()

    def on_screen_resume(self) -> None:
        """Called when the screen is resumed."""
        self._update_hive_screen_title()

    def _update_hive_screen_title(self) -> None:
        """Update the screen title from the current screen."""
        if self._show_screen_title and self.app:
            screen = self.app.screen
            # Get screen title from TITLE class var or name
            if hasattr(screen, "TITLE") and screen.TITLE:
                self._hive_screen_title = screen.TITLE
            elif hasattr(screen, "name") and screen.name:
                self._hive_screen_title = screen.name
            elif hasattr(screen, "__class__"):
                self._hive_screen_title = screen.__class__.__name__
            else:
                self._hive_screen_title = ""

    def _watch__hive_screen_title(self, _title: str) -> None:
        """Watch for screen title changes.

        Args:
            _title: The new screen title.
        """
        self.refresh()

    @property
    def full_title(self) -> str:
        """Get the full header title.

        Returns:
            The formatted title including app name, version, and screen.
        """
        parts: list[str] = []

        # App title
        if self.app:
            if self.app.title:
                parts.append(self.app.title)
            # Add version (sub_title) if set
            if self.app.sub_title:
                parts.append(self.app.sub_title)

        # Screen title
        if self._show_screen_title and self._hive_screen_title:
            if parts:
                parts.append("|")
            parts.append(self._hive_screen_title)

        return " ".join(parts)
