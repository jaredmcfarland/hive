"""Hive CLI module.

This module provides the command-line interface for the Hive framework,
including specification export, MCP server, REST API server, and project
management commands.

Commands:
    hive spec export: Export specification as JSON Schema or TOML
    hive spec diff: Compare specifications and detect breaking changes
    hive mcp serve: Start MCP server for AI agent integration
    hive serve: Start REST API server
    hive new: Create new Hive project
    hive dev: Start development server with hot reload
    hive build: Build distributable package
    hive publish: Publish package to registry
"""

from __future__ import annotations

# Public API exports - populated as modules are implemented
__all__: list[str] = []
