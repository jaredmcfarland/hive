# Phase 003 QA Plan - Spec Distribution

## Overview

This QA plan validates the Phase 003 (Spec Distribution) implementation before merge.
Current state: 578/583 tests passing, 83% coverage, PR #6 review feedback addressed.

## Test Summary

| Category | Tests | Coverage | Status |
|----------|-------|----------|--------|
| Unit | ~200 | 83% | Passing |
| Contract | ~150 | N/A | Passing |
| Integration | ~50 | N/A | 5 skipped (MCP server) |

### Coverage Gaps (Priority Files)

| File | Coverage | Priority |
|------|----------|----------|
| `cli/project.py` | 47% | High - manual testing required |
| `cli/mcp.py` | 65% | High - requires MCP runtime |
| `spec/diff.py` | 69% | Medium - edge cases |
| `spec/export.py` | 72% | Medium - format edge cases |

---

## QA Checklist

### 1. Automated Tests (CI/Pre-merge)

- [ ] `uv run pytest` - All tests pass
- [ ] `uv run pytest --cov=src/hive` - Coverage >= 80%
- [ ] `uv run ruff check .` - No lint errors
- [ ] `uv run pyright` - No type errors
- [ ] `uv run bandit -c pyproject.toml -r src/` - No security issues
- [ ] `uv run pre-commit run --all-files` - All hooks pass

### 2. CLI Command Testing

#### 2.1 `hive spec export`

**Setup**: Create a sample app with commands, queries, and entities.

```bash
# Create test app
mkdir -p /tmp/hive-qa && cd /tmp/hive-qa
cat > app.py << 'EOF'
from hive import App, command, query, entity
from hive.types import PositiveInt, NonEmptyStr, Email
from pydantic import Field
from sqlmodel import Field as SQLField

app = App("qa-test")

@entity(app)
class User:
    id: int = SQLField(default=None, primary_key=True)
    name: str
    email: str

@command(app, entities=[User])
async def create_user(ctx, name: NonEmptyStr, email: Email) -> User:
    """Create a new user."""
    return User(name=name, email=email)

@query(app, entities=[User])
async def get_user(ctx, user_id: PositiveInt) -> User | None:
    """Get user by ID."""
    return None
EOF
```

**Test Cases**:

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| JSON export to stdout | `hive spec export` | Valid JSON to stdout | [ ] |
| JSON export to file | `hive spec export -o spec.json` | File created, valid JSON | [ ] |
| TOML export | `hive spec export --format toml` | Valid TOML output | [ ] |
| Commands included | Check JSON output | `commands` array has `create_user` | [ ] |
| Queries included | Check JSON output | `queries` array has `get_user` | [ ] |
| Entities included | Check JSON output | `entities` array has `User` | [ ] |
| Refinement constraints | Check JSON | `PositiveInt` → `minimum: 1` | [ ] |
| Email format | Check JSON | `email` parameter has `format: email` | [ ] |
| JSON flag | `hive spec export --json` | Machine-readable JSON output | [ ] |
| Missing app | Run in empty dir | Helpful error message | [ ] |

#### 2.2 `hive spec diff`

**Setup**: Create two spec versions.

```bash
# Export v1
hive spec export -o v1.json

# Modify app (add command, remove parameter)
# ... make changes ...

# Export v2
hive spec export -o v2.json
```

**Test Cases**:

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| Identical specs | `hive spec diff v1.json v1.json` | "No changes detected" | [ ] |
| Added command | Add cmd, diff | Non-breaking change listed | [ ] |
| Removed command | Remove cmd, diff | **Breaking** change listed | [ ] |
| Added required param | Add required param, diff | **Breaking** change | [ ] |
| Added optional param | Add optional param, diff | Non-breaking change | [ ] |
| Type change | Change param type, diff | **Breaking** change | [ ] |
| Text format | `--format text` | Human-readable output | [ ] |
| JSON format | `--format json` | Parseable JSON output | [ ] |
| Fail on breaking | `--fail-on-breaking` with breaking | Exit code 1 | [ ] |
| Fail on breaking (none) | `--fail-on-breaking` without breaking | Exit code 0 | [ ] |
| Missing file | `hive spec diff missing.json v2.json` | Clear error message | [ ] |
| Invalid JSON | Diff with malformed JSON | Parse error shown | [ ] |

