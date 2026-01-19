"""TUI generation components for Hive framework.

This package provides Textual-based TUI application generation from
@screen decorated classes.

Public API:
    HiveScreen: Base class for screens with reactive data binding
    HiveApp: Generated Textual application
    ScreenContext: TUI-specific execution context
    QueryBindingExecutor: Execute query bindings with caching
"""

from __future__ import annotations

from hive.tui.app import HiveApp as HiveApp
from hive.tui.binding import QueryBindingExecutor as QueryBindingExecutor
from hive.tui.screens import DataError as DataError
from hive.tui.screens import DataLoaded as DataLoaded
from hive.tui.screens import HiveScreen as HiveScreen
from hive.tui.screens import ScreenContext as ScreenContext

__all__: list[str] = [
    "DataError",
    "DataLoaded",
    "HiveApp",
    "HiveScreen",
    "QueryBindingExecutor",
    "ScreenContext",
]
