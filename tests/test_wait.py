"""Tests for ``wait_for_run``: server-sent events first, then polling."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable

import httpx
import pytest

from devhelm._async import wait as async_wait
from devhelm._async.transport import AsyncTransport
from devhelm._errors import WaitTimeoutError
from devhelm._sync import wait as sync_wait
from devhelm._sync.transport import Transport

RUN_ID = "6f1c2a3b-4d5e-4f60-8a7b-9c0d1e2f3a4b"
RUN_PATH = f"/api/v1/runs/{RUN_ID}"
EVENTS_PATH = f"{RUN_PATH}/events"


def _run(phase: str, outcome: str | None = None) -> dict[str, object]:
    return {
        "id": RUN_ID,
        "organizationId": 1,
        "monitorId": "550e8400-e29b-41d4-a716-446655440000",
        "monitorName": "Checkout flow",
        "monitorType": "BROWSER",
        "revisionId": "7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d",
        "region": "us-east",
        "source": "remote_validation",
        "countsTowardHealth": False,
        "enqueuedAt": "2026-10-21T10:00:00Z",
        "phase": phase,
        "outcome": outcome,
        "cancelRequested": False,
        "bundleDigest": "sha256:abc",
        "capturePolicySnapshot": {"screenshots": "on_failure"},
        "bindingVersionSnapshot": {},
        "stream": phase != "finished",
        "evidence": [],
        "tabCounts": {"steps": 0, "assets": 0, "diff": 0},
        "attempt": 1,
        "attemptOf": 1,
        "attempts": [],
        "executionAttempts": [],
        "billable": True,
    }


def _sse(*events: dict[str, object], event_name: str | None = None) -> bytes:
    chunks = [": keep-alive\n\n"]
    for i, body in enumerate(events, start=1):
        head = f"event: {event_name}\n" if event_name else ""
        chunks.append(f"id: {i}\n{head}data: {json.dumps(body)}\n\n")
    return "".join(chunks).encode()


class _Server:
    """Answers GET /runs/{id} from a queue of phases and the events endpoint."""

    def __init__(
        self,
        runs: list[dict[str, object]],
        events: Callable[[httpx.Request], httpx.Response] | None = None,
    ) -> None:
        self.runs = runs
        self.events = events
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == EVENTS_PATH:
            if self.events is None:
                return httpx.Response(404, json={"message": "no stream"})
            return self.events(request)
        if request.url.path == RUN_PATH:
            body = self.runs.pop(0) if len(self.runs) > 1 else self.runs[0]
            return httpx.Response(200, json={"data": body})
        return httpx.Response(404, json={"message": "unexpected"})

    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]


def _sync_transport(server: _Server) -> Transport:
    return Transport(
        httpx.Client(transport=httpx.MockTransport(server), base_url="http://api.test")
    )


def _async_transport(server: _Server) -> AsyncTransport:
    return AsyncTransport(
        httpx.AsyncClient(
            transport=httpx.MockTransport(server), base_url="http://api.test"
        )
    )


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []

    def fake_sleep(seconds: float) -> None:
        recorded.append(seconds)

    async def fake_async_sleep(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(sync_wait, "sleep", fake_sleep)
    monkeypatch.setattr(async_wait, "sleep", fake_async_sleep)
    return recorded


def _event_stream(body: bytes) -> Callable[[httpx.Request], httpx.Response]:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=body, headers={"content-type": "text/event-stream"}
        )

    return handler


# -- sync ---------------------------------------------------------------------


def test_already_finished_returns_without_stream(sleeps: list[float]) -> None:
    server = _Server([_run("finished", "passed")])
    run = sync_wait.wait_for_run(_sync_transport(server), RUN_ID)
    assert run.phase == "finished" and run.outcome == "passed"
    assert server.paths() == [RUN_PATH]
    assert sleeps == []


def test_finished_event_then_get(sleeps: list[float]) -> None:
    stream = _sse(
        {"type": "phase", "payload": {"phase": "running"}},
        {"type": "step_started", "payload": {}},
        {"type": "finished", "payload": {}},
    )
    server = _Server(
        [_run("queued"), _run("finished", "passed")], events=_event_stream(stream)
    )
    run = sync_wait.wait_for_run(_sync_transport(server), RUN_ID)
    assert run.outcome == "passed"
    assert server.paths() == [RUN_PATH, EVENTS_PATH, RUN_PATH]
    events_request = server.requests[1]
    assert events_request.headers["accept"] == "text/event-stream"
    assert sleeps == []


def test_phase_finished_event_counts(sleeps: list[float]) -> None:
    stream = _sse({"type": "phase", "payload": {"phase": "finished"}})
    server = _Server(
        [_run("running"), _run("finished", "passed")], events=_event_stream(stream)
    )
    run = sync_wait.wait_for_run(_sync_transport(server), RUN_ID)
    assert run.phase == "finished"
    assert sleeps == []


def test_named_finished_event_counts(sleeps: list[float]) -> None:
    stream = _sse({"seq": 1}, event_name="finished")
    server = _Server(
        [_run("running"), _run("finished", "passed")], events=_event_stream(stream)
    )
    assert sync_wait.wait_for_run(_sync_transport(server), RUN_ID).phase == "finished"


@pytest.mark.parametrize("status", [404, 406])
def test_stream_refused_falls_back_to_polling(sleeps: list[float], status: int) -> None:
    def refuse(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"message": "nope", "code": "X"})

    server = _Server(
        [_run("queued"), _run("running"), _run("finished", "passed")], events=refuse
    )
    run = sync_wait.wait_for_run(_sync_transport(server), RUN_ID)
    assert run.outcome == "passed"
    assert server.paths() == [RUN_PATH, EVENTS_PATH, RUN_PATH, RUN_PATH]
    assert len(sleeps) == 2
    assert sleeps[1] > sleeps[0]  # backoff grows


def test_stream_ending_without_finished_polls(sleeps: list[float]) -> None:
    stream = _sse({"type": "headline", "payload": {}})
    server = _Server(
        [_run("queued"), _run("finished", "failed")], events=_event_stream(stream)
    )
    run = sync_wait.wait_for_run(_sync_transport(server), RUN_ID)
    assert run.outcome == "failed"
    assert len(sleeps) == 1


@pytest.mark.parametrize("outcome", ["failed", "execution_error", "timed_out"])
def test_failed_outcomes_are_returned(sleeps: list[float], outcome: str) -> None:
    server = _Server([_run("queued"), _run("finished", outcome)])
    run = sync_wait.wait_for_run(_sync_transport(server), RUN_ID)
    assert run.outcome == outcome


def test_deadline_raises_wait_timeout(
    sleeps: list[float], monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = [1000.0]

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(sync_wait, "sleep", fake_sleep)
    monkeypatch.setattr(sync_wait, "monotonic", lambda: clock[0])
    server = _Server([_run("running")])
    with pytest.raises(WaitTimeoutError) as err:
        sync_wait.wait_for_run(_sync_transport(server), RUN_ID, timeout_ms=5_000)
    assert err.value.run_id == RUN_ID
    assert err.value.phase == "running"
    assert err.value.aborted is False
    assert err.value.timeout_ms == 5_000
    assert sum(sleeps) == pytest.approx(5.0)
    # The run is never cancelled.
    assert all(r.method == "GET" for r in server.requests)


def test_signal_aborts(sleeps: list[float]) -> None:
    signal = threading.Event()
    signal.set()
    server = _Server([_run("queued")])
    with pytest.raises(WaitTimeoutError) as err:
        sync_wait.wait_for_run(_sync_transport(server), RUN_ID, signal=signal)
    assert err.value.aborted is True
    assert err.value.phase == "queued"
    assert EVENTS_PATH not in server.paths()


# -- async --------------------------------------------------------------------


def test_async_finished_event(sleeps: list[float]) -> None:
    stream = _sse({"type": "finished", "payload": {}})
    server = _Server(
        [_run("queued"), _run("finished", "passed")], events=_event_stream(stream)
    )
    run = asyncio.run(async_wait.wait_for_run(_async_transport(server), RUN_ID))
    assert run.outcome == "passed"
    assert server.paths() == [RUN_PATH, EVENTS_PATH, RUN_PATH]
    assert server.requests[1].headers["accept"] == "text/event-stream"


def test_async_polling_fallback(sleeps: list[float]) -> None:
    server = _Server([_run("queued"), _run("running"), _run("finished", "failed")])
    run = asyncio.run(async_wait.wait_for_run(_async_transport(server), RUN_ID))
    assert run.outcome == "failed"
    assert len(sleeps) == 2


def test_async_signal_aborts(sleeps: list[float]) -> None:
    async def go() -> None:
        signal = asyncio.Event()
        signal.set()
        server = _Server([_run("running")])
        with pytest.raises(WaitTimeoutError) as err:
            await async_wait.wait_for_run(
                _async_transport(server), RUN_ID, signal=signal
            )
        assert err.value.aborted is True

    asyncio.run(go())


def test_async_deadline(sleeps: list[float], monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [0.0]

    async def fake_sleep(seconds: float) -> None:
        clock[0] += seconds

    monkeypatch.setattr(async_wait, "sleep", fake_sleep)
    monkeypatch.setattr(async_wait, "monotonic", lambda: clock[0])
    server = _Server([_run("queued")])
    with pytest.raises(WaitTimeoutError) as err:
        asyncio.run(
            async_wait.wait_for_run(_async_transport(server), RUN_ID, timeout_ms=3_000)
        )
    assert err.value.phase == "queued"