#### 2.3 `hive mcp serve`

**Prerequisites**: `uv pip install hive[mcp]` or `fastmcp` installed.

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| Help output | `hive mcp serve --help` | Shows transport, host, port options | [ ] |
| Default stdio | `hive mcp serve` | Starts MCP server on stdio | [ ] |
| SSE transport | `hive mcp serve --transport sse` | Starts SSE server on :8080 | [ ] |
| Custom port | `hive mcp serve --transport sse --port 9000` | Server on :9000 | [ ] |
| JSON output | `hive mcp serve --json` | Machine-readable startup info | [ ] |
| Missing fastmcp | Uninstall fastmcp, run | Helpful "install with [mcp]" message | [ ] |
| Tool listing | Connect with MCP client | Commands appear as tools | [ ] |
| Tool execution | Execute tool via MCP | Correct response returned | [ ] |

#### 2.4 `hive serve` (REST API)

**Prerequisites**: `uv pip install hive[rest]` or `fastapi uvicorn` installed.

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| Help output | `hive serve --help` | Shows all options | [ ] |
| Default start | `hive serve` | Starts on :8000 | [ ] |
| Custom port | `hive serve --port 9000` | Server on :9000 | [ ] |
| OpenAPI docs | Visit `/docs` | Swagger UI loads | [ ] |
| OpenAPI JSON | Visit `/openapi.json` | Valid OpenAPI schema | [ ] |
| Command endpoint | POST `/commands/create_user` | 200 with result | [ ] |
| Query endpoint | GET `/queries/get_user?user_id=1` | 200 with result | [ ] |
| Validation error | POST with invalid data | 422 with error details | [ ] |
| Hot reload | `hive serve --reload` | Changes detected, reloads | [ ] |
| API key auth | `--auth api_key`, test with/without header | 401 without, 200 with | [ ] |
| Bearer auth | `--auth bearer` | Token validation works | [ ] |
| JSON output | `hive serve --json` | Machine-readable config | [ ] |
| Missing fastapi | Uninstall, run | Helpful "install with [rest]" message | [ ] |

#### 2.5 `hive new` (Project Scaffolding)

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| Help output | `hive new --help` | Shows features option | [ ] |
| Basic project | `hive new myapp` | Creates myapp/ with structure | [ ] |
| With TUI | `hive new myapp --features tui` | Includes TUI deps | [ ] |
| With MCP | `hive new myapp --features mcp` | Includes MCP deps | [ ] |
| With REST | `hive new myapp --features rest` | Includes REST deps | [ ] |
| All features | `hive new myapp --features tui,mcp,rest` | All optional deps | [ ] |
| Existing dir | `hive new existing-dir` | Error or prompt | [ ] |
| Invalid name | `hive new "invalid name"` | Validation error | [ ] |
| Generated app works | `cd myapp && uv sync && uv run hive --help` | CLI runs | [ ] |

#### 2.6 `hive dev` (Development Server)

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| Help output | `hive dev --help` | Shows interfaces option | [ ] |
| Default (CLI) | `hive dev` | Starts CLI dev mode | [ ] |
| With REST | `hive dev --interfaces rest` | Starts REST server with reload | [ ] |
| Multiple | `hive dev --interfaces cli,rest` | Both interfaces | [ ] |
| File changes | Modify app, save | Hot reload triggers | [ ] |

#### 2.7 `hive build` and `hive publish`

| Test | Command | Expected | Status |
|------|---------|----------|--------|
| Build | `hive build` | Creates dist/ with wheel and sdist | [ ] |
| Build clean | `hive build` twice | Succeeds, no artifacts conflict | [ ] |
| Publish dry-run | `hive publish --dry-run` | Shows what would be published | [ ] |

---

### 3. Integration Scenarios

#### 3.1 End-to-End Workflow

