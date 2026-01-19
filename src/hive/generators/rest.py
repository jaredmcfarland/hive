"""REST API generation via FastAPI.

This module provides the RESTGenerator class for converting Hive App
commands and queries into REST API endpoints, enabling web clients
to interact with the application via HTTP.

Optional dependency: Requires `fastapi` and `uvicorn` packages for
actual server functionality. Install with: pip install hive-framework[rest]
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Literal

from hive.generators.schema import python_type_to_json_schema
from hive.spec.models import RESTAPIConfig, RESTEndpoint

if TYPE_CHECKING:
    from collections.abc import Callable

    from hive.app import App

# Check for optional FastAPI dependency
_rest_available = False
try:
    import fastapi  # pyright: ignore[reportUnusedImport]
    import uvicorn

    _rest_available = True
except ImportError:
    fastapi = None
    uvicorn = None

REST_AVAILABLE: bool = _rest_available


def format_validation_error(errors: list[dict[str, Any]]) -> dict[str, Any]:
    """Format validation errors in Pydantic/FastAPI format.

    Args:
        errors: List of validation error dicts.

    Returns:
        Dict with 'detail' containing error list.
    """
    return {"detail": errors}


def format_execution_error(
    error: Exception,
    include_traceback: bool = False,
) -> dict[str, Any]:
    """Format an execution error as a REST error response.

    Args:
        error: The exception to format.
        include_traceback: Whether to include stack trace.

    Returns:
        Dict with error details.
    """
    result: dict[str, Any] = {
        "detail": str(error),
        "error_type": type(error).__name__,
    }

    if include_traceback:
        result["traceback"] = traceback.format_exc()

    return result


def _get_base_type(param_type: Any) -> type:
    """Extract base type from Annotated or return type as-is.

    For `Annotated[int, Is[...]]`, returns `int`.
    For plain types like `str`, returns `str`.

    Args:
        param_type: A type annotation, possibly Annotated.

    Returns:
        The base type without Annotated wrapper.
    """
    from typing import Annotated, get_args, get_origin  # noqa: PLC0415

    origin = get_origin(param_type)
    if origin is Annotated:
        args = get_args(param_type)
        return args[0] if args else param_type
    return param_type


AuthType = Literal["none", "api_key", "bearer", "basic"]


def create_auth_dependency(  # noqa: C901
    auth_type: AuthType = "none",
    api_key_header: str = "X-API-Key",
    api_key_env: str = "HIVE_API_KEY",
) -> Callable[..., Any] | None:
    """Create an authentication dependency for FastAPI.

    Args:
        auth_type: Type of authentication (none, api_key, bearer, basic).
        api_key_header: Header name for API key auth.
        api_key_env: Environment variable for API key.

    Returns:
        A FastAPI dependency function or None for no auth.

    Raises:
        ValueError: If auth_type is unknown.
    """
    if auth_type == "none":
        return None

    if not REST_AVAILABLE:
        msg = "FastAPI is not installed. Install with: pip install hive-framework[rest]"
        raise ImportError(msg)

    import os  # noqa: PLC0415

    from fastapi import Depends, Header, HTTPException, status  # noqa: PLC0415
    from fastapi.security import HTTPBasic, HTTPBearer  # noqa: PLC0415

    if auth_type == "api_key":

        async def api_key_auth(
            api_key: str = Header(alias=api_key_header),  # pyright: ignore[reportCallInDefaultInitializer]
        ) -> str:
            """Validate API key from header."""
            expected_key = os.environ.get(api_key_env, "")
            if not expected_key or api_key != expected_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )
            return api_key

        return api_key_auth

    if auth_type == "bearer":
        bearer_scheme = HTTPBearer()

        async def bearer_auth(
            credentials: Any = Depends(bearer_scheme),  # noqa: B008  # pyright: ignore[reportCallInDefaultInitializer]
        ) -> str:
            """Validate Bearer token."""
            # In a real implementation, validate the token
            # For now, just check it exists
            if not credentials or not credentials.credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid bearer token",
                )
            return str(credentials.credentials)

        return bearer_auth

    if auth_type == "basic":
        basic_scheme = HTTPBasic()

        async def basic_auth(
            credentials: Any = Depends(basic_scheme),  # noqa: B008  # pyright: ignore[reportCallInDefaultInitializer]
        ) -> str:
            """Validate Basic auth credentials."""
            # In a real implementation, validate username/password
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )
            return str(credentials.username)

        return basic_auth

    msg = f"Unknown auth type: {auth_type}"
    raise ValueError(msg)


class RESTGenerator:
    """Generate REST API configuration from a Hive App.

    Converts registered commands to POST endpoints and queries to
    GET endpoints with proper request/response schemas.

    Example:
        >>> from hive import App, command, query
        >>> from hive.generators.rest import RESTGenerator
        >>>
        >>> app = App("myapp")
        >>>
        >>> @command(app)
        >>> async def create_task(ctx, title: str) -> dict:
        ...     return {"title": title}
        >>>
        >>> generator = RESTGenerator()
        >>> config = generator.generate(app)
        >>> print(config.endpoints[0].path)  # "/commands/create_task"
    """

    def __init__(self) -> None:
        """Initialize the REST generator."""

    def generate(self, app: App) -> RESTAPIConfig:
        """Generate REST API configuration from an App.

        Converts all registered commands to POST endpoints and
        queries to GET endpoints.

        Args:
            app: A Hive App instance with registered commands/queries.

        Returns:
            RESTAPIConfig with endpoints for each command/query.
        """
        endpoints: list[RESTEndpoint] = []

        # Convert commands to POST endpoints
        for cmd_reg in app.registry.list_commands():
            endpoint = self._command_to_endpoint(cmd_reg)
            endpoints.append(endpoint)

        # Convert queries to GET endpoints
        for query_reg in app.registry.list_queries():
            endpoint = self._query_to_endpoint(query_reg)
            endpoints.append(endpoint)

        return RESTAPIConfig(
            title=app.name,
            description=f"REST API for {app.name}",
            endpoints=endpoints,
        )

    def _command_to_endpoint(self, cmd_reg: Any) -> RESTEndpoint:
        """Convert a CommandRegistration to a REST endpoint.

        Args:
            cmd_reg: CommandRegistration from the registry.

        Returns:
            RESTEndpoint representing the command as POST.
        """
        # Build request body schema from parameters
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

        request_body_schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        # Build response schema
        response_schema: dict[str, Any] = {"type": "object"}
        if cmd_reg.return_type:
            response_schema = python_type_to_json_schema(cmd_reg.return_type)

        return RESTEndpoint(
            path=f"/commands/{cmd_reg.name}",
            method="POST",
            operation_id=cmd_reg.name,
            summary=cmd_reg.name.replace("_", " ").title(),
            description=cmd_reg.docstring,
            request_body_schema=request_body_schema,
            response_schema=response_schema,
            tags=["commands"],
        )

    def _query_to_endpoint(self, query_reg: Any) -> RESTEndpoint:
        """Convert a QueryRegistration to a REST endpoint.

        Args:
            query_reg: QueryRegistration from the registry.

        Returns:
            RESTEndpoint representing the query as GET.
        """
        # Build response schema
        response_schema: dict[str, Any] = {"type": "object"}
        if query_reg.return_type:
            response_schema = python_type_to_json_schema(query_reg.return_type)

        return RESTEndpoint(
            path=f"/queries/{query_reg.name}",
            method="GET",
            operation_id=query_reg.name,
            summary=query_reg.name.replace("_", " ").title(),
            description=query_reg.docstring,
            request_body_schema=None,
            response_schema=response_schema,
            tags=["queries"],
        )

    def create_app(
        self,
        app: App,
        auth_type: AuthType = "none",
        api_key_header: str = "X-API-Key",
        api_key_env: str = "HIVE_API_KEY",
        debug: bool = False,
    ) -> Any:
        """Create a FastAPI application from a Hive App.

        Args:
            app: A Hive App instance.
            auth_type: Authentication type to use.
            api_key_header: Header name for API key auth.
            api_key_env: Environment variable for API key.
            debug: Enable debug mode (includes tracebacks in errors).

        Returns:
            A FastAPI application instance.

        Raises:
            ImportError: If FastAPI is not installed.
        """
        if not REST_AVAILABLE:
            msg = "FastAPI is not installed. Install with: pip install hive-framework[rest]"
            raise ImportError(msg)

        from fastapi import Depends, FastAPI  # noqa: PLC0415

        # Generate config for metadata
        config = self.generate(app)

        # Create FastAPI app
        fastapi_app = FastAPI(
            title=config.title,
            description=config.description or "",
            version=config.version,
        )

        # Create auth dependency if needed
        auth_dep = create_auth_dependency(auth_type, api_key_header, api_key_env)
        dependencies = [Depends(auth_dep)] if auth_dep else []

        # Add health endpoint
        @fastapi_app.get("/health")
        async def health_check() -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
            """Health check endpoint."""
            try:
                from hive import __version__  # noqa: PLC0415
            except ImportError:
                __version__ = "0.1.0"

            return {
                "status": "healthy",
                "version": __version__,
            }

        # Add spec endpoint (uses US1 export functionality)
        @fastapi_app.get("/spec")
        async def get_spec() -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
            """Get application specification."""
            import json  # noqa: PLC0415

            from hive.spec.export import export_specification  # noqa: PLC0415

            spec_json = export_specification(app, format="json")
            return json.loads(spec_json)

        # Register command endpoints
        for cmd_reg in app.registry.list_commands():
            self._register_command_endpoint(
                fastapi_app,
                app,
                cmd_reg,
                dependencies,
                debug,
            )

        # Register query endpoints
        for query_reg in app.registry.list_queries():
            self._register_query_endpoint(
                fastapi_app,
                app,
                query_reg,
                dependencies,
                debug,
            )

        return fastapi_app

    def _register_command_endpoint(
        self,
        fastapi_app: Any,
        hive_app: App,  # noqa: ARG002  # Reserved for future per-request context
        cmd_reg: Any,
        dependencies: list[Any],
        debug: bool,
    ) -> None:
        """Register a command as a POST endpoint.

        Args:
            fastapi_app: FastAPI application.
            hive_app: Hive App for command execution.
            cmd_reg: CommandRegistration to register.
            dependencies: FastAPI dependencies (auth, etc).
            debug: Enable debug mode.
        """
        from fastapi import Body, HTTPException  # noqa: PLC0415
        from pydantic import create_model  # noqa: PLC0415

        # Build request model from parameters
        fields: dict[str, Any] = {}
        for param in cmd_reg.parameters:
            if param.name == "ctx":
                continue

            # Get the type, defaulting to Any
            param_type = param.type if param.type else Any

            # Handle default value
            if param.has_default:
                fields[param.name] = (param_type, param.default)
            else:
                fields[param.name] = (param_type, ...)

        # Create dynamic request model
        request_model = create_model(
            f"{cmd_reg.name.title().replace('_', '')}Request",
            **fields,
        )

        # Create a factory function to capture the right cmd_reg and request_model
        def make_command_handler(
            cmd: Any,
            model: type,
            debug_mode: bool,
        ) -> Callable[..., Any]:
            """Create a command handler with proper closure."""

            async def handler(body: Any = Body(...)) -> Any:  # noqa: B008  # pyright: ignore[reportCallInDefaultInitializer]
                """Execute command."""
                from pydantic import ValidationError  # noqa: PLC0415

                from hive.runtime.context import ExecutionContext  # noqa: PLC0415

                # Validate body against model
                try:
                    validated = model.model_validate(body) if isinstance(body, dict) else body
                except ValidationError as e:
                    # Re-raise as FastAPI will handle this with 422
                    raise HTTPException(
                        status_code=422,
                        detail=e.errors(),
                    ) from e

                try:
                    async with ExecutionContext() as ctx:
                        params = (
                            validated.model_dump()
                            if hasattr(validated, "model_dump")
                            else dict(validated)
                        )
                        return await cmd.func(ctx, **params)
                except (ValueError, TypeError) as e:
                    raise HTTPException(status_code=400, detail=str(e)) from e
                except Exception as e:
                    error_response = format_execution_error(e, include_traceback=debug_mode)
                    raise HTTPException(status_code=500, detail=error_response["detail"]) from e

            return handler

        # Create and register the endpoint
        handler = make_command_handler(cmd_reg, request_model, debug)
        fastapi_app.add_api_route(
            f"/commands/{cmd_reg.name}",
            handler,
            methods=["POST"],
            tags=["commands"],
            summary=cmd_reg.name.replace("_", " ").title(),
            description=cmd_reg.docstring,
            dependencies=dependencies,
        )

    def _register_query_endpoint(
        self,
        fastapi_app: Any,
        hive_app: App,  # noqa: ARG002  # Reserved for future per-request context
        query_reg: Any,
        dependencies: list[Any],
        debug: bool,
    ) -> None:
        """Register a query as a GET endpoint.

        Args:
            fastapi_app: FastAPI application.
            hive_app: Hive App for query execution.
            query_reg: QueryRegistration to register.
            dependencies: FastAPI dependencies (auth, etc).
            debug: Enable debug mode.
        """
        from fastapi import HTTPException  # noqa: PLC0415

        # Collect parameter info
        param_list = [p for p in query_reg.parameters if p.name != "ctx"]

        # Create query handler using exec to build proper function signature
        # This allows FastAPI to recognize query parameters correctly

        # Build parameter code for the function signature
        param_code_parts: list[str] = []
        for p in param_list:
            base_type = _get_base_type(p.type)
            type_name = base_type.__name__ if hasattr(base_type, "__name__") else "str"
            if p.has_default:
                default_repr = repr(p.default)
                param_code_parts.append(f"{p.name}: {type_name} = {default_repr}")
            else:
                param_code_parts.append(f"{p.name}: {type_name}")

        params_str = ", ".join(param_code_parts)

        # Create the handler function dynamically
        func_code = f"""
