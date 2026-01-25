"""CRUD Task Manager Example.

A complete CRUD application demonstrating entities, commands, queries,
contracts, and refinement types in Hive.

Example:
    >>> from crud import app
    >>> from hive.testing import TestClient
    >>>
    >>> async def demo():
    ...     async with TestClient(app) as client:
    ...         task = await client.invoke("create_task", title="Learn Hive")
    ...         print(task)
"""

# Re-export app from the separate module to avoid circular imports
# Import to trigger decorator registration (side effects)
from crud import commands as commands  # noqa: F401
from crud import entities as entities  # noqa: F401
from crud import queries as queries  # noqa: F401
from crud.app import app as app

__all__ = ["app"]
