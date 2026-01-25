"""App instance for CRUD example.

This module defines the Hive App instance, separate from the
main __init__.py to avoid circular imports.
"""

from hive.app import App

# Create the Hive application
app = App("crud")