async def query_handler({params_str}) -> Any:
    from hive.runtime.context import ExecutionContext
    try:
        async with ExecutionContext() as ctx:
            return await _qry_func(ctx, {", ".join(f"{p.name}={p.name}" for p in param_list)})
    except (ValueError, TypeError) as e:
        raise _HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        error_response = _format_error(e, include_traceback=_debug)
        raise _HTTPException(status_code=500, detail=error_response["detail"]) from e
"""

        # Create namespace with required variables
        namespace: dict[str, Any] = {
            "_qry_func": query_reg.func,
            "_HTTPException": HTTPException,
            "_format_error": format_execution_error,
            "_debug": debug,
            "Any": Any,
            "int": int,
            "str": str,
            "bool": bool,
            "float": float,
            "list": list,
            "dict": dict,
        }

        # Execute to create the function
        exec(func_code, namespace)  # noqa: S102  # nosec B102
        handler = namespace["query_handler"]

        # Register the endpoint
        fastapi_app.add_api_route(
            f"/queries/{query_reg.name}",
            handler,
            methods=["GET"],
            tags=["queries"],
            summary=query_reg.name.replace("_", " ").title(),
            description=query_reg.docstring,
            dependencies=dependencies,
        )

    def serve(  # noqa: PLR0913
        self,
        app: App,
        host: str = "127.0.0.1",
        port: int = 8000,
        reload: bool = False,
        workers: int = 1,
        auth_type: AuthType = "none",
        api_key_header: str = "X-API-Key",
        api_key_env: str = "HIVE_API_KEY",
        debug: bool = False,
    ) -> None:
        """Start the REST API server.

        Args:
            app: Hive App to serve.
            host: Host to bind.
            port: Port to listen on.
            reload: Enable hot reload.
            workers: Number of worker processes.
            auth_type: Authentication type.
            api_key_header: Header name for API key.
            api_key_env: Environment variable for API key.
            debug: Enable debug mode.

        Raises:
            ImportError: If FastAPI/uvicorn is not installed.
        """
        if not REST_AVAILABLE:
            msg = "FastAPI is not installed. Install with: pip install hive-framework[rest]"
            raise ImportError(msg)

        fastapi_app = self.create_app(
            app,
            auth_type=auth_type,
            api_key_header=api_key_header,
            api_key_env=api_key_env,
            debug=debug,
        )

        uvicorn.run(  # type: ignore[union-attr]
            fastapi_app,
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
        )
