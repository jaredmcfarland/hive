"""Contract tests for MCP generation.

Tests the MCP server generation from App registry including
command-to-tool conversion, input schema generation, and error handling.

RED phase: These tests should FAIL until MCP generator is implemented.
"""

from __future__ import annotations

# Import refinement types at module level for proper type resolution
# (needed because get_type_hints requires types in global scope)
from hive.types import PositiveInt


class TestMCPGenerator:
    """Contract tests for MCPGenerator class."""

    def test_generator_exists(self) -> None:
        """MCPGenerator class exists and can be instantiated."""
        from hive.generators.mcp import MCPGenerator

        generator = MCPGenerator()
        assert generator is not None

    def test_generator_requires_fastmcp(self) -> None:
        """MCPGenerator raises ImportError if FastMCP not installed."""
        # This test validates the optional dependency guard
        from hive.generators.mcp import MCPGenerator

        generator = MCPGenerator()
        # Should work if fastmcp is installed (optional dep)
        assert hasattr(generator, "generate")

    def test_generate_returns_mcp_server_config(self) -> None:
        """MCPGenerator.generate() returns MCPServerConfig."""
        from hive import App
        from hive.generators.mcp import MCPGenerator
        from hive.spec.models import MCPServerConfig

        app = App("test_app")
        generator = MCPGenerator()
        config = generator.generate(app)

        assert isinstance(config, MCPServerConfig)
        assert config.name == "test_app"

    def test_generate_includes_tools_for_commands(self) -> None:
        """Generated MCP config includes tools for registered commands."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def create_task(ctx, title: str, priority: int = 1) -> dict:
            """Create a new task."""
            return {"title": title, "priority": priority}

        generator = MCPGenerator()
        config = generator.generate(app)

        assert len(config.tools) >= 1
        tool_names = [t.name for t in config.tools]
        assert "create_task" in tool_names


class TestCommandToToolConversion:
    """Tests for converting Hive commands to MCP tools."""

    def test_command_becomes_tool(self) -> None:
        """Command is converted to MCP tool with same name."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def my_command(ctx, arg: str) -> str:
            """My command description."""
            return arg

        generator = MCPGenerator()
        config = generator.generate(app)

        tool = next((t for t in config.tools if t.name == "my_command"), None)
        assert tool is not None
        assert tool.description == "My command description."

    def test_command_parameters_become_tool_input_schema(self) -> None:
        """Command parameters are converted to tool input schema."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def create_item(ctx, name: str, count: int, active: bool = True) -> dict:
            """Create an item."""
            return {"name": name, "count": count, "active": active}

        generator = MCPGenerator()
        config = generator.generate(app)

        tool = next((t for t in config.tools if t.name == "create_item"), None)
        assert tool is not None

        # Check input schema has properties
        schema = tool.input_schema
        assert schema is not None
        assert hasattr(schema, "properties")
        assert "name" in schema.properties
        assert "count" in schema.properties

    def test_required_parameters_marked_in_schema(self) -> None:
        """Required parameters are listed in schema's required array."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def create_item(ctx, required_arg: str, optional_arg: str = "default") -> dict:
            """Create an item."""
            return {}

        generator = MCPGenerator()
        config = generator.generate(app)

        tool = next((t for t in config.tools if t.name == "create_item"), None)
        assert tool is not None

        schema = tool.input_schema
        assert hasattr(schema, "required")
        assert "required_arg" in schema.required
        assert "optional_arg" not in schema.required


class TestMCPInputSchemaGeneration:
    """Tests for MCP tool input schema generation."""

    def test_string_parameter_schema(self) -> None:
        """String parameters generate correct JSON Schema."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def cmd(ctx, name: str) -> str:
            """Command."""
            return name

        generator = MCPGenerator()
        config = generator.generate(app)
        tool = config.tools[0]

        assert tool.input_schema.properties["name"]["type"] == "string"

    def test_integer_parameter_schema(self) -> None:
        """Integer parameters generate correct JSON Schema."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def cmd(ctx, count: int) -> int:
            """Command."""
            return count

        generator = MCPGenerator()
        config = generator.generate(app)
        tool = config.tools[0]

        assert tool.input_schema.properties["count"]["type"] == "integer"

    def test_refinement_type_constraints_preserved(self) -> None:
        """Hive refinement type constraints are included in schema."""
        from hive import App, command
        from hive.generators.mcp import MCPGenerator

        app = App("test_app")

        @command(app)
        async def cmd(ctx, priority: PositiveInt) -> int:
            """Command."""
            return priority

        generator = MCPGenerator()
        config = generator.generate(app)
        tool = config.tools[0]

        schema = tool.input_schema.properties["priority"]
        assert schema["type"] == "integer"
        assert schema.get("minimum") == 1


class TestMCPErrorHandling:
    """Tests for MCP error response format."""

    def test_validation_error_format(self) -> None:
        """Validation errors are converted to MCP error format."""
        from hive.generators.mcp import format_mcp_error

        error = ValueError("Invalid input: name is required")
        mcp_error = format_mcp_error(error)

        assert "error" in mcp_error
        assert mcp_error["error"]["code"] == "validation_error"
        assert "name is required" in mcp_error["error"]["message"]

    def test_execution_error_format(self) -> None:
        """Execution errors are converted to MCP error format."""
        from hive.generators.mcp import format_mcp_error

        error = RuntimeError("Database connection failed")
        mcp_error = format_mcp_error(error)

        assert "error" in mcp_error
        assert mcp_error["error"]["code"] == "execution_error"
        assert "Database connection failed" in mcp_error["error"]["message"]

    def test_error_includes_type(self) -> None:
        """MCP error includes the original exception type."""
        from hive.generators.mcp import format_mcp_error

        class CustomError(Exception):
            pass

        error = CustomError("Custom error message")
        mcp_error = format_mcp_error(error)

        assert "CustomError" in mcp_error["error"].get("type", "")
