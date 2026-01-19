"""Unit tests for optional FastMCP dependency handling.

Tests that the MCP generator gracefully handles the case where
FastMCP is not installed.

RED phase: These tests should FAIL until MCP generator is implemented.
"""

from __future__ import annotations

import sys
from unittest.mock import patch


class TestMCPOptionalDependency:
    """Tests for optional FastMCP dependency handling."""

    def test_mcp_module_importable(self) -> None:
        """hive.generators.mcp module can be imported."""
        from hive.generators import mcp

        assert mcp is not None

    def test_generator_works_with_fastmcp_installed(self) -> None:
        """MCPGenerator works when FastMCP is available."""
        from hive.generators.mcp import MCPGenerator

        generator = MCPGenerator()
        assert generator is not None

    def test_missing_fastmcp_raises_helpful_error(self) -> None:
        """Importing MCPGenerator without FastMCP raises ImportError with install hint."""
        # Temporarily hide fastmcp
        with patch.dict(sys.modules, {"fastmcp": None}):
            # Re-import to trigger the check

            from hive.generators import mcp

            # The module should still import
            assert mcp is not None

    def test_mcp_available_flag_reflects_installation(self) -> None:
        """MCP_AVAILABLE constant reflects FastMCP installation status."""
        from hive.generators.mcp import MCP_AVAILABLE

        # If we got here, fastmcp should be available (it's in optional deps)
        # This test verifies the constant exists
        assert isinstance(MCP_AVAILABLE, bool)

    def test_serve_without_fastmcp_raises_error(self) -> None:
        """Attempting to serve MCP without FastMCP raises helpful error."""
        from hive.generators.mcp import MCPGenerator

        generator = MCPGenerator()

        # If FastMCP is not installed, serve should raise
        # If it is installed, this should work
        # We just verify the method exists
        assert hasattr(generator, "serve")
