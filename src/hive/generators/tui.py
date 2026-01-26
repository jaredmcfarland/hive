"""TUI application generator.

Generates a Textual TUI application from the Hive application registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hive.errors import ConfigurationError
from hive.tui.app import HiveApp

if TYPE_CHECKING:
    from hive.app import App
    from hive.core.types import ScreenRegistration
    from hive.runtime.context import ExecutionContext


def generate_tui_app(
    app: App,
    *,
    execution_context: ExecutionContext | None = None,
    css_path: str | None = None,
) -> HiveApp:
    """Generate a Textual TUI application from a Hive app.

    Creates a HiveApp instance that binds all registered screens
    with their keybindings.

    Args:
        app: The Hive application with registered screens.
        execution_context: Optional execution context for database/service access.
        css_path: Optional path to custom CSS file.

    Returns:
        A configured HiveApp ready to run.

    Raises:
        ConfigurationError: If no screens are registered.

    Example:
        from hive import App
        from hive.core.decorators import screen
        from hive.generators.tui import generate_tui_app

        app = App("myapp")

        @screen(app, default=True, keybinding="d")
        class DashboardScreen(HiveScreen):
            ...

        tui_app = generate_tui_app(app)
        tui_app.run()
    """
    screens = app.registry.list_screens()

    if not screens:
        raise ConfigurationError("No screens registered. Add at least one @screen decorator.")

    # Validate all query references (T037)
    _validate_query_references(app, screens)

    return HiveApp(
        registry=app.registry,
        execution_context=execution_context,
        title=app.name,
        css_path=css_path,
    )


def _validate_query_references(app: App, screens: list[ScreenRegistration]) -> None:
    """Validate that all query references in screens exist.

    Args:
        app: The Hive application.
        screens: List of screen registrations.

    Raises:
        ConfigurationError: If a referenced query does not exist.
    """
    for screen_reg in screens:
        for query_name in screen_reg.queries:
            if app.registry.get_query(query_name) is None:
                msg = (
                    f"Query '{query_name}' not found in registry. "
                    f"Screen '{screen_reg.name}' references a non-existent query."
                )
                raise ConfigurationError(msg)
