"""Type definitions for Hive core framework.

This module contains dataclasses that represent registration metadata
for commands, queries, entities, and screens.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class ConstraintMetadata:
    """Constraint information extracted from refinement types."""

    description: str = ""
    """Human-readable constraint description."""

    min_value: float | None = None
    """Minimum value for numeric types."""

    max_value: float | None = None
    """Maximum value for numeric types."""

    pattern: str | None = None
    """Regex pattern for string types."""

    min_length: int | None = None
    """Minimum length for string/collection types."""

    max_length: int | None = None
    """Maximum length for string/collection types."""

    validator: Callable[[Any], bool] | None = field(default=None, repr=False)
    """Runtime validation function."""


class ParameterKind(Enum):
    """Kind of parameter in a function signature."""

    POSITIONAL = "positional"
    KEYWORD = "keyword"
    VAR_POSITIONAL = "var_positional"
    VAR_KEYWORD = "var_keyword"


@dataclass
class ParameterInfo:
    """Metadata about a single function parameter.

    Extracted from function signature using inspect module.
    """

    name: str
    type: type
    default: Any = None
    has_default: bool = False
    kind: ParameterKind = ParameterKind.KEYWORD
    help: str | None = None
    short: str | None = None
    constraints: ConstraintMetadata | None = None


@dataclass
class CommandRegistration:
    """Represents a decorated command function.

    Commands are state-modifying operations that may create, update,
    or delete data.
    """

    name: str
    func: Callable[..., Any]
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: type | None = None
    docstring: str | None = None
    entities: list[type] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    hidden: bool = False


@dataclass
class QueryRegistration:
    """Represents a decorated query function.

    Queries are read-only operations that retrieve data without
    modifying state. They may optionally be cached.
    """

    name: str
    func: Callable[..., Any]
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: type | None = None
    docstring: str | None = None
    entities: list[type] = field(default_factory=list)
    cache_ttl: int | None = None


@dataclass
class FieldInfo:
    """Metadata about an entity field."""

    name: str
    type: type
    primary_key: bool = False
    nullable: bool = False
    default: Any = None
    index: bool = False


@dataclass
class RelationshipInfo:
    """Metadata about entity relationships."""

    field_name: str
    target_entity: str
    relationship_type: str  # "one-to-one", "one-to-many", "many-to-one"
    foreign_key: str


@dataclass
class EntityRegistration:
    """Represents a decorated entity class.

    Entities are SQLModel classes that define database tables.
    """

    name: str
    cls: type
    fields: list[FieldInfo] = field(default_factory=list)
    table_name: str = ""
    relationships: list[RelationshipInfo] = field(default_factory=list)


@dataclass
class ScreenRegistration:
    """Represents a decorated screen class.

    Screens are TUI views that can be navigated to.
    """

    name: str
    cls: type
    default: bool = False
    keybinding: str | None = None
    docstring: str | None = None


@dataclass
class Argument:
    """Marker for CLI positional arguments.

    Used with Annotated to provide metadata for CLI generation.

    Example:
        async def add(
            ctx,
            title: Annotated[str, Argument(help="Task title")],
        ) -> Task:
            ...
    """

    help: str | None = None


@dataclass
class Option:
    """Marker for CLI named options.

    Used with Annotated to provide metadata for CLI generation.

    Example:
        async def list_tasks(
            ctx,
            completed: Annotated[bool, Option("--completed", "-c", help="Show completed")] = False,
        ) -> list[Task]:
            ...
    """

    names: tuple[str, ...] = field(default_factory=tuple)
    help: str | None = None

    def __init__(self, *names: str, help: str | None = None) -> None:
        object.__setattr__(self, "names", names)
        object.__setattr__(self, "help", help)
