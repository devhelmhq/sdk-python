# Changelog

## 1.13.0

Code checks (browser and multi-step API) across the whole lifecycle, an
asyncio client, and typed errors per category.

### Added

- `AsyncDevhelm`: the same surface as `Devhelm`, every method a coroutine
  (httpx). Both clients are generated from one source (`src/devhelm/_async`,
  `scripts/unasync.py`).
- Code checks: `code=` on `monitors.create`, `monitors.update`,
  `monitors.test`, `monitors.test_adhoc` and `monitors.revisions.create`
  takes a path, `{"entrypoint", "include"}` or `{"entrypoint", "files"}` in
  memory. The SDK uploads the file set to `POST /bundles` (JSON, or a zip
  when a file is binary), checks the returned `uploadDigest` against its own
  D-12 digest (`BUNDLE_DIGEST_MISMATCH` otherwise) and lets the server
  resolve the import closure. No Node, no JavaScript parsing.
  `devhelm.bundle_digest(files)` exposes the digest.
- `include` adds files nothing imports (fixtures, data) to the default set
  and names them to the server so the closure keeps them.
- `environment=` (slug or id) on create, update, restore, `test_adhoc`,
  `monitors.list` and `secrets.list`.
- Monitors: `test` (validation run), `probe` (uptime result), `test_adhoc`,
  `run_now`, `trigger` (multi-region; `wait=True` returns `TriggeredRuns`),
  `publish`, `rollback`, `rollback_preview`, `transfer`, `takeover`,
  `drift`, `restore`, `mute`, `unmute`, `quarantine`, `release_quarantine`,
  `list(name=, environment=, types=, tag=, display_health=)`, `list_all`.
- Sub-resources: `monitors.revisions` (list, get, create, test, diff, files,
  discard, keep, purge), `monitors.versions.list/get`, `monitors.history`,
  `monitors.trash`, `monitors.secret_requests`, `monitors.sessions`.
- `runs`: list / list_all (RunListParams filters), get, `wait`, cancel,
  steps, console, network, network_row, trace_summary, diff, export, pin,
  unpin, purge, `runs.artifacts.list/link/download`.
- `bundles.create/check`, `runtimes.list/get`, `account.usage/entitlements`,
  `audit.list`, `secrets.usage`, `secrets.values.set/delete`.
- Incidents: `update`, `acknowledge`, `add_update`, `runs`, `events`,
  `related`, `trigger`. Status pages: component `set_override` /
  `clear_override`.
- `wait` uses `GET /runs/{id}/events` (server-sent events) first, then polls.
  It returns the finished run whatever the outcome and raises only
  `WaitTimeoutError`.
- One error class per `ErrorResponse` category: `ValidationError`,
  `BlockedError`, `AuthError`, `PermissionError`, `OwnershipError`,
  `PlanLimitError`, `QuotaError`, `RateLimitError`, `ConflictError`,
  `ConfirmationRequiredError`, `NotFoundError`, `GoneError`,
  `PlatformError`, `TransportError`, plus `WaitTimeoutError`. Every envelope
  field is an attribute. The earlier HTTP-class names stay as base classes.
- Transport: `X-DevHelm-Client: sdk-python/<version>` on every call, an
  `Idempotency-Key` per POST reused only for retries, retries for 429, 503
  and retryable 409s honouring `Retry-After` (`max_attempts`, default 5).
- Credentials: the CLI's current context (`~/.devhelm/contexts.json`) after
  `token=` and `DEVHELM_API_TOKEN`; `DEVHELM_API_URL` sets the base URL. No
  token raises `ValidationError` `NO_TOKEN`.
- Request methods take the generated model, a dict, or the model's fields as
  keyword arguments (snake_case or camelCase).

### Changed

- `monitors.test(id)` runs a code check and returns its `RunDto`. On an
  uptime monitor it still returns the probe result with a one-time
  deprecation warning until 2027-01-31, then raises `ValidationError`
  `USE_PROBE`. The result type is `MonitorTestOutcome`; narrow it with
  `devhelm.is_run`. The probe is `monitors.probe(id)`.
- Free-form JSON fields (`capturePolicySnapshot`, `details`, …) are typed
  `JsonValue` instead of `dict[str, dict[str, Any]]`, which also fixes
  decoding scalar values in them.
- Regenerated from the Wave 0 spec: `RunDto.flaky`, nullable
  `RunDto.monitorId`, owner `GIT`. Run list, cases, console and network
  filters are generated `*Params` models built from the operations' query
  parameters (`scripts/query_models.py`).
- The offset-page envelope (`TableValueResult`) is sealed again: an unknown
  top-level key raises.

### Deprecated (removed 2027-01-31, warns once)

- `monitors.versions(id)` → `monitors.versions.list(id)`
- `monitors.results(id)` → `monitors.history.list(id)`
- `monitors.test_run(id)` → `monitors.test(id)`
