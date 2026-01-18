"""Standard widgets for Hive TUI applications.

This package provides themed, reusable widgets that integrate with
the Hive framework.

Public API:
    HiveHeader: Application header with title and navigation
    HiveFooter: Footer with keybinding hints
    HiveDataTable: Data table with query binding support (Phase 7)
    CommandPalette: Command search and execution palette (Phase 6)
    ParameterModal: Dynamic parameter input modal (Phase 6)
"""

from __future__ import annotations

from hive.tui.widgets.footer import HiveFooter as HiveFooter
from hive.tui.widgets.header import HiveHeader as HiveHeader
from hive.tui.widgets.modal import ParameterModal as ParameterModal
from hive.tui.widgets.palette import CommandPalette as CommandPalette
from hive.tui.widgets.table import HiveDataTable as HiveDataTable

__all__: list[str] = [
    "CommandPalette",
    "HiveDataTable",
    "HiveFooter",
    "HiveHeader",
    "ParameterModal",
]
