# DevHelm Python SDK

Typed Python client for the [DevHelm](https://devhelm.io) API: uptime monitors,
browser and multi-step API checks, runs, incidents, alerting and status pages.
`Devhelm` blocks; `AsyncDevhelm` is the same surface for asyncio.

## Installation

```bash
pip install devhelm
```

## Code checks in five calls

```python
from devhelm import Devhelm

devhelm = Devhelm()                              # token from DEVHELM_API_TOKEN
m = devhelm.monitors.create(name="Checkout", type="BROWSER", environment="production",
                            code="./checkout.spec.ts", frequency_seconds=600, regions=["us-east"])
draft = devhelm.monitors.revisions.create(m.id, code="./checkout.spec.ts").revision
run = devhelm.monitors.revisions.test(m.id, draft.id, wait=True)
if run.outcome == "passed":
    devhelm.monitors.publish(m.id, revision_id=draft.id, expected_live_revision_id=m.live_revision_id)
```

- **Create** uploads the code and makes revision 1 live at once, and the
  monitor runs right away. **Change** code as a draft, **test** it in the
  monitor's own environment, then **publish**. `monitors.update(id, code=...)`
  is the one-call path: live, untested.
- `environment` takes a slug or an id. Request fields take snake_case or the
  wire's camelCase; unknown fields are refused before any call.
- `wait=True` (or `devhelm.runs.wait(run_id)`) follows the run's event stream,
  falls back to polling, and returns the finished `RunDto` whatever its
  outcome. Only `WaitTimeoutError` is raised (the run keeps going).
  Check `run.flaky` rather than parsing outcome strings.

### The `code` argument

| Form | Example | What is sent |
|---|---|---|
| A path | `code="./checks/checkout.spec.ts"` | The entry file's directory, recursively |
| Entry + include globs | `code={"entrypoint": "checks/checkout.spec.ts", "include": ["fixtures/order.json"]}` | The entry file's directory, plus the files the globs match (fixtures, data nothing imports) |
| In memory | `code={"entrypoint": "a.spec.ts", "files": {"a.spec.ts": src, "data.json": raw}, "include": ["data.json"]}` | Exactly those files; nothing is read from disk |

The SDK does not parse JavaScript and needs no Node: it uploads the file set
and the server resolves the import closure. The bundle root is `root=` when
given, else the nearest directory with `.git`, else the entry file's
directory. The default set leaves out `node_modules/`, `.git/`, `dist/`,
`build/`, `coverage/`, `*.map`, dotfiles (`.env*` included) and whatever
`.devhelmignore` (gitignore syntax) matches. `include` names files that must
ship although nothing imports them; the server keeps them in the closure.
`auth.setup.ts` next to the entry file is always sent. Symlinks are refused; a set is capped at 256 files and
5 MB. `devhelm.bundle_digest(files)` computes the same D-12 digest as the
server and the other SDKs.

### More of the lifecycle

```python
# Validate a file before any monitor exists (billed validation run, no monitor)
tried = devhelm.monitors.test_adhoc(type="BROWSER", environment="staging",
                                    code="./checkout.spec.ts", wait=True)

# Fan out to several regions now. Never alerts unless signal=True.
result = devhelm.monitors.trigger(m.id, regions=["us-east", "eu-west"], wait=True)
for r in result.runs:
    print(r.region, r.outcome, r.url)

# Roll back, list and diff revisions
devhelm.monitors.rollback(m.id, reason="checkout broke on 2026.11")
drafts = devhelm.monitors.revisions.list(m.id, state=["draft", "tested_failed"])
diff = devhelm.monitors.revisions.diff(m.id, draft.id)       # against the live revision

# Evidence
page = devhelm.runs.list(monitor_id=m.id, outcome="failed", limit=25)
cases = devhelm.runs.steps(run.id)
png = devhelm.runs.artifacts.download(devhelm.runs.artifacts.list(run.id)[0].id)

# Secrets: values are written per environment and never read back
devhelm.secrets.values.set("CARD_TOKEN", environment="production", value=token)
```

### asyncio

```python
from devhelm import AsyncDevhelm

async with AsyncDevhelm() as devhelm:
    run = await devhelm.monitors.test_adhoc(type="MULTI_STEP_API", environment="staging",
                                            code={"entrypoint": "orders.spec.ts",
                                                  "files": {"orders.spec.ts": src}},
                                            wait=True)
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

# Inbound testing. `webhooks` stays outbound alert delivery.
inbox = client.inboxes.create(name="stripe")
event = inbox.wait(timeout_ms=30_000, http={"method": "POST"})
payment = event.json()
raw = event.raw()

to = client.email.address(label="signup")
message = to.wait(timeout_ms=60_000, subject_contains="code")
code = message.otp[0].value if message.otp else None
pdf = message.attachments[0].bytes() if message.attachments else None

# Pause / resume
client.monitors.pause(monitor.id)
client.monitors.resume(monitor.id)

# Delete
client.monitors.delete(monitor.id)
```

## Testing a monitor

Neither method records the result against the monitor's health.

```python
# Browser and multi-step API: a validation run in the monitor's environment
run = client.monitors.test(monitor.id, region="eu-west", wait=True)
print(run.outcome, run.url)

# HTTP, TCP, DNS, ICMP, MCP: run once through the probe and return the result
result = client.monitors.probe(monitor.id)
print(result.passed, result.status_code)
```

`monitors.test()` returns `MonitorTestOutcome` (narrow it with
`devhelm.is_run`). On an uptime monitor it still returns the probe result,
with a one-time deprecation warning, until 2027-01-31; after that it raises
`ValidationError` with code `USE_PROBE`. `monitors.probe()` on a code monitor raises
`DevhelmMonitorTestQueuedError` with the queued run on `err.run`.

## Configuration

```python
from devhelm import Devhelm

client = Devhelm(
    token="your-api-token",            # or DEVHELM_API_TOKEN, or the CLI's current context
    org_id="1",                        # optional — see notes below
    workspace_id="1",                  # optional — see notes below
    base_url="https://api.devhelm.io", # optional; DEVHELM_API_URL overrides the default
    max_attempts=5,                    # retries for 429 / 503 / retryable 409
)
```

Environment variables are used as fallbacks when constructor arguments are not provided:

| Parameter      | Required | Env Variable           | Notes                                                                                                    |
| -------------- | -------- | ---------------------- | -------------------------------------------------------------------------------------------------------- |
| `token`        | Yes      | `DEVHELM_API_TOKEN`    | API key. Falls back to the current context in `~/.devhelm/contexts.json` (`devhelm auth login`). None at all raises `ValidationError` `NO_TOKEN`. |
| `base_url`     | No       | `DEVHELM_API_URL`      | Defaults to `https://api.devhelm.io`.                                                                    |
| `org_id`       | No       | `DEVHELM_ORG_ID`       | Auto-resolved if your token is scoped to one org. Required only when the token has access to multiple.   |
| `workspace_id` | No       | `DEVHELM_WORKSPACE_ID` | Auto-resolved if your token is scoped to one workspace. Required only when the token spans multiple.     |

## Resources

The client exposes the following resource modules:

| Resource                | Description                      |
| ----------------------- | -------------------------------- |
| `client.monitors`       | Uptime monitors and browser / multi-step API checks, with `revisions`, `versions`, `history`, `trash`, `secret_requests`, `sessions` |
| `client.runs`           | Runs, `wait`, steps, console, network, traces, diffs, `artifacts` |
| `client.bundles`        | Upload check files (`create`) and check imports (`check`) |
| `client.runtimes`       | Runtime profiles (Node, Playwright, package catalog) |
| `client.account`        | Plan entitlements and synthetics usage |
| `client.audit`          | Audit log |
| `client.incidents`      | Manual and auto-detected incidents |
| `client.alert_channels` | Slack, email, webhook, and other alert channels |
| `client.notification_policies` | Routing rules for alerts   |
| `client.environments`   | Environment grouping (prod, staging, etc.) |
| `client.secrets`        | Encrypted secrets for monitor auth |
| `client.tags`           | Organize monitors with tags      |
| `client.resource_groups`| Logical resource groups           |
| `client.webhooks`       | Outgoing webhook endpoints        |
| `client.inboxes`        | Inbound HTTP capture URLs         |
| `client.email`          | Inbound mailboxes and custom domains |
| `client.api_keys`       | API key management                |
| `client.dependencies`   | Service dependency tracking       |
| `client.deploy_lock`    | Deploy lock for safe deployments  |
| `client.services`       | Status Data catalog: vendor services, components, incidents, uptime |
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

# Cursor pagination (runs, monitor history)
runs = client.runs.list(limit=50)
print(runs.data, runs.next_cursor, runs.has_more)
everything = client.runs.list_all(monitor_id=monitor_id)
```

## Error Handling

Every refusal carries the API's `ErrorResponse` envelope, and the SDK raises
one class per `category` (never chosen from the HTTP status):

| category | class | | category | class |
|---|---|---|---|---|
| `validation` | `ValidationError` | | `conflict` | `ConflictError` |
| `blocked` | `BlockedError` | | `confirmation_required` | `ConfirmationRequiredError` |
| `auth` | `AuthError` | | `not_found` | `NotFoundError` |
| `permission` | `PermissionError` | | `gone` | `GoneError` |
| `ownership` | `OwnershipError` | | `platform` | `PlatformError` |
| `plan` | `PlanLimitError` | | `rate_limit` | `RateLimitError` |
| `quota` | `QuotaError` | | `transport` (client-side) | `TransportError` |

All extend `DevhelmApiError` (except `TransportError`) and `DevhelmError`, and
expose every envelope field in snake_case: `status`, `code`, `category`,
`retryable`, `message`, `request_id`, `errors`, `retry_after_seconds`,
`resource`, `used`, `limit`, `resets_at`, `plan`, `upgrade_url`, `can_raise`,
`owner`, `required`, `have`, `reason`, `next`, `details`, `expired_at`,
`policy`. Errors the SDK raises itself (`NO_TOKEN`, `USE_PROBE`,
`BUNDLE_DIGEST_MISMATCH`, …) use the same classes with `status == 0`.
`WaitTimeoutError` carries `run_id` and `phase`. `DevhelmValidationError` is
a local request or response shape failure (pydantic `errors`).

The pre-category names still work: `DevhelmAuthError` (401/403),
`DevhelmNotFoundError`, `DevhelmConflictError`, `DevhelmRateLimitError`,
`DevhelmServerError` are base classes of the category classes.
`from devhelm import errors` avoids shadowing Python's own `PermissionError`.

```python
from devhelm import Devhelm, errors

devhelm = Devhelm()
try:
    devhelm.monitors.trigger(monitor_id)
except errors.QuotaError as e:
    print(f"{e.resource}: {e.used}/{e.limit}, resumes {e.resets_at}")
except errors.PermissionError as e:
    print(f"missing scope {e.required} (request {e.request_id})")
```

Retries: 429, 503 and retryable 409s are retried up to 5 times honouring
`Retry-After`. Every POST carries an `Idempotency-Key` that is reused only for
those retries, so a retried POST replays instead of running twice. Every call
sends `X-DevHelm-Client: sdk-python/<version>`.

## Deprecations

Removed on 2027-01-31; each warns once per process:

| Deprecated | Use |
|---|---|
| `monitors.versions(id)` | `monitors.versions.list(id)` |
| `monitors.results(id)` | `monitors.history.list(id)` |
| `monitors.test_run(id)` | `monitors.test(id)` |
| `monitors.test(id)` on an uptime monitor (returns the probe result) | `monitors.probe(id)`; from 2027-01-31 `test()` raises `USE_PROBE` there |

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

# Regenerate the sync client after editing src/devhelm/_async
make unasync
```

`src/devhelm/_async/` is the source of the resources, transport, pagination
and `wait`. `scripts/unasync.py` generates the blocking client from it
(`src/devhelm/resources/`, `src/devhelm/_sync/`, `src/devhelm/client.py`);
`make lint` fails when the generated files are stale.

## License

MIT
