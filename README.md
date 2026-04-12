# DevHelm Python SDK

Typed Python client for the [DevHelm](https://devhelm.io) monitoring API — monitors, incidents, alerting, and more.

## Installation

```bash
pip install devhelm
```

## Quick Start

```python
from devhelm import Devhelm

client = Devhelm(
    token="your-api-token",
    org_id="your-org-id",
    workspace_id="your-workspace-id",
)

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
    token="your-api-token",           # required (or DEVHELM_API_TOKEN env var)
    org_id="1",                        # required (or DEVHELM_ORG_ID env var)
    workspace_id="1",                  # required (or DEVHELM_WORKSPACE_ID env var)
    base_url="https://api.devhelm.io", # optional, defaults to production
)
```

Environment variables are used as fallbacks when constructor arguments are not provided:

| Parameter      | Env Variable            |
| -------------- | ----------------------- |
| `token`        | `DEVHELM_API_TOKEN`     |
| `org_id`       | `DEVHELM_ORG_ID`        |
| `workspace_id` | `DEVHELM_WORKSPACE_ID`  |

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

```python
from devhelm import Devhelm, DevhelmError, AuthError

client = Devhelm(token="bad-token", org_id="1", workspace_id="1")

try:
    client.monitors.list()
except AuthError as e:
    print(f"Auth failed: {e.message} (HTTP {e.status})")
except DevhelmError as e:
    print(f"API error [{e.code}]: {e.message}")
```

Error codes: `AUTH`, `NOT_FOUND`, `CONFLICT`, `VALIDATION`, `API`.

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
