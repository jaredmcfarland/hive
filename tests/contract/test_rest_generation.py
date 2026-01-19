"""Contract tests for REST API generation.

Tests the REST API generation from App registry including
command-to-POST and query-to-GET endpoint conversion,
request/response schema generation, and error handling.

RED phase: These tests should FAIL until REST generator is implemented.
"""

from __future__ import annotations

# Import refinement types at module level for proper type resolution


class TestRESTGenerator:
    """Contract tests for RESTGenerator class."""

    def test_generator_exists(self) -> None:
        """RESTGenerator class exists and can be instantiated."""
        from hive.generators.rest import RESTGenerator

        generator = RESTGenerator()
        assert generator is not None

    def test_generator_requires_fastapi(self) -> None:
        """RESTGenerator has REST_AVAILABLE flag for optional dependency."""
        from hive.generators.rest import REST_AVAILABLE

        # Verify the constant exists
        assert isinstance(REST_AVAILABLE, bool)

    def test_generate_returns_rest_api_config(self) -> None:
        """RESTGenerator.generate() returns RESTAPIConfig."""
        from hive import App
        from hive.generators.rest import RESTGenerator
        from hive.spec.models import RESTAPIConfig

        app = App("test_app")
        generator = RESTGenerator()
        config = generator.generate(app)

        assert isinstance(config, RESTAPIConfig)
        assert config.title == "test_app"

    def test_generate_includes_endpoints_for_commands(self) -> None:
        """Generated REST config includes endpoints for registered commands."""
        from hive import App, command
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def create_task(ctx, title: str, priority: int = 1) -> dict:
            """Create a new task."""
            return {"title": title, "priority": priority}

        generator = RESTGenerator()
        config = generator.generate(app)

        assert len(config.endpoints) >= 1
        paths = [e.path for e in config.endpoints]
        assert "/commands/create_task" in paths

    def test_generate_includes_endpoints_for_queries(self) -> None:
        """Generated REST config includes endpoints for registered queries."""
        from hive import App, query
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @query(app)
        async def list_tasks(ctx, completed: bool = False) -> list:
            """List all tasks."""
            return []

        generator = RESTGenerator()
        config = generator.generate(app)

        paths = [e.path for e in config.endpoints]
        assert "/queries/list_tasks" in paths


class TestCommandToPostEndpoint:
    """Tests for converting Hive commands to POST endpoints."""

    def test_command_becomes_post_endpoint(self) -> None:
        """Command is converted to POST endpoint."""
        from hive import App, command
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def my_command(ctx, arg: str) -> str:
            """My command description."""
            return arg

        generator = RESTGenerator()
        config = generator.generate(app)

        endpoint = next((e for e in config.endpoints if e.path == "/commands/my_command"), None)
        assert endpoint is not None
        assert endpoint.method == "POST"
        assert endpoint.description == "My command description."

    def test_command_parameters_become_request_body_schema(self) -> None:
        """Command parameters are converted to request body schema."""
        from hive import App, command
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def create_item(ctx, name: str, count: int, active: bool = True) -> dict:
            """Create an item."""
            return {"name": name, "count": count, "active": active}

        generator = RESTGenerator()
        config = generator.generate(app)

        endpoint = next((e for e in config.endpoints if e.path == "/commands/create_item"), None)
        assert endpoint is not None

        # Check request body schema has properties
        schema = endpoint.request_body_schema
        assert schema is not None
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "count" in schema["properties"]

    def test_command_endpoint_has_operation_id(self) -> None:
        """Command endpoint has correct operation_id."""
        from hive import App, command
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def create_task(ctx, title: str) -> dict:
            """Create a task."""
            return {}

        generator = RESTGenerator()
        config = generator.generate(app)

        endpoint = next((e for e in config.endpoints if e.path == "/commands/create_task"), None)
        assert endpoint is not None
        assert endpoint.operation_id == "create_task"


class TestQueryToGetEndpoint:
    """Tests for converting Hive queries to GET endpoints."""

    def test_query_becomes_get_endpoint(self) -> None:
        """Query is converted to GET endpoint."""
        from hive import App, query
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @query(app)
        async def get_items(ctx, category: str = "all") -> list:
            """Get items by category."""
            return []

        generator = RESTGenerator()
        config = generator.generate(app)

        endpoint = next((e for e in config.endpoints if e.path == "/queries/get_items"), None)
        assert endpoint is not None
        assert endpoint.method == "GET"
        assert endpoint.description == "Get items by category."

    def test_query_has_response_schema(self) -> None:
        """Query endpoint has response schema."""
        from hive import App, query
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @query(app)
        async def get_items(ctx) -> list:
            """Get items."""
            return []

        generator = RESTGenerator()
        config = generator.generate(app)

        endpoint = next((e for e in config.endpoints if e.path == "/queries/get_items"), None)
        assert endpoint is not None
        assert endpoint.response_schema is not None


class TestValidationErrorResponse:
    """Tests for ValidationError response format (HTTP 400)."""

    def test_validation_error_format(self) -> None:
        """Validation errors follow Pydantic/FastAPI format."""
        from hive.generators.rest import format_validation_error

        # Create a validation-like error
        errors = [
            {"loc": ["body", "name"], "msg": "field required", "type": "value_error.missing"},
        ]
        response = format_validation_error(errors)

        assert "detail" in response
        assert isinstance(response["detail"], list)
        assert len(response["detail"]) == 1
        assert response["detail"][0]["loc"] == ["body", "name"]

    def test_validation_error_includes_location(self) -> None:
        """Validation error includes field location."""
        from hive.generators.rest import format_validation_error

        errors = [
            {"loc": ["body", "priority"], "msg": "value must be positive", "type": "value_error"},
        ]
        response = format_validation_error(errors)

        assert response["detail"][0]["loc"] == ["body", "priority"]

    def test_validation_error_includes_message(self) -> None:
        """Validation error includes descriptive message."""
        from hive.generators.rest import format_validation_error

        errors = [
            {"loc": ["query", "page"], "msg": "value is not a valid integer", "type": "type_error"},
        ]
        response = format_validation_error(errors)

        assert "not a valid integer" in response["detail"][0]["msg"]


class TestExecutionErrorResponse:
    """Tests for ExecutionError response format (HTTP 500)."""

    def test_execution_error_format(self) -> None:
        """Execution errors are converted to REST error format."""
        from hive.generators.rest import format_execution_error

        error = RuntimeError("Database connection failed")
        response = format_execution_error(error)

        assert "detail" in response
        assert "Database connection failed" in response["detail"]

    def test_execution_error_includes_type(self) -> None:
        """Execution error includes exception type."""
        from hive.generators.rest import format_execution_error

        error = ValueError("Invalid configuration")
        response = format_execution_error(error)

        assert "error_type" in response
        assert response["error_type"] == "ValueError"

    def test_execution_error_no_traceback_by_default(self) -> None:
        """Execution error doesn't include traceback by default."""
        from hive.generators.rest import format_execution_error

        error = RuntimeError("Test error")
        response = format_execution_error(error)

        assert response.get("traceback") is None

    def test_execution_error_includes_traceback_in_debug(self) -> None:
        """Execution error includes traceback in debug mode."""
        from hive.generators.rest import format_execution_error

        try:
            raise RuntimeError("Test error")
        except RuntimeError as e:
            response = format_execution_error(e, include_traceback=True)

        assert response.get("traceback") is not None
        assert "RuntimeError" in response["traceback"]
