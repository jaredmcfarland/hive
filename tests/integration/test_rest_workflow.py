# ruff: noqa: S607
"""Integration tests for REST API workflow.

Tests the end-to-end REST API functionality including
hive serve command, OpenAPI docs, and built-in endpoints.

RED phase: These tests should FAIL until REST functionality is implemented.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

# Skip all tests if FastAPI not installed
fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

if TYPE_CHECKING:
    from collections.abc import Generator


class TestRESTServerStartup:
    """Tests for REST server startup via CLI."""

    @pytest.fixture
    def test_app(self) -> Generator[str, None, None]:
        """Create a temporary test app file."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            app_file = Path(tmpdir) / "app.py"
            app_file.write_text('''
from hive import App, command, query

app = App("test_rest_app")

@command(app)
async def create_item(ctx, name: str, value: int = 0) -> dict:
    """Create a new item."""
    return {"name": name, "value": value, "id": 1}

@query(app)
async def list_items(ctx, limit: int = 10) -> list:
    """List all items."""
    return [{"name": "item1", "id": 1}]
''')
            yield str(app_file)

    def test_serve_command_exists(self) -> None:
        """Hive serve command exists."""
        result = subprocess.run(  # noqa: PLW1510
            ["uv", "run", "hive", "serve", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "serve" in result.stdout.lower() or "serve" in result.stderr.lower()


class TestOpenAPIDocs:
    """Tests for OpenAPI documentation at /docs."""

    @pytest.fixture
    def rest_app(self):
        """Create a FastAPI app from RESTGenerator."""
        from hive import App, command, query
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def create_task(ctx, title: str) -> dict:
            """Create a task."""
            return {"title": title}

        @query(app)
        async def list_tasks(ctx) -> list:
            """List tasks."""
            return []

        generator = RESTGenerator()
        return generator.create_app(app)

    def test_openapi_docs_available(self, rest_app) -> None:
        """OpenAPI docs are available at /docs."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self, rest_app) -> None:
        """OpenAPI JSON schema is available at /openapi.json."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    @pytest.fixture
    def rest_app(self):
        """Create a FastAPI app from RESTGenerator."""
        from hive import App
        from hive.generators.rest import RESTGenerator

        app = App("test_app")
        generator = RESTGenerator()
        return generator.create_app(app)

    def test_health_endpoint_returns_200(self, rest_app) -> None:
        """/health returns HTTP 200."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_status(self, rest_app) -> None:
        """/health returns status field."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_returns_version(self, rest_app) -> None:
        """/health returns version field."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestSpecEndpoint:
    """Tests for /spec endpoint."""

    @pytest.fixture
    def rest_app(self):
        """Create a FastAPI app from RESTGenerator."""
        from hive import App, command
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def greet(ctx, name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        generator = RESTGenerator()
        return generator.create_app(app)

    def test_spec_endpoint_returns_200(self, rest_app) -> None:
        """/spec returns HTTP 200."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/spec")
        assert response.status_code == 200

    def test_spec_endpoint_returns_specification(self, rest_app) -> None:
        """/spec returns application specification."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/spec")
        data = response.json()
        assert "metadata" in data
        assert "commands" in data

    def test_spec_endpoint_includes_commands(self, rest_app) -> None:
        """/spec includes registered commands."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/spec")
        data = response.json()
        assert "greet" in data["commands"]


class TestCommandEndpoints:
    """Tests for generated command endpoints."""

    @pytest.fixture
    def rest_app(self):
        """Create a FastAPI app with commands."""
        from hive import App, command
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @command(app)
        async def create_item(ctx, name: str, value: int = 0) -> dict:
            """Create an item."""
            return {"name": name, "value": value, "id": 1}

        generator = RESTGenerator()
        return generator.create_app(app)

    def test_command_endpoint_accepts_post(self, rest_app) -> None:
        """Command endpoint accepts POST requests."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.post(
            "/commands/create_item",
            json={"name": "test", "value": 42},
        )
        assert response.status_code == 200

    def test_command_endpoint_returns_result(self, rest_app) -> None:
        """Command endpoint returns command result."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.post(
            "/commands/create_item",
            json={"name": "test", "value": 42},
        )
        data = response.json()
        assert data["name"] == "test"
        assert data["value"] == 42

    def test_command_validation_error(self, rest_app) -> None:
        """Command endpoint returns 400 for validation errors."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.post(
            "/commands/create_item",
            json={},  # Missing required 'name'
        )
        assert response.status_code == 422  # FastAPI validation error


class TestQueryEndpoints:
    """Tests for generated query endpoints."""

    @pytest.fixture
    def rest_app(self):
        """Create a FastAPI app with queries."""
        from hive import App, query
        from hive.generators.rest import RESTGenerator

        app = App("test_app")

        @query(app)
        async def get_items(ctx, category: str = "all", limit: int = 10) -> list:
            """Get items by category."""
            return [{"category": category, "id": i} for i in range(min(limit, 3))]

        generator = RESTGenerator()
        return generator.create_app(app)

    def test_query_endpoint_accepts_get(self, rest_app) -> None:
        """Query endpoint accepts GET requests."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/queries/get_items")
        assert response.status_code == 200

    def test_query_endpoint_accepts_query_params(self, rest_app) -> None:
        """Query endpoint accepts query parameters."""
        from fastapi.testclient import TestClient

        client = TestClient(rest_app)
        response = client.get("/queries/get_items?category=books&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert all(item["category"] == "books" for item in data)
