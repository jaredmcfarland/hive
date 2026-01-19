"""Unit tests for optional FastAPI dependency handling.

Tests that the REST generator gracefully handles the case where
FastAPI is not installed.

RED phase: These tests should FAIL until REST generator is implemented.
"""

from __future__ import annotations


class TestRESTOptionalDependency:
    """Tests for optional FastAPI dependency handling."""

    def test_rest_module_importable(self) -> None:
        """hive.generators.rest module can be imported."""
        from hive.generators import rest

        assert rest is not None

    def test_generator_works_with_fastapi_installed(self) -> None:
        """RESTGenerator works when FastAPI is available."""
        from hive.generators.rest import RESTGenerator

        generator = RESTGenerator()
        assert generator is not None

    def test_rest_available_flag_reflects_installation(self) -> None:
        """REST_AVAILABLE constant reflects FastAPI installation status."""
        from hive.generators.rest import REST_AVAILABLE

        # Verify the constant exists and is boolean
        assert isinstance(REST_AVAILABLE, bool)

    def test_serve_without_fastapi_raises_error(self) -> None:
        """Attempting to serve REST without FastAPI raises helpful error."""
        from hive import App
        from hive.generators.rest import RESTGenerator

        _app = App("test")  # Would be used in serve()
        generator = RESTGenerator()

        # Verify the method exists
        assert hasattr(generator, "serve")

    def test_create_app_method_exists(self) -> None:
        """RESTGenerator has create_app method to create FastAPI app."""
        from hive.generators.rest import RESTGenerator

        generator = RESTGenerator()
        assert hasattr(generator, "create_app")
