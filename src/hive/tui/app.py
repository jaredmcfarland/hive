"""HiveApp - Generated Textual application from registry.

Provides the main TUI application class that binds screens from
the application registry.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, override

from textual import on
from textual.app import App
from textual.binding import Binding, BindingType
from textual.command import Provider
from textual.events import Resize

from hive.tui.commands import HiveCommandProvider
from hive.tui.widgets.modal import ParameterSubmitted

if TYPE_CHECKING:
    from textual.screen import Screen

    from hive.core.registry import ApplicationRegistry
    from hive.core.types import CommandRegistration
    from hive.runtime.context import ExecutionContext

# Minimum terminal size for proper widget display (SC-006)
MIN_TERMINAL_WIDTH = 80
MIN_TERMINAL_HEIGHT = 24


class HiveApp(App[None]):
    """Generated Textual application from Hive registry.

    Automatically installs screens and binds keybindings from the
    application registry. Uses Textual's built-in command palette (Ctrl+P)
    with HiveCommandProvider for command discovery.

    Attributes:
        BINDINGS: List of key bindings for navigation.
        COMMANDS: Command providers for the command palette.
        _hive_registry: The application registry.
        _default_screen: Name of the default screen.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    COMMANDS: ClassVar[set[type[Provider] | Callable[[], type[Provider]]]] = {HiveCommandProvider}

    CSS: ClassVar[str] = """
    Screen {
        layout: vertical;
    }
    """

    def __init__(
        self,
        registry: ApplicationRegistry,
        *,
        execution_context: ExecutionContext | None = None,
        title: str = "Hive Application",
        css_path: str | None = None,
        min_width: int = MIN_TERMINAL_WIDTH,
        min_height: int = MIN_TERMINAL_HEIGHT,
    ) -> None:
        """Initialize the HiveApp.

        Args:
            registry: The application registry containing screens.
            execution_context: Optional execution context for service/db access.
            title: Application title (shown in header).
            css_path: Optional path to CSS file.
            min_width: Minimum terminal width (default 80).
            min_height: Minimum terminal height (default 24).
        """
        super().__init__()
        self._hive_registry = registry
        self._execution_context = execution_context
        self.title = title
        self._default_screen: str | None = None
        self._screen_classes: dict[str, type[Screen[Any]]] = {}
        self._css_path = css_path
        self._dynamic_bindings: list[BindingType] = []
        self._min_width = min_width
        self._min_height = min_height
        self._size_warning_shown = False

        # Process registered screens
        self._setup_screens()

    def _setup_screens(self) -> None:
        """Set up screens from registry."""
        screens = self._hive_registry.list_screens()

        for screen_reg in screens:
            # Store screen class
            self._screen_classes[screen_reg.name] = screen_reg.cls

            # Track default screen
            if screen_reg.default:
                self._default_screen = screen_reg.name

            # Add keybinding if specified
            if screen_reg.keybinding:
                binding = Binding(
                    screen_reg.keybinding,
                    f"navigate_to_{screen_reg.name}",
                    screen_reg.docstring or screen_reg.name,
                )
                self._dynamic_bindings.append(binding)

        # Use first screen if no default specified
        if self._default_screen is None and screens:
            self._default_screen = screens[0].name

    @property
    def _all_bindings(self) -> list[BindingType]:
        """Get all bindings including dynamic screen bindings."""
        return [*self.BINDINGS, *self._dynamic_bindings]

    @override
    def compose(self) -> Any:
        """Compose the application layout.

        Returns:
            Empty generator - screens are pushed dynamically.
        """
        # Screens are pushed dynamically via on_mount
        # Use empty generator pattern for type checking
        if False:
            yield

    def on_mount(self) -> None:
        """Called when app is mounted. Pushes default screen."""
        # Register dynamic bindings
        for binding in self._dynamic_bindings:
            if isinstance(binding, Binding):
                self._bindings.bind(
                    binding.key,
                    binding.action,
                    binding.description,
                    priority=binding.priority,
                )

        # Check terminal size on mount
        self._check_terminal_size()

        if self._default_screen:
            self.push_screen(self._create_screen(self._default_screen))

    def on_resize(self, _event: Resize) -> None:
        """Handle terminal resize events.

        Shows a warning if the terminal is smaller than the minimum size.

        Args:
            _event: The resize event (unused, size taken from self.size).
        """
        self._check_terminal_size()

    def _check_terminal_size(self) -> None:
        """Check if terminal meets minimum size requirements.

        Shows a warning notification if the terminal is too small.
        Warning is only shown once per resize event.
        """
        width = self.size.width
        height = self.size.height

        too_small = width < self._min_width or height < self._min_height

        if too_small and not self._size_warning_shown:
            msg = (
                f"Terminal size ({width}x{height}) is smaller than recommended "
                f"({self._min_width}x{self._min_height}). "
                "Some widgets may not display correctly."
            )
            self.notify(msg, severity="warning", timeout=10)
            self._size_warning_shown = True
        elif not too_small:
            # Reset warning flag when size is adequate
            self._size_warning_shown = False

    def _create_screen(self, screen_name: str) -> Screen[Any]:
        """Create a screen instance by name.

        Args:
            screen_name: The screen name.

        Returns:
            Screen instance.

        Raises:
            KeyError: If screen not found.
        """
        # Import here to avoid circular dependency
        from hive.tui.screens import HiveScreen, ScreenContext  # noqa: PLC0415

        screen_cls = self._screen_classes[screen_name]
        screen = screen_cls()

        # Set query names and registry if HiveScreen (intentional internal access)
        if hasattr(screen, "_query_names"):
            reg = self._hive_registry.get_screen(screen_name)
            if reg and hasattr(reg, "queries"):
                screen._query_names = list(reg.queries)  # type: ignore[attr-defined]  # noqa: SLF001

            # Set registry for query execution
            if hasattr(screen, "_registry"):
                screen._registry = self._hive_registry  # type: ignore[attr-defined]  # noqa: SLF001

        # Initialize screen context if execution context is available
        # (intentional internal access - _set_context is designed to be called by HiveApp)
        if isinstance(screen, HiveScreen) and self._execution_context is not None:
            ctx = ScreenContext(self._execution_context, self, screen)
            screen._set_context(ctx)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        return screen

    def navigate_to(self, screen_name: str) -> None:
        """Navigate to a named screen.

        Args:
            screen_name: The screen to navigate to.
        """
        if screen_name in self._screen_classes:
            self.push_screen(self._create_screen(screen_name))

    def __getattr__(self, name: str) -> Any:
        """Dynamic action handler for screen keybindings.

        Args:
            name: Attribute name.

        Returns:
            Action method if pattern matches.

        Raises:
            AttributeError: If not a navigate_to action.
        """
        if name.startswith("action_navigate_to_"):
            screen_name = name[19:]  # Remove 'action_navigate_to_' prefix
            if screen_name in self._screen_classes:

                async def navigate_action() -> None:
                    self.push_screen(self._create_screen(screen_name))

                return navigate_action

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @on(ParameterSubmitted)
    async def _on_parameters_submitted(self, event: ParameterSubmitted) -> None:
        """Handle parameter submission and execute the command.

        Args:
            event: Parameter submission event.
        """
        await self._execute_command(event.command, event.parameters)

    async def _execute_command(
        self,
        command: CommandRegistration,
        parameters: dict[str, Any],
    ) -> None:
        """Execute a command with the given parameters.

        Uses the same execution path as CLI commands.

        Args:
            command: Command registration to execute.
            parameters: Dictionary of parameter values.
        """
        # Late import to avoid circular dependency at module load time
        from hive.runtime.context import ExecutionContext  # noqa: PLC0415
        from hive.runtime.output import OutputFormat  # noqa: PLC0415

        try:
            # Create execution context (same as CLI)
            async with ExecutionContext(
                registry=self._hive_registry,
                output_format=OutputFormat.TABLE,
                command_name=command.name,
            ) as ctx:
                # Execute the command function
                result = await command.func(ctx, **parameters)

                # Show success notification
                if result is not None:
                    message = str(result)
                    if len(message) > 100:  # noqa: PLR2004
                        message = message[:97] + "..."
                    self.notify(f"Success: {message}", severity="information")
                else:
                    self.notify(f"Command '{command.name}' executed", severity="information")

        except Exception as e:  # noqa: BLE001
            # Show error notification
            error_message = str(e)
            self.notify(error_message, severity="error")
