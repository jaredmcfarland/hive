# API Client Example

This example demonstrates Hive's service integration capabilities for building
CLI applications that interact with external APIs.

## Features

- **@service decorator** - Declare external API clients with automatic lifecycle management
- **Credential management** - Secure API key storage using keyring
- **httpx integration** - Modern async HTTP client for API calls
- **Mock testing** - Service mocking patterns for reliable tests

## Quick Start

```bash
# Install dependencies
uv sync

# Set your API key (stored securely in system keyring)
api-client config set-key YOUR_API_KEY

# Fetch a user by ID
api-client user get 123

# List users with pagination
api-client user list --limit 10 --offset 0

# Search users
api-client user search "john"
```

## Project Structure

```
examples/api-client/
├── pyproject.toml           # Project configuration
├── README.md                # This file
├── src/api_client/
│   ├── __init__.py         # App definition and CLI export
│   ├── app.py              # Hive App instance
│   ├── services.py         # @service decorated API client
│   ├── commands.py         # Commands using the service
│   ├── credentials.py      # Credential management utilities
│   └── entities.py         # Data models (User, etc.)
└── tests/
    ├── __init__.py
    └── test_commands.py    # Tests with service mocking
```

## Service Pattern

Services in Hive are external dependencies that commands can use:

```python
from hive.core.decorators import service
from api_client.app import app

@service(app, credentials="keyring:api-client/api_key")
class JSONPlaceholderClient:
    \"\"\"Client for JSONPlaceholder API.\"\"\"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = "https://jsonplaceholder.typicode.com"

    async def get_user(self, user_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
```

## Commands Using Services

Commands access services through the execution context:

```python
from hive.core.decorators import command
from api_client.app import app

@command(app)
async def get_user(ctx, user_id: int) -> User:
    \"\"\"Fetch a user by ID from the API.\"\"\"
    client = ctx.services.json_placeholder
    data = await client.get_user(user_id)
    return User(**data)
```

## Credential Management

API keys are stored securely using the system keyring:

```python
from hive.core.decorators import command
from api_client.app import app
from api_client.credentials import store_api_key, get_api_key

@command(app)
async def set_key(ctx, api_key: str) -> str:
    \"\"\"Store API key in system keyring.\"\"\"
    store_api_key(api_key)
    return "API key stored successfully"
```

## Testing with Mocks

Use `unittest.mock` to mock services in tests:

```python
from unittest.mock import AsyncMock, MagicMock
from hive.testing import TestClient

async def test_get_user():
    # Create mock service
    mock_client = MagicMock()
    mock_client.get_user = AsyncMock(return_value={
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
    })

    async with TestClient(app, services={"json_placeholder": mock_client}) as client:
        result = await client.invoke("get_user", user_id=1)
        assert result.name == "John Doe"
        mock_client.get_user.assert_called_once_with(1)
```

## API Reference

### Commands

| Command | Description |
|---------|-------------|
| `config set-key KEY` | Store API key in keyring |
| `config show-key` | Display stored API key (masked) |
| `user get ID` | Fetch user by ID |
| `user list` | List users with pagination |
| `user search QUERY` | Search users by name |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_CLIENT_BASE_URL` | API base URL | https://jsonplaceholder.typicode.com |
| `API_CLIENT_TIMEOUT` | Request timeout (seconds) | 30 |

## Learn More

- [Hive Services Documentation](https://github.com/jaredmcfarland/hive)
- [httpx Documentation](https://www.python-httpx.org/)
- [keyring Documentation](https://keyring.readthedocs.io/)
