"""Minimal Hive application example.

This is the simplest possible Hive application - a single command
that says hello. Use this as a starting point for understanding
Hive's core concepts.

Example:
    >>> from minimal import app
    >>> from hive.testing import TestClient
    >>>
    >>> async def demo():
    ...     async with TestClient(app) as client:
    ...         result = await client.invoke("hello", name="World")
    ...         print(result)
    ...
    >>> import asyncio
    >>> asyncio.run(demo())
    Hello, World!
"""

from hive.app import App
from hive.core.decorators import command
from hive.runtime.context import ExecutionContext

# Create the Hive application
app = App("minimal")


@command(app)
async def hello(ctx: ExecutionContext, name: str = "World") -> str:  # noqa: ARG001
    """Say hello to someone.

    A friendly greeting command demonstrating basic Hive patterns.

    Args:
        ctx: Execution context (provides database, services, config).
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting string.

    Example:
        >>> await hello(ctx, name="Alice")
        'Hello, Alice!'
    """
    return f"Hello, {name}!"


# Export the app for CLI generation and testing
__all__ = ["app", "hello"]
