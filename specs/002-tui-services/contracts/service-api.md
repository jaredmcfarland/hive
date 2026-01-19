# Service API Contract

**Feature**: 002-tui-services
**Version**: 1.0.0

## @service Decorator

### Signature

```python
def service(
    app: App,
    *,
    credentials: str | None = None,
    name: str | None = None,
    cleanup: Callable[[Any], None] | None = None,
) -> Callable[[Callable[[str], T]], Callable[[str], T]]
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `App` | required | Application instance |
| `credentials` | `str \| None` | `None` | Credential source pattern |
| `name` | `str \| None` | `None` | Override service name (defaults to function name) |
| `cleanup` | `Callable \| None` | `None` | Cleanup function called on context exit |

### Credential Patterns

| Pattern | Resolution |
|---------|------------|
| `keyring:github` | `keyring.get_password("hive", "github")` |
| `env:GITHUB_TOKEN` | `os.environ["GITHUB_TOKEN"]` |
| `None` | No credentials passed to factory |

### Behavior

1. Registers service factory with application registry
2. Factory is NOT called at decoration time (lazy instantiation)
3. Factory receives resolved credentials as first argument
4. Returns decorated function unchanged

### Example

```python
@service(app, credentials="keyring:github")
def github_client(token: str) -> httpx.AsyncClient:
    """GitHub API client."""
    return httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={"Authorization": f"Bearer {token}"}
    )

# With cleanup
@service(app, credentials="keyring:db", cleanup=lambda c: c.close())
def database_pool(connection_string: str) -> ConnectionPool:
    """Database connection pool."""
    return ConnectionPool(connection_string)
```

## Service Access

### Via ExecutionContext

```python
@command(app)
async def fetch_repos(ctx) -> list[Repo]:
    """Fetch repositories from GitHub."""
    client = ctx.services.github_client  # Lazy instantiation
    response = await client.get("/user/repos")
    return [Repo(**r) for r in response.json()]
```

### Service Proxy Behavior

```
┌──────────────────┐
│ ctx.services.foo │
└────────┬─────────┘
         ▼
┌──────────────────┐     ┌───────────────┐
│ In cache?        │─Yes─►│ Return cached │
└────────┬─────────┘     └───────────────┘
         │ No
         ▼
┌──────────────────┐
│ Resolve creds    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Call factory     │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Cache & return   │
└──────────────────┘
```

### Credential Resolution Chain

```
1. keyring.get_password("hive", key)
   ├── Found → Use credential
   └── Not found → Continue

2. os.environ.get(f"{KEY}_API_KEY")
   ├── Found → Use credential
   └── Not found → Continue

3. os.environ.get(f"{KEY}_TOKEN")
   ├── Found → Use credential
   └── Not found → Continue

4. In TUI mode?
   ├── Yes → Show credential prompt modal
   └── No → Raise CredentialError
```

## Service Lifecycle

### Instantiation

- Services are instantiated **lazily** on first access
- Same instance returned for all accesses within one context
- Thread-safe instantiation via lock

### Cleanup

```python
async with ExecutionContext(app) as ctx:
    # Services used here
    client = ctx.services.github_client
    await do_work(client)
# Cleanup called automatically for all instantiated services
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Credentials not found | Raise `CredentialError` with helpful message |
| Factory raises | Propagate exception, do not cache |
| Cleanup raises | Log warning, continue cleanup of other services |

## Security Constraints

### MUST

- Credentials MUST be retrieved at instantiation, not stored
- Credentials MUST NOT appear in logs or error messages
- Credentials MUST be masked in any debug output

### MUST NOT

- Service proxy MUST NOT expose credential values
- Stack traces MUST NOT include credential values
- Serialized contexts MUST NOT include credentials
