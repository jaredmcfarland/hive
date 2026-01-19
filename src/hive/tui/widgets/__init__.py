"""Standard widgets for Hive TUI applications.

This package provides themed, reusable widgets that integrate with
the Hive framework.

Public API:
    HiveHeader: Application header with title and navigation
    HiveFooter: Footer with keybinding hints
    HiveDataTable: Data table with query binding support (Phase 7)
    ParameterModal: Dynamic parameter input modal (Phase 6)
    filter_commands: Fuzzy search filter for commands (used by command palette)
"""

from __future__ import annotations

from hive.tui.widgets.footer import HiveFooter as HiveFooter
from hive.tui.widgets.header import HiveHeader as HiveHeader
from hive.tui.widgets.modal import ParameterModal as ParameterModal
from hive.tui.widgets.palette import filter_commands as filter_commands
from hive.tui.widgets.table import HiveDataTable as HiveDataTable

__all__: list[str] = [
    "HiveDataTable",
    "HiveFooter",
    "HiveHeader",
    "ParameterModal",
    "filter_commands",
]
