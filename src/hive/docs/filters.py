"""Jinja2 filters for documentation generation.

Custom filters for formatting constraints, types, and other
documentation elements in templates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jinja2 import Environment


def format_type(type_str: str) -> str:
    """Format a type string for display in documentation.

    Converts JSON Schema types to human-readable format.

    Args:
        type_str: JSON Schema type (e.g., "string", "integer").

    Returns:
        Human-readable type string.

    Example:
        >>> format_type("string")
        'string'
        >>> format_type("integer")
        'integer'
    """
    type_map = {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
        "array": "list",
        "object": "object",
        "null": "null",
    }
    return type_map.get(type_str, type_str)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def format_constraints(param: dict[str, Any] | Any) -> str:
    """Format parameter constraints as a human-readable string.

    Extracts and formats constraint information from a parameter schema.
    Works with both dicts and Pydantic model objects.

    Args:
        param: Parameter schema dictionary or Pydantic model with constraint fields.

    Returns:
        Formatted constraint string, or empty string if no constraints.

    Example:
        >>> format_constraints({"minimum": 1, "maximum": 100})
        '1 ≤ value ≤ 100'
        >>> format_constraints({"minLength": 1})
        'length ≥ 1'
    """
    parts = []

    # Numeric constraints
    min_val = _get_attr(param, "minimum")
    max_val = _get_attr(param, "maximum")
    if min_val is not None and max_val is not None:
        parts.append(f"{min_val} ≤ value ≤ {max_val}")
    elif min_val is not None:
        parts.append(f"value ≥ {min_val}")
    elif max_val is not None:
        parts.append(f"value ≤ {max_val}")

    # Length constraints
    min_len = _get_attr(param, "minLength") or _get_attr(param, "min_length")
    max_len = _get_attr(param, "maxLength") or _get_attr(param, "max_length")
    if min_len is not None and max_len is not None:
        parts.append(f"length: {min_len}-{max_len}")
    elif min_len is not None:
        parts.append(f"length ≥ {min_len}")
    elif max_len is not None:
        parts.append(f"length ≤ {max_len}")

    # Pattern constraint
    pattern = _get_attr(param, "pattern")
    if pattern:
        parts.append(f"pattern: `{pattern}`")

    # Format constraint
    fmt = _get_attr(param, "format")
    if fmt:
        parts.append(f"format: {fmt}")

    return ", ".join(parts)


def format_default(value: Any) -> str:
    """Format a default value for display.

    Handles None, strings, and other types appropriately.

    Args:
        value: Default value to format.

    Returns:
        Formatted default value string.

    Example:
        >>> format_default(None)
        'None'
        >>> format_default("hello")
        '"hello"'
        >>> format_default(42)
        '42'
    """
    if value is None:
        return "None"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return str(value)
    return str(value)


def markdown_escape(text: str) -> str:
    r"""Escape special markdown characters.

    Args:
        text: Text to escape.

    Returns:
        Text with markdown special characters escaped.

    Example:
        >>> markdown_escape("*bold* and _italic_")
        '\\*bold\\* and \\_italic\\_'
    """
    if not text:
        return ""
    special_chars = ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!"]
    result = text
    for char in special_chars:
        result = result.replace(char, f"\\{char}")
    return result


def troff_escape(text: str) -> str:
    r"""Escape special troff/groff characters for man pages.

    Args:
        text: Text to escape.

    Returns:
        Text with troff special characters escaped.

    Example:
        >>> troff_escape("use --help for help")
        'use \\-\\-help for help'
    """
    if not text:
        return ""
    # Escape backslash first
    result = text.replace("\\", "\\\\")
    # Escape hyphens (troff treats them as minus signs)
    result = result.replace("-", "\\-")
    # Escape dots at start of line (would be interpreted as commands)
    lines = result.split("\n")
    escaped_lines = []
    for line in lines:
        if line.startswith("."):
            escaped_lines.append("\\&" + line)
        else:
            escaped_lines.append(line)
    return "\n".join(escaped_lines)


def first_line(text: str | None) -> str:
    r"""Extract the first line of text for brief descriptions.

    Args:
        text: Text to extract from.

    Returns:
        First line of text, or empty string if None/empty.

    Example:
        >>> first_line("First line.\nSecond line.")
        'First line.'
    """
    if not text:
        return ""
    return text.split("\n")[0].strip()


def code_block(text: str, language: str = "") -> str:
    """Wrap text in a markdown code block.

    Args:
        text: Text to wrap.
        language: Optional language for syntax highlighting.

    Returns:
        Text wrapped in markdown code fences.

    Example:
        >>> print(code_block("x = 1", "python"))
        ```python
        x = 1
        ```
    """
    return f"```{language}\n{text}\n```"


def register_filters(env: Environment) -> None:
    """Register all custom filters with a Jinja2 environment.

    Args:
        env: Jinja2 environment to add filters to.
    """
    env.filters["format_type"] = format_type
    env.filters["format_constraints"] = format_constraints
    env.filters["format_default"] = format_default
    env.filters["markdown_escape"] = markdown_escape
    env.filters["troff_escape"] = troff_escape
    env.filters["first_line"] = first_line
    env.filters["code_block"] = code_block
