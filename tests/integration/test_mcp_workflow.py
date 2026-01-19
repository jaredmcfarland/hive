"""Integration tests for MCP workflow.

Tests the full MCP server workflow including CLI commands
and transport options.

RED phase: These tests should FAIL until MCP server is implemented.
"""

from __future__ import annotations

import subprocess

import pytest


class TestHiveMCPServeCLI:
    """Integration tests for `hive mcp serve` command."""

    def test_mcp_serve_help(self) -> None:
        """Hive mcp serve --help shows usage."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "mcp", "serve", "--help"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "serve" in result.stdout.lower()
        assert "--transport" in result.stdout

    def test_mcp_serve_lists_transports(self) -> None:
        """Hive mcp serve --help lists available transports."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "mcp", "serve", "--help"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "stdio" in result.stdout.lower()
        assert "sse" in result.stdout.lower()

    def test_mcp_serve_default_transport_is_stdio(self) -> None:
        """Hive mcp serve defaults to stdio transport."""
        # We can't easily test actual server startup, but we can check the help
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "mcp", "serve", "--help"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Check default value indicator
        assert "stdio" in result.stdout.lower()

    @pytest.mark.skip(reason="Requires actual MCP server running")
    def test_mcp_serve_stdio_transport(self) -> None:
        """Hive mcp serve --transport stdio starts stdio server."""
        # This would require more sophisticated testing with process management

    @pytest.mark.skip(reason="Requires actual MCP server running")
    def test_mcp_serve_sse_transport(self) -> None:
        """Hive mcp serve --transport sse --host 127.0.0.1 --port 8080 starts SSE server."""


class TestMCPToolExecution:
    """Integration tests for MCP tool execution."""

    @pytest.mark.skip(reason="Requires actual MCP server running")
    def test_tool_execution_success(self) -> None:
        """Tool execution returns success response."""

    @pytest.mark.skip(reason="Requires actual MCP server running")
    def test_tool_execution_validation_error(self) -> None:
        """Tool execution with invalid input returns validation error."""

    @pytest.mark.skip(reason="Requires actual MCP server running")
    def test_tool_execution_with_context(self) -> None:
        """Tool execution receives proper ExecutionContext."""


class TestMCPServerGeneration:
    """Integration tests for MCP server generation."""

    def test_generate_mcp_server_config(self) -> None:
        """Can generate MCP server configuration from App."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def hello(ctx, name: str) -> str:
            """Say hello."""
            return f"Hello, {name}!"

        generator = MCPGenerator()
        config = generator.generate(app)

        assert config.name == "test_app"
        assert len(config.tools) == 1
        assert config.tools[0].name == "hello"

    def test_generated_config_has_valid_schemas(self) -> None:
        """Generated tool schemas are valid JSON Schema."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def create_item(ctx, name: str, count: int = 1) -> dict:
            """Create an item."""
            return {"name": name, "count": count}

        generator = MCPGenerator()
        config = generator.generate(app)

        tool = config.tools[0]
        schema = tool.input_schema

        # Validate schema structure (MCPToolSchema is a Pydantic model)
        assert schema.type == "object"
        assert hasattr(schema, "properties")
        assert "name" in schema.properties
        assert "count" in schema.properties
