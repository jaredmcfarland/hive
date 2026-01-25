# Services

Services are lazily-instantiated external API clients with credential management. They provide a clean abstraction for integrating with external systems like GitHub, Slack, or any HTTP API.

## Basic Usage

Use the `@service` decorator to register a factory function:

```python
from hive import App, service
import httpx

app = App("myapp")

@service(app, credentials="keyring:github_token")
def github_client(credentials: str) -> httpx.Client:
    """GitHub API client."""
    return httpx.Client(
        base_url="https://api.github.com",
        headers={"Authorization": f"token {credentials}"},
    )
```

## Accessing Services

Access registered services through `ctx.services` in commands and queries:

```python
@command(app)
async def list_repos(ctx) -> list[dict]:
    """List GitHub repositories."""
    client = ctx.services.github_client
    response = client.get("/user/repos")
    response.raise_for_status()
    return response.json()
```

!!! tip "Lazy Loading"
    Services are instantiated on first access, not at startup. This means
    credentials are only resolved when actually needed.

## Credential Management

### Keyring Storage

Store credentials securely in the system keyring:

```python
@service(app, credentials="keyring:github_token")
def github_client(credentials: str) -> httpx.Client:
    """Uses system keyring for credential storage."""
    ...
```

Set the credential using the CLI:

```bash
hive credentials set github_token
# Prompts for the token securely
```

### Environment Variables

Read credentials from environment variables:

```python
@service(app, credentials="env:GITHUB_TOKEN")
def github_client(credentials: str) -> httpx.Client:
    """Uses GITHUB_TOKEN environment variable."""
    ...
```

### Fallback Behavior

If no `credentials` parameter is specified, Hive looks for `HIVE_{SERVICE}_CREDENTIAL`:

```python
@service(app)
def slack_client(credentials: str) -> httpx.Client:
    """Uses HIVE_SLACK_CLIENT_CREDENTIAL by default."""
    ...
```

## Decorator Parameters

### credentials

Specify the credential source:

```python
# System keyring
@service(app, credentials="keyring:api_key")
def my_service(credentials: str) -> Client:
    ...

# Environment variable
@service(app, credentials="env:MY_API_KEY")
def my_service(credentials: str) -> Client:
    ...
```

### name

Override the service name (defaults to function name):

```python
@service(app, name="github", credentials="keyring:github_token")
def create_github_client(credentials: str) -> httpx.Client:
    """Accessed as ctx.services.github"""
    ...
```

### cleanup

Provide a cleanup function for resource management:

```python
@service(
    app,
    credentials="keyring:db_password",
    cleanup=lambda client: client.close()
)
def database_client(credentials: str) -> DatabaseClient:
    """Client with automatic cleanup on context exit."""
    return DatabaseClient(password=credentials)
```

Async cleanup functions are also supported:

```python
async def close_client(client: AsyncClient) -> None:
    await client.aclose()

@service(app, credentials="keyring:api_key", cleanup=close_client)
def async_api_client(credentials: str) -> AsyncClient:
    """Async client with async cleanup."""
    ...
```

## Common Patterns

### HTTP API Client

```python
import httpx

@service(app, credentials="keyring:openai_key")
def openai_client(credentials: str) -> httpx.Client:
    """OpenAI API client."""
    return httpx.Client(
        base_url="https://api.openai.com/v1",
        headers={"Authorization": f"Bearer {credentials}"},
        timeout=30.0,
    )

@command(app)
async def generate(ctx, prompt: str) -> str:
    """Generate text with OpenAI."""
    client = ctx.services.openai_client
    response = client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
```

### Database Connection

```python
import asyncpg

@service(
    app,
    credentials="keyring:postgres_url",
    cleanup=lambda pool: pool.close()
)
def postgres_pool(credentials: str) -> asyncpg.Pool:
    """PostgreSQL connection pool."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        asyncpg.create_pool(credentials)
    )
```

### SDK Client

```python
from slack_sdk import WebClient

@service(app, credentials="keyring:slack_token")
def slack_client(credentials: str) -> WebClient:
    """Slack SDK client."""
    return WebClient(token=credentials)

@command(app)
async def send_message(ctx, channel: str, message: str) -> dict:
    """Send a Slack message."""
    client = ctx.services.slack_client
    response = client.chat_postMessage(channel=channel, text=message)
    return response.data
```

## Error Handling

Handle credential errors gracefully:

```python
from hive.errors import CredentialError

@command(app)
async def sync_issues(ctx) -> int:
    """Sync issues from GitHub."""
    try:
        client = ctx.services.github_client
    except CredentialError:
        ctx.output.error("GitHub credentials not configured")
        ctx.output.info("Run: hive credentials set github_token")
        raise CommandError("Missing credentials", exit_code=77)

    response = client.get("/repos/owner/repo/issues")
    ...
```

!!! warning "Security"
    Never log or display credential values. Hive automatically masks
    credentials in error messages and stack traces.

## Testing Services

Mock services in tests:

```python
from unittest.mock import MagicMock
from hive.testing import MockExecutionContext

async def test_list_repos():
    async with MockExecutionContext() as ctx:
        # Create mock client
        mock_client = MagicMock()
        mock_client.get.return_value.json.return_value = [
            {"name": "repo1"},
            {"name": "repo2"},
        ]

        # Inject mock service
        ctx.services.github_client = mock_client

        # Execute command
        repos = await list_repos(ctx)

        # Verify
        assert len(repos) == 2
        mock_client.get.assert_called_once_with("/user/repos")
```

## Best Practices

!!! success "Do"
    - Use keyring for sensitive credentials in production
    - Provide cleanup functions for resources that need closing
    - Handle `CredentialError` gracefully with user-friendly messages
    - Document expected credential format in docstrings
    - Use environment variables in CI/CD environments

!!! failure "Don't"
    - Hardcode credentials in source code
    - Log or display credential values
    - Create services with side effects in the factory function
    - Assume credentials are always available
