# Generated from src/devhelm/_async/wait.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Wait for a run to finish: server-sent events first, then polling.

``wait_for_run`` returns the finished ``RunDto`` whatever its outcome; it
never raises on ``failed``. It raises only :class:`WaitTimeoutError` (with the
run id and last phase) when the run is still going at the deadline, and it
never cancels the run. ``GET /runs/{id}/events`` counts once per connection
against the rate limit, which is why it is tried before polling.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field

import httpx

from devhelm._errors import DevhelmApiError, DevhelmTransportError, WaitTimeoutError
from devhelm._generated import RunDto
from devhelm._sync._compat import Event, is_set, monotonic, sleep
from devhelm._sync.transport import Transport, api_get
from devhelm._transport import path_param
from devhelm._validation import parse_single

DEFAULT_WAIT_TIMEOUT_MS = 300_000
FINISHED = "finished"

# Polling cadence once the event stream is unavailable.
_POLL_START_S = 2.0
_POLL_MAX_S = 10.0
# One event-stream connection waits at most this long for the next line.
_STREAM_READ_S = 60.0


def is_finished(run: RunDto) -> bool:
    return run.phase == FINISHED


@dataclass
class _SseEvent:
    id: str | None = None
    event: str | None = None
    data: list[str] = field(default_factory=list)

    def finished(self) -> bool:
        if self.event == FINISHED:
            return True
        try:
            body = json.loads("\n".join(self.data)) if self.data else None
        except ValueError:
            return False
        if not isinstance(body, dict):
            return False
        kind = body.get("type")
        if kind == FINISHED:
            return True
        payload = body.get("payload")
        return (
            kind == "phase"
            and isinstance(payload, dict)
            and payload.get("phase") == FINISHED
        )


def _events(response: httpx.Response) -> Iterator[_SseEvent]:
    current = _SseEvent()
    for line in response.iter_lines():
        if not line:
            if current.data or current.event:
                yield current
            current = _SseEvent()
            continue
        if line.startswith(":"):
            continue
        name, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if name == "data":
            current.data.append(value)
        elif name == "event":
            current.event = value
        elif name == "id":
            current.id = value
    if current.data or current.event:
        yield current


def get_run(transport: Transport, run_id: str) -> RunDto:
    path = f"/api/v1/runs/{path_param(run_id)}"
    return parse_single(RunDto, api_get(transport, path), f"GET {path}")


def _stream_until_finished(
    transport: Transport, run_id: str, deadline: float, signal: Event | None
) -> bool:
    """Follow the event stream until a finished event, the deadline or a drop.

    Returns ``True`` on a finished event, ``False`` when the stream is
    unavailable or ended without one (the caller then polls).
    """
    path = f"/api/v1/runs/{path_param(run_id)}/events"
    last_id: str | None = None
    while True:
        remaining = deadline - monotonic()
        if remaining <= 0 or is_set(signal):
            return False
        headers = {"Accept": "text/event-stream"}
        if last_id is not None:
            headers["Last-Event-ID"] = last_id
        timeout = httpx.Timeout(10.0, read=min(remaining, _STREAM_READ_S))
        try:
            with transport.stream(
                "GET", path, headers=headers, timeout=timeout
            ) as response:
                for event in _events(response):
                    last_id = event.id or last_id
                    if event.finished():
                        return True
                    if is_set(signal) or monotonic() >= deadline:
                        return False
        except DevhelmApiError:
            # The stream was refused (older server, proxy): poll instead.
            return False
        except DevhelmTransportError:
            # Read timeout or a dropped connection. Reconnect only when the
            # stream had delivered something; otherwise poll.
            if last_id is None:
                return False
            continue
        # The server closed the stream without a finished event.
        return False


def wait_for_run(
    transport: Transport,
    run_id: str,
    *,
    timeout_ms: int = DEFAULT_WAIT_TIMEOUT_MS,
    signal: Event | None = None,
) -> RunDto:
    """Return the run once ``phase == "finished"``. See the module docstring."""
    run_id = str(run_id)
    deadline = monotonic() + timeout_ms / 1000
    run = get_run(transport, run_id)
    if is_finished(run):
        return run
    if _stream_until_finished(transport, run_id, deadline, signal):
        run = get_run(transport, run_id)
        if is_finished(run):
            return run
    delay = _POLL_START_S
    while True:
        if is_set(signal):
            raise WaitTimeoutError(
                run_id, run.phase, timeout_ms=timeout_ms, aborted=True
            )
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise WaitTimeoutError(run_id, run.phase, timeout_ms=timeout_ms)
        sleep(min(delay, remaining))
        run = get_run(transport, run_id)
        if is_finished(run):
            return run
        delay = min(delay * 1.5, _POLL_MAX_S)
