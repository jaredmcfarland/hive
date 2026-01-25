"""API Client Example - Hive Service Integration.

Demonstrates @service decorator, httpx integration, and credential management
for building CLI applications that interact with external APIs.

Example:
    $ api-client config set-key YOUR_API_KEY
    $ api-client user get 123
    $ api-client user list --limit 10
"""

from __future__ import annotations

# Import commands to register them
from api_client import commands as _commands  # noqa: F401
from api_client import services as _services  # noqa: F401
from api_client.app import app

# Generate CLI from app
cli = app.cli()

__all__ = ["app", "cli"]
