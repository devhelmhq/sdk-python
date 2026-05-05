# DevHelm Python SDK

Typed Python client for the [DevHelm](https://devhelm.io) monitoring API — monitors, incidents, alerting, and more.

## Installation

```bash
pip install devhelm
```

## Quick Start

```python
from devhelm import Devhelm

client = Devhelm(token="your-api-token")

# List all monitors
monitors = client.monitors.list()
for m in monitors:
    print(f"{m.name} — {m.type}")

# Create a monitor
monitor = client.monitors.create({
    "name": "My API Health",
    "type": "HTTP",
    "config": {"url": "https://api.example.com/health", "method": "GET"},
    "frequencySeconds": 60,
    "regions": ["us-east"],
    # `managedBy` records who reconciles drift on this resource. Use
    # "DASHBOARD" (the default for one-off SDK scripts), "CLI" if the
    # monitor lives in a `devhelm.yml` you re-deploy, or "TERRAFORM"
    # if it lives in `.tf` you re-apply.
    "managedBy": "DASHBOARD",
})

# Get a single monitor
monitor = client.monitors.get(monitor.id)

# Pause / resume
client.monitors.pause(monitor.id)
client.monitors.resume(monitor.id)

# Delete
client.monitors.delete(monitor.id)
```

## Configuration

```python
from devhelm import Devhelm

client = Devhelm(
    token="your-api-token",            # required (or DEVHELM_API_TOKEN env var)
    org_id="1",                        # optional — see notes below
    workspace_id="1",                  # optional — see notes below
    base_url="https://api.devhelm.io", # optional, defaults to production
)
```

Environment variables are used as fallbacks when constructor arguments are not provided:

| Parameter      | Required | Env Variable           | Notes                                                                                                    |
| -------------- | -------- | ---------------------- | -------------------------------------------------------------------------------------------------------- |
| `token`        | Yes      | `DEVHELM_API_TOKEN`    | Personal or workspace API token.                                                                         |
| `org_id`       | No       | `DEVHELM_ORG_ID`       | Auto-resolved if your token is scoped to one org. Required only when the token has access to multiple.   |
| `workspace_id` | No       | `DEVHELM_WORKSPACE_ID` | Auto-resolved if your token is scoped to one workspace. Required only when the token spans multiple.     |

## Resources

The client exposes the following resource modules:

| Resource                | Description                      |
| ----------------------- | -------------------------------- |
| `client.monitors`       | HTTP, DNS, TCP, ICMP, MCP, and Heartbeat monitors |
| `client.incidents`      | Manual and auto-detected incidents |
| `client.alert_channels` | Slack, email, webhook, and other alert channels |
| `client.notification_policies` | Routing rules for alerts   |
| `client.environments`   | Environment grouping (prod, staging, etc.) |
| `client.secrets`        | Encrypted secrets for monitor auth |
| `client.tags`           | Organize monitors with tags      |
| `client.resource_groups`| Logical resource groups           |
| `client.webhooks`       | Outgoing webhook endpoints        |
| `client.api_keys`       | API key management                |
| `client.dependencies`   | Service dependency tracking       |
| `client.deploy_lock`    | Deploy lock for safe deployments  |
| `client.status`         | Dashboard overview                |

## Pagination

List methods auto-paginate by default. For manual page control:

```python
# Auto-paginate (fetches all pages)
all_monitors = client.monitors.list()

# Manual page control
page = client.monitors.list_page(page=0, size=20)
print(page.data)       # list of monitors
print(page.has_next)   # True if more pages
print(page.has_prev)   # True if previous page exists

# Cursor pagination (for check results)
results = client.monitors.results(monitor_id, limit=50)
print(results.data)
print(results.next_cursor)
print(results.has_more)
```

## Error Handling

The SDK raises three top-level error types (see
[`040-codegen-policies.md`](https://github.com/devhelmhq/mono/blob/main/cowork/design/040-codegen-policies.md)):

- `DevhelmValidationError` — local request/response shape validation failed.
- `DevhelmApiError` — the API returned a non-2xx status. Subclassed by HTTP
  class for ergonomics: `DevhelmAuthError` (401/403), `DevhelmNotFoundError`
  (404), `DevhelmConflictError` (409), `DevhelmRateLimitError` (429),
  `DevhelmServerError` (5xx).
- `DevhelmTransportError` — the request never reached a server response
  (connection refused, timeout, TLS failure, etc.).

Every `DevhelmApiError` carries:

- `status` — the HTTP status code
- `code` — coarse machine-readable category (e.g. `NOT_FOUND`,
  `RATE_LIMITED`); switch on this, not the human-readable `message`
- `request_id` — the per-request id from the `X-Request-Id` response header;
  always include this in support tickets

```python
from devhelm import Devhelm, DevhelmAuthError, DevhelmError

client = Devhelm(token="bad-token")

try:
    client.monitors.list()
except DevhelmAuthError as e:
    print(f"Auth failed: {e.message} (HTTP {e.status}, request_id={e.request_id})")
except DevhelmError as e:
    print(f"API error [{e.code}]: {e.message}")
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
make test

# Lint + format check
make lint

# Type check
make typecheck

# Regenerate types from OpenAPI spec
make typegen
```

## License

MIT