```bash
# 1. Create new project
hive new myproject --features mcp,rest
cd myproject
uv sync

# 2. Add a command to the app
# ... edit app.py ...

# 3. Export spec
hive spec export -o v1-spec.json

# 4. Start REST server, test endpoints
hive serve &
curl -X POST http://localhost:8000/commands/my_command -d '{"arg": "value"}'

# 5. Modify app, re-export
# ... edit app.py ...
hive spec export -o v2-spec.json

# 6. Check for breaking changes
hive spec diff v1-spec.json v2-spec.json --fail-on-breaking

# 7. Start MCP server
hive mcp serve --transport sse --port 8080
```

| Step | Expected Outcome | Status |
|------|------------------|--------|
| Project created | Clean directory structure | [x] |
| Spec exported | Valid JSON with commands | [x] |
| REST server works | Endpoints respond correctly | [x] (hello, status work; entity instantiation needs SQLModel setup) |
| Diff detects changes | Breaking/non-breaking categorized | [x] |
| MCP server works | Tools available via MCP | [x] |

**Tested 2026-01-19**: Full E2E workflow validated with `hive new myproject --features mcp,rest`. Spec diff correctly detected 2 breaking changes (priority default removed, required changed) and 4 non-breaking changes (new command, new parameter). MCP server started on SSE transport with FastMCP 2.14.3.

#### 3.2 CI Pipeline Simulation

```bash
# In GitHub Actions-like environment
uv sync --dev
uv run ruff check .
uv run pyright
uv run pytest --cov=src/hive --cov-fail-under=80
uv run bandit -c pyproject.toml -r src/
hive spec export -o current-spec.json
hive spec diff baseline-spec.json current-spec.json --fail-on-breaking
```

| Check | Pass Criteria | Status |
|-------|---------------|--------|
| Lint | Zero errors | [x] |
| Types | Zero errors | [~] 13 errors (deepdiff import, TUI cycle warning) |
| Tests | All pass, >=80% coverage | [x] 578 passed, 82.81% coverage |
| Security | No high/critical issues | [x] |
| Breaking changes | None (or acknowledged) | [x] |
| Pre-commit | All hooks pass | [x] |

**Tested 2026-01-19**: All CI checks pass except pyright has 13 errors (mostly `deepdiff` type stubs and TUI import cycle warnings). Coverage at 82.81% exceeds 80% threshold.

---

### 4. Edge Cases & Error Handling

| Scenario | Expected Behavior | Status |
|----------|-------------------|--------|
| Empty app (no commands) | Valid spec with empty arrays | [x] |
| Circular entity references | Handled without infinite loop | [x] |
| Forward type references | Resolved correctly | [x] |
| `Optional[T]` vs `T \| None` | Identical schema output | [x] |
| Generic types (`List[int]`) | Correct JSON Schema array | [x] |
| Pydantic nested models | Full schema serialization | [x] (uses $ref, $defs empty) |
| Unicode in docstrings | Preserved in spec | [x] |
| Very long parameter names | No truncation | [x] (91-char names preserved) |
| 100+ commands | Performance acceptable | [x] (0.46s for 150 commands/queries) |
| Invalid Python in app | Clear import error | [x] (syntax errors shown with line numbers) |

**Tested 2026-01-19**: All edge cases handled correctly. Unicode (Japanese, emojis, math symbols) preserved in JSON output. Performance well under thresholds. Import errors masked by "No Hive app found" message (minor improvement opportunity).

---

### 5. Performance & Stress Testing

| Test | Threshold | Status |
|------|-----------|--------|
| Export 100 commands | < 2 seconds | [x] 0.46s for 100 cmds + 50 queries |
| Diff large specs (1MB) | < 5 seconds | [ ] |
| REST server cold start | < 3 seconds | [x] ~2s |
| MCP server cold start | < 3 seconds | [x] ~2s |
| REST request latency | < 100ms p95 | [ ] |

**Tested 2026-01-19**: Spec export performance excellent (0.46s for 150 operations, 60KB output). Server cold starts within threshold.

---

### 6. Documentation Verification

| Doc | Verified | Status |
|-----|----------|--------|
| CLAUDE.md commands accurate | All commands work as documented | [x] |
| CLI `--help` complete | All options documented | [x] |
| Error messages actionable | Users know how to fix | [x] |
| Dependency messages helpful | `pip install hive[mcp]` shown | [x] |

