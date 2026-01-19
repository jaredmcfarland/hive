"""Hive project templates module.

This module provides project scaffolding templates for the `hive new` command.
Templates define the file structure, dependencies, and example code for
new Hive projects.

Example:
    >>> from hive.templates import load_template, list_templates
    >>>
    >>> templates = list_templates()
    >>> template = load_template("default")
"""

from __future__ import annotations

# Public API exports - populated as modules are implemented
__all__: list[str] = []
