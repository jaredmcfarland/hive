"""ParameterModal widget for Hive TUI applications.

Provides a modal dialog for inputting command parameters with
dynamically generated form fields based on parameter types.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, get_args, get_origin, override

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, Switch

if TYPE_CHECKING:
    from hive.core.types import CommandRegistration, ParameterInfo


def get_form_parameters(parameters: list[ParameterInfo]) -> list[ParameterInfo]:
    """Get parameters that should be included in the form.

    Filters out the context parameter which is injected automatically.

    Args:
        parameters: All command parameters.

    Returns:
        Parameters to display in the form (excluding ctx).
    """
    return [p for p in parameters if p.name != "ctx"]


def _get_base_type(param_type: type[Any] | Any) -> type[Any]:
    """Extract the base type from potentially Annotated types.

    Handles types like PositiveInt (Annotated[int, ...]) by extracting
    the underlying int type.

    Args:
        param_type: The parameter type, possibly Annotated.

    Returns:
        The base type (e.g., int, str, float, bool).
    """
    origin = get_origin(param_type)

    # Handle Annotated types (e.g., Annotated[int, Is[...]])
    if origin is Annotated:
        args = get_args(param_type)
        if args:
            return _get_base_type(args[0])  # Recurse in case of nested Annotated

    # Handle other generic types (e.g., list[int] -> list)
    if origin is not None:
        return origin

    # Already a base type
    return param_type


def get_widget_for_parameter(
    param: ParameterInfo,
) -> tuple[str, dict[str, Any]]:
    """Determine the widget type and configuration for a parameter.

    Maps parameter types to appropriate Textual widgets:
    - str -> Input
    - int -> Input with integer validation
    - float -> Input with number validation
    - bool -> Switch
    - Enum -> Select with options

    Args:
        param: Parameter information.

    Returns:
        Tuple of (widget_type, config_dict).
    """
    config: dict[str, Any] = {}

    # Get the base type (handles Annotated types like PositiveInt)
    base_type = _get_base_type(param.type)

    # Set default/initial value if present
    if param.has_default and param.default is not None:
        config["value"] = param.default
    elif param.has_default and base_type is bool:
        config["value"] = param.default  # Allow False as explicit default

    # Set placeholder from help text
    if param.help:
        config["placeholder"] = param.help

    if base_type is bool:
        return ("Switch", config)

    # Check for Enum types (isinstance needed for runtime type safety)
    if isinstance(base_type, type) and issubclass(base_type, Enum):  # pyright: ignore[reportUnnecessaryIsInstance]
        # Generate options from enum members
        options = [(member.name, member) for member in base_type]
        config["options"] = options
        return ("Select", config)

    if base_type is int:
        config["type"] = "integer"
        return ("Input", config)

    if base_type is float:
        config["type"] = "number"
        return ("Input", config)

    # Default to string input
    return ("Input", config)


def _get_docstring_summary(docstring: str | None) -> str | None:
    """Extract the first line/summary from a docstring.

    Args:
        docstring: Full docstring text.

    Returns:
        First non-empty line of the docstring, or None.
    """
    if not docstring:
        return None
    # Get first non-empty line (the summary)
    for line in docstring.strip().split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def generate_form_config(cmd_reg: CommandRegistration) -> dict[str, Any]:
    """Generate form configuration for a command.

    Args:
        cmd_reg: Command registration.

    Returns:
        Form configuration dictionary.
    """
    form_params = get_form_parameters(cmd_reg.parameters)

    fields: list[dict[str, Any]] = []
    for param in form_params:
        widget_type, widget_config = get_widget_for_parameter(param)
        fields.append(
            {
                "name": param.name,
                "type": param.type,
                "widget_type": widget_type,
                "config": widget_config,
                "required": not param.has_default,
                "help": param.help,
            }
        )

    # Use only the docstring summary (first line) as the title
    title = _get_docstring_summary(cmd_reg.docstring) or cmd_reg.name

    return {
        "command_name": cmd_reg.name,
        "title": title,
        "fields": fields,
        "confirmation_only": len(fields) == 0,
    }


def extract_value(param: ParameterInfo, raw_value: Any) -> Any:
    """Extract and convert a value for a parameter.

    Args:
        param: Parameter information with type.
        raw_value: Raw value from widget.

    Returns:
        Converted value appropriate for the parameter type.

    Raises:
        ValueError: If conversion fails.
    """
    # Get base type (handles Annotated types like PositiveInt)
    base_type = _get_base_type(param.type)

    if base_type is bool:
        return bool(raw_value)

    # Check for Enum types (isinstance needed for runtime type safety)
    if isinstance(base_type, type) and issubclass(base_type, Enum):  # pyright: ignore[reportUnnecessaryIsInstance]
        return raw_value  # Already an enum value from Select

    if base_type is int:
        try:
            return int(raw_value)
        except (ValueError, TypeError) as e:
            msg = f"Invalid integer value: {raw_value}"
            raise ValueError(msg) from e

    if base_type is float:
        try:
            return float(raw_value)
        except (ValueError, TypeError) as e:
            msg = f"Invalid number value: {raw_value}"
            raise ValueError(msg) from e

    # Default: return as string
    return str(raw_value) if raw_value is not None else ""


class ParameterSubmitted(Message):
    """Message posted when parameters are submitted.

    Attributes:
        command: The command registration.
        parameters: Dictionary of parameter names to values.
    """

    def __init__(
        self,
        command: CommandRegistration,
        parameters: dict[str, Any],
    ) -> None:
        """Initialize the message.

        Args:
            command: The command registration.
            parameters: Dictionary of parameter values.
        """
        super().__init__()
        self.command = command
        self.parameters = parameters


class ParameterCancelled(Message):
    """Message posted when parameter input is cancelled."""


class ParameterModal(ModalScreen[dict[str, Any] | None]):
    """Modal dialog for inputting command parameters.

    Dynamically generates form fields based on command parameter types
    and validates input before submission.

    Attributes:
        BINDINGS: Key bindings for the modal.
        DEFAULT_CSS: Default styling for the modal.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "submit", "Submit", show=False),
    ]

    DEFAULT_CSS: ClassVar[str] = """
    ParameterModal {
        align: center middle;
    }

    ParameterModal > Vertical {
        width: 60;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1 2;
    }

    ParameterModal #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    ParameterModal .form-field {
        height: auto;
        margin-bottom: 1;
    }

    ParameterModal .field-label {
        height: 1;
        margin-bottom: 0;
    }

    ParameterModal Input {
        width: 100%;
        height: 3;
        border: tall $primary;
        background: $background;
        padding: 0 1;
    }

    ParameterModal Input:focus {
        border: tall $accent;
    }

    ParameterModal Switch {
        height: 1;
    }

    ParameterModal Select {
        width: 100%;
        height: 3;
    }

    ParameterModal .required-marker {
        color: $error;
    }

    ParameterModal #button-row {
        height: 3;
        margin-top: 1;
        align: center middle;
    }

    ParameterModal Button {
        min-width: 12;
        margin: 0 1;
    }

    ParameterModal #submit-btn {
        background: $success;
        color: $text;
    }

    ParameterModal #cancel-btn {
        background: $error;
        color: $text;
    }
    """

    def __init__(
        self,
        command: CommandRegistration,
        *,
        name: str | None = None,
        widget_id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the ParameterModal.

        Args:
            command: Command registration to show parameters for.
            name: Widget name.
            widget_id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=widget_id, classes=classes)
        self._command = command
        self._form_config = generate_form_config(command)
        self._widgets: dict[str, Any] = {}

    @property
    def command(self) -> CommandRegistration:
        """Get the command registration.

        Returns:
            The command registration.
        """
        return self._command

    @override
    def compose(self) -> ComposeResult:
        """Compose the modal layout.

        Returns:
            Widget composition.
        """
        with Vertical():
            yield Static(self._form_config["title"], id="modal-title")

            if self._form_config["confirmation_only"]:
                yield Static("Press Enter to execute or Escape to cancel.")
            else:
                for field in self._form_config["fields"]:
                    yield from self._compose_field(field)

            with Horizontal(id="button-row"):
                yield Button("Submit", variant="success", id="submit-btn")
                yield Button("Cancel", variant="error", id="cancel-btn")

    def _compose_field(self, field: dict[str, Any]) -> ComposeResult:
        """Compose a single form field.

        Args:
            field: Field configuration dictionary.

        Yields:
            Widgets for the field.
        """
        name = field["name"]
        widget_type = field["widget_type"]
        config = field["config"]
        required = field["required"]

        with Vertical(classes="form-field"):
            # Label with optional required marker
            label_text = name.replace("_", " ").title()
            if required:
                yield Label(f"{label_text} [red]*[/red]", classes="field-label")
            else:
                yield Label(label_text, classes="field-label")

            # Create appropriate widget
            widget = self._create_widget(name, widget_type, config)
            self._widgets[name] = widget
            yield widget

    def _create_widget(
        self,
        name: str,
        widget_type: str,
        config: dict[str, Any],
    ) -> Input | Switch | Select[Any]:
        """Create a widget for a field.

        Args:
            name: Field name.
            widget_type: Type of widget to create.
            config: Widget configuration.

        Returns:
            Configured widget instance.
        """
        if widget_type == "Switch":
            value = config.get("value", False)
            return Switch(value=value, id=f"field-{name}")

        if widget_type == "Select":
            options = config.get("options", [])
            return Select(
                options,
                prompt="Select...",
                id=f"field-{name}",
            )

        # String input (default widget type)
        value = str(config.get("value", "")) if config.get("value") is not None else ""
        placeholder = config.get("placeholder", "")
        return Input(
            value=value,
            placeholder=placeholder,
            id=f"field-{name}",
        )

    def _get_form_values(self) -> dict[str, Any]:
        """Extract values from all form widgets.

        Returns:
            Dictionary of field names to extracted values.
        """
        values: dict[str, Any] = {}
        form_params = get_form_parameters(self._command.parameters)

        for field in self._form_config["fields"]:
            name = field["name"]
            widget = self._widgets.get(name)

            if widget is None:
                continue

            # Find corresponding parameter info
            param = next((p for p in form_params if p.name == name), None)
            if param is None:
                continue

            # Extract value from widget (all widget types have .value)
            raw_value = widget.value

            values[name] = extract_value(param, raw_value)

        return values

    def _validate_required_fields(self) -> list[str]:
        """Validate that all required fields have values.

        Returns:
            List of error messages for invalid fields.
        """
        errors: list[str] = []

        for field in self._form_config["fields"]:
            if not field["required"]:
                continue

            name = field["name"]
            widget = self._widgets.get(name)

            if widget is None:
                continue

            # Check if value is empty/missing
            is_empty_input = isinstance(widget, Input) and not widget.value.strip()
            is_blank_select = isinstance(widget, Select) and widget.value is Select.BLANK
            if is_empty_input or is_blank_select:
                errors.append(f"{name} is required")

        return errors

    def action_cancel(self) -> None:
        """Cancel the modal and dismiss."""
        self.dismiss(None)
        self.post_message(ParameterCancelled())

    def action_submit(self) -> None:
        """Submit the form values."""
        errors = self._validate_required_fields()
        if errors:
            # Show validation errors
            self.notify("\n".join(errors), severity="error")
            return

        try:
            values = self._get_form_values()
            self.post_message(ParameterSubmitted(self._command, values))
            self.dismiss(values)
        except ValueError as e:
            self.notify(str(e), severity="error")

    @on(Button.Pressed, "#submit-btn")
    def _on_submit_pressed(self, _event: Button.Pressed) -> None:
        """Handle submit button press."""
        self.action_submit()

    @on(Button.Pressed, "#cancel-btn")
    def _on_cancel_pressed(self, _event: Button.Pressed) -> None:
        """Handle cancel button press."""
        self.action_cancel()