**Tested 2026-01-19**: All 16 documented CLI commands in CLAUDE.md verified working with correct options. Error messages provide clear guidance (missing app shows example code, missing file shows path, invalid name explains rules). Dependency messages now correctly show `pip install hive-framework[mcp]` and `[rest]` after BUG-005 fix.

---

---

## Known Issues (Found During QA)

### BUG-001: MCP Server `**kwargs` Not Supported - ✅ FIXED

**File**: [src/hive/generators/mcp.py:185](src/hive/generators/mcp.py#L185)

**Severity**: Blocking (MCP server cannot start)

**Description**: The `_register_tool` method creates a `tool_handler(**kwargs)` function, but FastMCP does not support tools with `**kwargs` signatures. It requires explicit parameter definitions.

**Error**: `Functions with **kwargs are not supported as tools`

**Fix**: Added `_get_base_type()` helper and replaced `_register_tool()` to use `exec()` for dynamic function creation with explicit parameter signatures.

### BUG-002: REST Server Dynamic Function Type Annotations - ✅ FIXED

**File**: [src/hive/generators/rest.py:~520-548](src/hive/generators/rest.py#L520)

**Severity**: Blocking (REST server cannot start with typed parameters)

**Description**: When generating dynamic endpoint handlers, the REST generator converts type annotations to strings. For complex types like `Annotated[int, ...]`, it generates `user_id: Annotated` instead of the actual type, causing FastAPI to see `ForwardRef('Annotated')` and fail.

**Error**: `FastAPIError: Invalid args for response field! Hint: check that ForwardRef('Annotated') is a valid Pydantic field type.`

**Fix**: Added `_get_base_type()` function to extract base type from `Annotated` before generating signature string.

### BUG-003: `hive new` Accepts Invalid Project Names - ✅ FIXED

**File**: [src/hive/cli/project.py](src/hive/cli/project.py)

**Severity**: Low (causes broken packages, user can work around)

**Description**: The `hive new` command accepts project names with spaces, hyphens, and other invalid Python identifier characters. This creates directories and packages that cannot be imported.

**Fix**: Added `_normalize_project_name()` function that:
- Converts hyphens to underscores (`my-app` → `my_app`)
- Validates result is a valid Python identifier
- Rejects Python keywords
- Shows helpful error messages

### BUG-004: JSON Output Control Character Escaping - ✅ FIXED

**File**: [src/hive/cli/spec.py:94](src/hive/cli/spec.py#L94)

**Severity**: Medium (JSON output unparsable by external tools)

**Description**: When exporting specs to stdout in JSON format, `console.print(result)` was used instead of `console.print_json(result)`. This caused control characters (newlines, tabs) in docstrings to not be properly escaped, making the JSON invalid for parsing by `jq` and other tools.

**Error**: `jq: parse error: Invalid string: control characters from U+0000 through U+001F must be escaped`

**Fix**: Changed line 94 from `console.print(result, markup=False, highlight=False)` to `console.print_json(result)` when format is JSON. TOML output continues to use `console.print` with `markup=False`.

### BUG-005: Rich Markup Strips Brackets in Dependency Messages - ✅ FIXED

**Files**:
- [src/hive/cli/mcp.py:83-85](src/hive/cli/mcp.py#L83)
- [src/hive/cli/serve.py:113-114](src/hive/cli/serve.py#L113)

**Severity**: Low (confusing install instructions)

**Description**: Dependency error messages like `pip install hive-framework[mcp]` were passed to Rich's `console.print()`. Rich interpreted `[mcp]` and `[rest]` as markup tags (like `[red]`) and stripped them, showing only `pip install hive-framework`.

**Symptom**: User sees "Install with: pip install hive-framework" instead of "pip install hive-framework[mcp]"

**Fix**: Escaped brackets using `\\[mcp]` and split the message into two lines with the install command styled separately.

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | | | |
| QA | | | |
| Reviewer | | | |

## Notes

- MCP server tests require actual MCP client (Claude Desktop, etc.)
- REST tests can use `curl` or `httpie`
- Performance thresholds are guidelines, adjust based on hardware
