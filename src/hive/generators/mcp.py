"""MCP (Model Context Protocol) server generation.

This module provides the MCPGenerator class for converting Hive App
commands into MCP tools, enabling AI agents to discover and invoke
them through the MCP protocol.

Optional dependency: Requires `fastmcp` package for actual server
functionality. Install with: pip install hive-framework[mcp]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hive.generators.schema import python_type_to_json_schema
from hive.spec.models import MCPServerConfig, MCPTool, MCPToolSchema

if TYPE_CHECKING:
    from hive.app import App

# Check for optional FastMCP dependency
_mcp_available = False
try:
    import fastmcp

    _mcp_available = True
except ImportError:
    # fastmcp is an optional dependency; MCP features disabled when not installed.
    pass

MCP_AVAILABLE: bool = _mcp_available


class MCPGenerator:
    """Generate MCP server configuration from a Hive App.

    Converts registered commands to MCP tools with proper input schemas,
    descriptions, and parameter validation.

    Example:
        >>> from hive import App, command
        >>> from hive.generators.mcp import MCPGenerator
        >>>
        >>> app = App("myapp")
        >>>
        >>> @command(app)
        >>> async def greet(ctx, name: str) -> str:
        ...     return f"Hello, {name}!"
        >>>
        >>> generator = MCPGenerator()
        >>> config = generator.generate(app)
        >>> print(config.tools[0].name)  # "greet"
    """

    def __init__(self) -> None:
        """Initialize the MCP generator."""

    def generate(self, app: App) -> MCPServerConfig:
        """Generate MCP server configuration from an App.

        Converts all registered commands to MCP tools.

        Args:
            app: A Hive App instance with registered commands.

        Returns:
            MCPServerConfig with tools for each command.
        """
        tools: list[MCPTool] = []

        for cmd_reg in app.registry.list_commands():
            tool = self._command_to_tool(cmd_reg)
            tools.append(tool)

        return MCPServerConfig(
            name=app.name,
            description=f"MCP server for {app.name}",
            tools=tools,
        )

    def _command_to_tool(self, cmd_reg: Any) -> MCPTool:
        """Convert a CommandRegistration to an MCPTool.

        Args:
            cmd_reg: CommandRegistration from the registry.

        Returns:
            MCPTool representing the command.
        """
        # Build input schema from parameters
        properties: dict[str, dict[str, Any]] = {}
        required: list[str] = []

        for param in cmd_reg.parameters:
            # Skip context parameter
            if param.name == "ctx":
                continue

            # Get JSON Schema for parameter type
            param_schema = python_type_to_json_schema(param.type)

            # Add description if available
            if param.help:
                param_schema["description"] = param.help

            properties[param.name] = param_schema

            # Track required parameters
            if not param.has_default:
                required.append(param.name)

        input_schema = MCPToolSchema(
            type="object",
            properties=properties,
            required=required,
        )

        return MCPTool(
            name=cmd_reg.name,
            description=cmd_reg.docstring or f"Execute {cmd_reg.name} command",
            inputSchema=input_schema,  # Use alias name for Pydantic
        )

    def serve(
        self,
        app: App,
        transport: str = "stdio",
        host: str = "127.0.0.1",
        port: int = 8080,
    ) -> None:
        """Start the MCP server.

        Args:
            app: Hive App to serve.
            transport: Transport protocol ('stdio' or 'sse').
            host: Host to bind for SSE transport.
            port: Port for SSE transport.

        Raises:
            ImportError: If FastMCP is not installed.
        """
        if not MCP_AVAILABLE:
            msg = "FastMCP is not installed. Install with: pip install hive-framework[mcp]"
            raise ImportError(msg)

        # Generate server config
        config = self.generate(app)

        # Create FastMCP server
        mcp = fastmcp.FastMCP(config.name)  # type: ignore[name-defined]

        # Register tools
        for tool in config.tools:
            self._register_tool(mcp, app, tool)

        # Start server based on transport
        if transport == "stdio":
            mcp.run()
        elif transport == "sse":
            mcp.run(transport="sse", host=host, port=port)
        else:
            msg = f"Unknown transport: {transport}"
            raise ValueError(msg)

    def _register_tool(
        self,
        mcp: Any,
        app: App,
        tool: MCPTool,
    ) -> None:
        """Register an MCP tool with the FastMCP server.

        Args:
            mcp: FastMCP server instance.
            app: Hive App for command execution.
            tool: MCPTool to register.
        """
        cmd_reg = app.registry.get_command(tool.name)
        if cmd_reg is None:
            msg = f"Command not found: {tool.name}"
            raise ValueError(msg)

        # Create tool function
        @mcp.tool(name=tool.name, description=tool.description)
        async def tool_handler(**kwargs: Any) -> Any:  # pyright: ignore[reportUnusedFunction]
            """Execute the command."""
            from hive.runtime.context import ExecutionContext  # noqa: PLC0415

            async with ExecutionContext() as ctx:
                return await cmd_reg.func(ctx, **kwargs)


def format_mcp_error(error: Exception) -> dict[str, Any]:
    """Format an exception as an MCP error response.

    Args:
        error: The exception to format.

    Returns:
        Dict with MCP error format.
    """
    # Determine error code based on exception type
    code = "validation_error" if isinstance(error, (ValueError, TypeError)) else "execution_error"

    return {
        "error": {
            "code": code,
            "message": str(error),
            "type": type(error).__name__,
        }
    }
