"""Trakr - Personal project and time tracking.

A Hive application demonstrating CLI, TUI, and REST interfaces.
"""

# Import modules to register decorators
from trakr import (
    commands,  # pyright: ignore[reportUnusedImport] # noqa: F401
    queries,  # pyright: ignore[reportUnusedImport] # noqa: F401
    screens,  # pyright: ignore[reportUnusedImport] # noqa: F401
    services,  # pyright: ignore[reportUnusedImport] # noqa: F401
)
from trakr.app import app

__all__ = ["app"]
