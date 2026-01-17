"""Decorator factories for commands, queries, entities, and screens.

These decorators register functions and classes with the application registry
at import time, enabling automatic generation of CLI, TUI, and other interfaces.
"""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

from hive.core.types import (
    CommandRegistration,
    ConstraintMetadata,
    EntityRegistration,
    FieldInfo,
    ParameterInfo,
    ParameterKind,
    QueryRegistration,
    ScreenRegistration,
)
from hive.types.introspection import extract_constraints

# Type variable for preserving function signature
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T", bound=type)


def _extract_parameters(func: Callable[..., Any]) -> list[ParameterInfo]:
    """Extract parameter information from a function signature.

    Args:
        func: The function to inspect.

    Returns:
        List of ParameterInfo for each parameter (excluding 'ctx').
    """
    sig = inspect.signature(func)
    try:
        # Use include_extras=True to preserve Annotated metadata for constraint extraction
        hints = get_type_hints(func, include_extras=True)
    except (NameError, TypeError, AttributeError):
        hints = {}

    params: list[ParameterInfo] = []

    for name, param in sig.parameters.items():
        # Skip the context parameter
        if name == "ctx":
            continue

        # Determine parameter kind
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            kind = ParameterKind.POSITIONAL
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            kind = ParameterKind.VAR_POSITIONAL
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            kind = ParameterKind.VAR_KEYWORD
        else:
            kind = ParameterKind.KEYWORD

        # Get type annotation (with Annotated metadata preserved)
        param_type = hints.get(name, Any)

        # Extract constraint metadata from refinement types
        constraint_info = extract_constraints(param_type)
        constraints: ConstraintMetadata | None = None
        if constraint_info:
            constraints = ConstraintMetadata(
                description=constraint_info.description,
                min_value=constraint_info.min_value,
                max_value=constraint_info.max_value,
                pattern=constraint_info.pattern,
                min_length=constraint_info.min_length,
                max_length=constraint_info.max_length,
                validator=constraint_info.validator,
            )

        # Check for default value
        has_default = param.default is not inspect.Parameter.empty
        default = param.default if has_default else None

        params.append(
            ParameterInfo(
                name=name,
                type=param_type,
                default=default,
                has_default=has_default,
                kind=kind,
                constraints=constraints,
            )
        )

    return params


def _extract_return_type(func: Callable[..., Any]) -> type | None:
    """Extract return type annotation from a function.

    Args:
        func: The function to inspect.

    Returns:
        The return type annotation, or None if not specified.
    """
    try:
        hints = get_type_hints(func)
        return hints.get("return")
    except (NameError, TypeError, AttributeError):
        return None


def command(
    app: Any,
    *,
    entities: list[type] | None = None,
    name: str | None = None,
    aliases: list[str] | None = None,
    hidden: bool = False,
) -> Callable[[F], F]:
    """Decorator factory for registering commands.

    Commands are state-modifying operations that may create, update,
    or delete data.

    Args:
        app: The application instance.
        entities: Related entity classes for documentation/cache invalidation.
        name: Override the command name (defaults to function name).
        aliases: Alternative names for the command.
        hidden: If True, hide from help text.

    Returns:
        Decorator that registers the function and returns it unchanged.

    Example:
        @command(app, entities=[Task])
        async def add(ctx, title: str) -> Task:
            '''Add a new task.'''
            ...
    """

    def decorator(func: F) -> F:
        cmd_name = name if name is not None else func.__name__

        registration = CommandRegistration(
            name=cmd_name,
            func=func,
            parameters=_extract_parameters(func),
            return_type=_extract_return_type(func),
            docstring=func.__doc__,
            entities=entities or [],
            aliases=aliases or [],
            hidden=hidden,
        )

        app.registry.register_command(registration)
        return func

    return decorator


def query(
    app: Any,
    *,
    entities: list[type] | None = None,
    cache_ttl: int | None = None,
    name: str | None = None,
) -> Callable[[F], F]:
    """Decorator factory for registering queries.

    Queries are read-only operations that retrieve data without
    modifying state. They may optionally be cached.

    Args:
        app: The application instance.
        entities: Related entity classes for cache invalidation.
        cache_ttl: Cache time-to-live in seconds (None = no caching).
        name: Override the query name (defaults to function name).

    Returns:
        Decorator that registers the function and returns it unchanged.

    Example:
        @query(app, entities=[Task], cache_ttl=300)
        async def list_tasks(ctx, completed: bool = False) -> list[Task]:
            '''List all tasks.'''
            ...
    """

    def decorator(func: F) -> F:
        query_name = name if name is not None else func.__name__

        registration = QueryRegistration(
            name=query_name,
            func=func,
            parameters=_extract_parameters(func),
            return_type=_extract_return_type(func),
            docstring=func.__doc__,
            entities=entities or [],
            cache_ttl=cache_ttl,
        )

        app.registry.register_query(registration)
        return func

    return decorator


def entity(app: Any) -> Callable[[T], T]:
    """Decorator factory for registering entities.

    Entities are SQLModel classes that define database tables.

    Args:
        app: The application instance.

    Returns:
        Decorator that registers the class and returns it unchanged.

    Example:
        @entity(app)
        class Task(SQLModel, table=True):
            id: int | None = Field(default=None, primary_key=True)
            title: str
    """

    def decorator(cls: T) -> T:
        # Extract field information from the class
        fields: list[FieldInfo] = []

        # Try to get model_fields from Pydantic/SQLModel
        if hasattr(cls, "model_fields"):
            for field_name, field_info in cls.model_fields.items():
                # Check for primary_key in field extras or metadata
                is_pk = False
                if hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
                    is_pk = field_info.json_schema_extra.get("primary_key", False)
                # Also check SQLModel's sa_column metadata
                if hasattr(field_info, "metadata"):
                    for meta in field_info.metadata:
                        if hasattr(meta, "primary_key"):
                            is_pk = meta.primary_key

                fields.append(
                    FieldInfo(
                        name=field_name,
                        type=field_info.annotation or type(None),
                        primary_key=is_pk,
                        nullable=not field_info.is_required(),
                        default=field_info.default if field_info.default is not None else None,
                    )
                )

        # Determine table name
        table_name = getattr(cls, "__tablename__", cls.__name__.lower())

        registration = EntityRegistration(
            name=cls.__name__,
            cls=cls,
            fields=fields,
            table_name=table_name,
        )

        app.registry.register_entity(registration)
        return cls

    return decorator


def screen(
    app: Any,
    *,
    default: bool = False,
    keybinding: str | None = None,
    name: str | None = None,
) -> Callable[[T], T]:
    """Decorator factory for registering screens.

    Screens are TUI views that can be navigated to.

    Args:
        app: The application instance.
        default: If True, this is the startup screen.
        keybinding: Global key to navigate to this screen.
        name: Override the screen name (defaults to class name).

    Returns:
        Decorator that registers the class and returns it unchanged.

    Example:
        @screen(app, default=True, keybinding="d")
        class DashboardScreen(Screen):
            '''Main dashboard.'''
            ...
    """

    def decorator(cls: T) -> T:
        screen_name = name if name is not None else cls.__name__

        registration = ScreenRegistration(
            name=screen_name,
            cls=cls,
            default=default,
            keybinding=keybinding,
            docstring=cls.__doc__,
        )

        app.registry.register_screen(registration)
        return cls

    return decorator
