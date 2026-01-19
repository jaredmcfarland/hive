"""Hive specification export module.

This module provides functionality for exporting Hive application specifications
to machine-readable formats (JSON Schema, TOML) and comparing specifications
to detect breaking changes.

Example:
    >>> from hive import App
    >>> from hive.spec import (
    ...     build_specification,
    ...     export_specification,
    ...     diff_specifications,
    ... )
    >>>
    >>> app = App("myapp")
    >>> spec = build_specification(app)
    >>> json_schema = export_specification(app, format="json")
"""

from __future__ import annotations

from hive.spec.models import (
    CommandSchema,
    DiffItem,
    EntitySchema,
    FieldSchema,
    MCPServerConfig,
    MCPTool,
    MCPToolSchema,
    ParameterSchema,
    ProjectTemplate,
    QuerySchema,
    RelationshipSchema,
    RESTAPIConfig,
    RESTEndpoint,
    Specification,
    SpecificationDiff,
    SpecificationMetadata,
    TemplateFile,
)

__all__: list[str] = [  # noqa: RUF022
    # Core specification models
    "Specification",
    "SpecificationMetadata",
    "CommandSchema",
    "QuerySchema",
    "EntitySchema",
    "FieldSchema",
    "RelationshipSchema",
    "ParameterSchema",
    # Diff models
    "DiffItem",
    "SpecificationDiff",
    # MCP models
    "MCPTool",
    "MCPToolSchema",
    "MCPServerConfig",
    # REST models
    "RESTEndpoint",
    "RESTAPIConfig",
    # Template models
    "TemplateFile",
    "ProjectTemplate",
]
