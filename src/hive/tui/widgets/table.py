"""HiveDataTable widget for TUI applications.

A data table with automatic column generation from Pydantic models,
sorting support, row selection events, and loading/error/empty states.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable

if TYPE_CHECKING:
    from textual.widgets.data_table import RowKey


class HiveRowSelected(Message):
    """Posted when a row is selected in HiveDataTable.

    Attributes:
        row_key: The key of the selected row.
        row_data: The data for the selected row.
    """

    def __init__(self, row_key: RowKey, row_data: dict[str, Any]) -> None:
        """Initialize the message.

        Args:
            row_key: The key of the selected row.
            row_data: The data for the selected row.
        """
        self.row_key = row_key
        self.row_data = row_data
        super().__init__()


class HiveDataTable[T: BaseModel | dict[str, Any]](DataTable[str]):
    """Data table with automatic column generation and state management.

    Extends Textual DataTable to provide:
    - Automatic column generation from Pydantic model schema
    - Automatic column generation from dict keys
    - Sorting by clicking column headers
    - Row selection events with row data
    - Loading, error, and empty state display

    CSS Classes:
        .hive-data-table: Base table styling
        .hive-data-table--loading: Loading overlay
        .hive-data-table--error: Error display
        .hive-data-table--empty: Empty state

    Attributes:
        is_loading: True while data is being loaded.
        error: Error message if loading failed.
        empty_message: Message to display when no data.
    """

    DEFAULT_CSS = """
    HiveDataTable {
        width: 100%;
        height: 100%;
    }

    HiveDataTable.hive-data-table--loading {
        opacity: 0.5;
    }

    HiveDataTable.hive-data-table--error {
        border: solid red;
    }

    HiveDataTable.hive-data-table--empty {
        color: $text-muted;
    }
    """

    # Reactive properties for state management (use is_loading to avoid Widget.loading conflict)
    is_loading: reactive[bool] = reactive(False)
    error: reactive[str | None] = reactive(None)

    class ColumnSorted(Message):
        """Posted when a column is sorted.

        Attributes:
            column: The column key that was sorted.
            ascending: True if sorted ascending, False if descending.
        """

        def __init__(self, column: str, ascending: bool) -> None:
            """Initialize the message.

            Args:
                column: The column key that was sorted.
                ascending: True if sorted ascending.
            """
            self.column = column
            self.ascending = ascending
            super().__init__()

    def __init__(
        self,
        *,
        query: str | None = None,
        columns: list[str] | None = None,
        empty_message: str = "No data",
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize the data table.

        Args:
            query: Optional query name for data binding.
            columns: Optional list of column keys. If None, columns are
                auto-generated from the first data item.
            empty_message: Message to display when no data.
            name: Optional widget name.
            id: Optional widget ID for CSS.
            classes: Optional CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._query = query
        self._specified_columns = columns
        self._empty_message = empty_message
        self._hive_data: list[T] = []
        self._columns_set = False
        self._sort_column: str | None = None
        self._sort_ascending = True
        self.add_class("hive-data-table")

    @property
    def empty_message(self) -> str:
        """Get the empty message.

        Returns:
            The message displayed when the table has no data.
        """
        return self._empty_message

    def _watch_is_loading(self, is_loading: bool) -> None:
        """Watch the is_loading reactive property.

        Args:
            is_loading: The new loading state.
        """
        if is_loading:
            self.add_class("hive-data-table--loading")
        else:
            self.remove_class("hive-data-table--loading")

    def _watch_error(self, error: str | None) -> None:
        """Watch the error reactive property.

        Args:
            error: The new error message.
        """
        if error:
            self.add_class("hive-data-table--error")
        else:
            self.remove_class("hive-data-table--error")

    def set_data(self, data: list[T]) -> None:
        """Set the table data.

        Automatically generates columns from the first item if columns
        were not specified.

        Args:
            data: List of data items (Pydantic models or dicts).
        """
        self._hive_data = data
        self.clear()

        if not data:
            self.add_class("hive-data-table--empty")
            return

        self.remove_class("hive-data-table--empty")

        # Get column names
        column_names = self._get_column_names(data[0])

        # Set up columns if not already done
        if not self._columns_set:
            for col_name in column_names:
                self.add_column(col_name, key=col_name)
            self._columns_set = True

        # Add rows
        for i, item in enumerate(data):
            row_values = self._get_row_values(item, column_names)
            self.add_row(*row_values, key=str(i))

    def _get_column_names(self, item: T) -> list[str]:
        """Get column names from a data item.

        Args:
            item: A data item (Pydantic model or dict).

        Returns:
            List of column names.
        """
        if self._specified_columns:
            return self._specified_columns

        if isinstance(item, BaseModel):
            return list(type(item).model_fields.keys())
        if isinstance(item, dict):
            return list(item.keys())
        return []

    def _get_row_values(self, item: T, column_names: list[str]) -> list[Any]:
        """Get row values from a data item.

        Args:
            item: A data item (Pydantic model or dict).
            column_names: List of column names to extract.

        Returns:
            List of values for the row.
        """
        if isinstance(item, BaseModel):
            return [getattr(item, col, "") for col in column_names]
        if isinstance(item, dict):
            return [item.get(col, "") for col in column_names]
        return []

    def get_hive_row_at(self, index: int) -> dict[str, Any] | None:
        """Get Hive row data at the given index.

        This is different from DataTable.get_row_at which returns the raw row values.
        This method returns the original data item as a dictionary.

        Args:
            index: The row index.

        Returns:
            The row data as a dict, or None if index is invalid.
        """
        if 0 <= index < len(self._hive_data):
            item = self._hive_data[index]
            if isinstance(item, BaseModel):
                return item.model_dump()
            # Item is a dict based on type bound
            return dict(item)
        return None

    def sort_by(self, column: str, *, ascending: bool = True) -> None:
        """Sort the table by the given column.

        Args:
            column: The column key to sort by.
            ascending: True for ascending, False for descending.
        """
        self._sort_column = column
        self._sort_ascending = ascending

        # Sort the data
        if self._hive_data:
            self._hive_data = sorted(
                self._hive_data,
                key=lambda item: self._get_sort_key(item, column),
                reverse=not ascending,
            )
            # Refresh the table
            self.set_data(self._hive_data)

        self.post_message(self.ColumnSorted(column, ascending))

    def _get_sort_key(self, item: T, column: str) -> Any:
        """Get the sort key for an item.

        Args:
            item: The data item.
            column: The column to sort by.

        Returns:
            The value to use for sorting.
        """
        if isinstance(item, BaseModel):
            return getattr(item, column, "")
        if isinstance(item, dict):
            return item.get(column, "")
        return ""

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection.

        Args:
            event: The row selected event.
        """
        # Get the row data
        row_key = event.row_key
        if row_key.value is None:
            return
        try:
            row_index = int(row_key.value)
            row_data = self.get_hive_row_at(row_index)
            if row_data:
                self.post_message(HiveRowSelected(row_key, row_data))
        except (ValueError, TypeError):
            pass

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click for sorting.

        Args:
            event: The header selected event.
        """
        column_key = event.column_key
        if column_key:
            # Toggle sort direction if same column
            if self._sort_column == str(column_key.value):
                self._sort_ascending = not self._sort_ascending
            else:
                self._sort_ascending = True

            self.sort_by(str(column_key.value), ascending=self._sort_ascending)
