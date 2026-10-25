"""Unit tests for the code-check surface of ``monitors`` (doc 42 §9).

Every test drives the sync ``Monitors`` resource (generated from
``devhelm/_async/resources/monitors.py``) through an ``httpx.MockTransport``
router and asserts the exact routes, query strings and request bodies.
"""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest

import devhelm._authoring as authoring
from devhelm import (
    CursorPage,
    DefinitionHeadDto,
    DevhelmMonitorTestQueuedError,
    DevhelmValidationError,
    MonitorDto,
    MonitorTestResultDto,
    Page,
    RunDto,
    TriggeredRuns,
    TriggerRunsResponse,
    ValidationError,
    bundle_digest,
)
from devhelm._generated import HttpMonitorConfig
from devhelm.resources.monitors import Monitors

BASE = "http://api.test"
TS = "2026-10-25T10:00:00Z"
MID = "550e8400-e29b-41d4-a716-446655440000"
ENV = "11111111-2222-4333-8444-555555555555"
REV = "7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d"
LIVE = "8b9c0d1e-2f3a-4b4c-9d5e-6f7a8b9c0d1e"
DEF = "9c0d1e2f-3a4b-4c5d-8e6f-7a8b9c0d1e2f"
RUN_ID = "6f1c2a3b-4d5e-4f60-8a7b-9c0d1e2f3a4b"
RUN_ID_2 = "6f1c2a3b-4d5e-4f60-8a7b-9c0d1e2f3a4c"
CLOSURE = "sha256:" + "a" * 64

Handler = Callable[[httpx.Request], httpx.Response]


class Router:
    """Route ``(method, path)`` to a canned response and record every call."""

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Handler] = {}
        self.calls: list[httpx.Request] = []

    def add(
        self,
        method: str,
        path: str,
        body: object = None,
        *,
        status: int = 200,
        handler: Handler | None = None,
    ) -> None:
        def respond(_req: httpx.Request) -> httpx.Response:
            if body is None:
                return httpx.Response(status)
            return httpx.Response(status, json=body)

        self.routes[(method, path)] = handler or respond

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        route = self.routes.get((request.method, request.url.path))
        if route is None:
            return httpx.Response(
                404,
                json={
                    "status": 404,
                    "code": "NOT_FOUND",
                    "category": "not_found",
                    "retryable": False,
                    "message": f"no route {request.method} {request.url.path}",
                    "timestamp": 0,
                },
            )
        return route(request)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self), base_url=BASE)

    def paths(self) -> list[tuple[str, str]]:
        return [(r.method, r.url.path) for r in self.calls]

    def last(self, method: str, path: str) -> httpx.Request:
        for request in reversed(self.calls):
            if request.method == method and request.url.path == path:
                return request
        raise AssertionError(f"{method} {path} was not called: {self.paths()}")


def body_of(request: httpx.Request) -> dict[str, object]:
    parsed = json.loads(request.content)
    assert isinstance(parsed, dict)
    return parsed


def single(data: object) -> dict[str, object]:
    return {"data": data}


def table(items: list[object], *, has_next: bool = False) -> dict[str, object]:
    return {"data": items, "hasNext": has_next, "hasPrev": False}


def cursor(items: list[object], next_cursor: str | None = None) -> dict[str, object]:
    return {
        "data": items,
        "nextCursor": next_cursor,
        "hasMore": next_cursor is not None,
    }


def monitor(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": MID,
        "organizationId": 1,
        "name": "Checkout",
        "type": "BROWSER",
        "config": {},
        "frequencySeconds": 600,
        "enabled": True,
        "regions": ["us-east"],
        "managedBy": "API",
        "ownerEnforced": False,
        "createdAt": TS,
        "updatedAt": TS,
        "muted": False,
        "liveRevisionId": LIVE,
    }
    base.update(over)
    return base


def run(
    run_id: str = RUN_ID, phase: str = "queued", **over: object
) -> dict[str, object]:
    base: dict[str, object] = {
        "id": run_id,
        "organizationId": 1,
        "monitorId": MID,
        "revisionId": REV,
        "region": "us-east",
        "source": "remote_validation",
        "countsTowardHealth": False,
        "enqueuedAt": TS,
        "phase": phase,
        "cancelRequested": False,
        "bundleDigest": CLOSURE,
        "capturePolicySnapshot": {"screenshots": "on_failure"},
        "bindingVersionSnapshot": {},
        "stream": False,
        "evidence": [],
        "tabCounts": {"steps": 0, "assets": 0, "diff": 0},
        "attempt": 1,
        "attemptOf": 1,
        "attempts": [],
        "executionAttempts": [],
        "billable": True,
    }
    if phase == "finished":
        base["outcome"] = "passed"
    base.update(over)
    return base


def revision(rev_id: str = REV, **over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": rev_id,
        "definitionId": DEF,
        "number": 2,
        "digest": CLOSURE,
        "entrypoint": "checkout.spec.ts",
        "files": ["checkout.spec.ts"],
        "keys": [],
        "createdAt": TS,
        "state": "draft",
    }
    base.update(over)
    return base


def environment(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": ENV,
        "orgId": 1,
        "name": "Production",
        "slug": "production",
        "variables": {},
        "monitorCount": 1,
        "isDefault": True,
        "createdAt": TS,
        "updatedAt": TS,
    }
    base.update(over)
    return base


def head() -> dict[str, object]:
    return {
        "definitionId": DEF,
        "environment": environment(),
        "revision": revision(state="live"),
        "activatedAt": TS,
    }


PROBE: dict[str, object] = {"passed": True, "statusCode": 200, "assertionResults": []}


def _json_bundle_handler(request: httpx.Request) -> httpx.Response:
    files = {k: v.encode("utf-8") for k, v in body_of(request)["files"].items()}  # type: ignore[union-attr]
    return _bundle_response(files)


def _zip_bundle_handler(request: httpx.Request) -> httpx.Response:
    with zipfile.ZipFile(io.BytesIO(request.content)) as zf:
        files = {name: zf.read(name) for name in zf.namelist()}
    return _bundle_response(files)


def _bundle_response(files: dict[str, bytes]) -> httpx.Response:
    return httpx.Response(
        201,
        json=single(
            {
                "digest": CLOSURE,
                "uploadDigest": bundle_digest(files),
                "files": sorted(files),
                "keys": [],
                "size": sum(len(v) for v in files.values()),
            }
        ),
    )


def add_bundles(router: Router) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["content-type"] == "application/zip":
            return _zip_bundle_handler(request)
        return _json_bundle_handler(request)

    router.add("POST", "/api/v1/bundles", handler=handler)


MEMORY_CODE = {
    "entrypoint": "checkout.spec.ts",
    "files": {"checkout.spec.ts": "test('ok', async () => {})\n"},
}


@pytest.fixture(autouse=True)
def _reset_deprecations() -> Iterator[None]:
    authoring._warned.clear()
    yield
    authoring._warned.clear()


@pytest.fixture
def router() -> Router:
    return Router()


def monitors(router: Router) -> Monitors:
    return Monitors(router.client())


# -- create / update with code ------------------------------------------------


def test_create_with_path_uploads_bundle_then_creates(
    router: Router, tmp_path: Path
) -> None:
    entry = tmp_path / "checkout.spec.ts"
    entry.write_text("test('checkout', async () => {})\n")
    add_bundles(router)
    router.add("POST", "/api/v1/monitors", single(monitor()), status=201)

    out = monitors(router).create(
        name="Checkout",
        type="BROWSER",
        environment_id=ENV,
        code=str(entry),
        root=tmp_path,
        frequency_seconds=600,
        regions=["us-east"],
    )

    assert isinstance(out, MonitorDto)
    assert router.paths() == [("POST", "/api/v1/bundles"), ("POST", "/api/v1/monitors")]
    upload = body_of(router.calls[0])
    assert upload["entrypoint"] == "checkout.spec.ts"
    assert upload["files"] == {"checkout.spec.ts": entry.read_text()}
    created = body_of(router.calls[1])
    code = created["code"]
    assert isinstance(code, dict)
    assert code["bundle"] == CLOSURE
    assert code["entrypoint"] == "checkout.spec.ts"
    assert created["frequencySeconds"] == 600
    assert created["environmentId"] == ENV


def test_upload_digest_mismatch_stops_before_create(router: Router) -> None:
    router.add(
        "POST",
        "/api/v1/bundles",
        single(
            {
                "digest": CLOSURE,
                "uploadDigest": "sha256:" + "b" * 64,
                "files": [],
                "keys": [],
                "size": 0,
            }
        ),
        status=201,
    )
    with pytest.raises(ValidationError) as exc:
        monitors(router).create(
            name="Checkout", type="BROWSER", environment_id=ENV, code=MEMORY_CODE
        )
    assert exc.value.code == "BUNDLE_DIGEST_MISMATCH"
    assert exc.value.status == 0
    assert router.paths() == [("POST", "/api/v1/bundles")]


def test_in_memory_binary_file_uploads_as_zip(router: Router) -> None:
    add_bundles(router)
    router.add("POST", "/api/v1/monitors", single(monitor()), status=201)
    files: dict[str, str | bytes] = {
        "checkout.spec.ts": "test('x', async () => {})\n",
        "fixtures/logo.png": b"\x89PNG\r\n\x1a\n\xff\xfe",
    }
    monitors(router).create(
        name="Checkout",
        type="BROWSER",
        environment_id=ENV,
        code={"entrypoint": "checkout.spec.ts", "files": files},
    )
    upload = router.calls[0]
    assert upload.headers["content-type"] == "application/zip"
    assert upload.url.params["entrypoint"] == "checkout.spec.ts"
    with zipfile.ZipFile(io.BytesIO(upload.content)) as zf:
        assert zf.read("fixtures/logo.png") == files["fixtures/logo.png"]


def test_environment_slug_is_resolved(router: Router) -> None:
    add_bundles(router)
    router.add("GET", "/api/v1/environments/production", single(environment()))
    router.add("POST", "/api/v1/monitors", single(monitor()), status=201)
    monitors(router).create(
        name="Checkout", type="BROWSER", environment="production", code=MEMORY_CODE
    )
    assert ("GET", "/api/v1/environments/production") in router.paths()
    assert body_of(router.last("POST", "/api/v1/monitors"))["environmentId"] == ENV


def test_environment_uuid_needs_no_lookup(router: Router) -> None:
    add_bundles(router)
    router.add("POST", "/api/v1/monitors", single(monitor()), status=201)
    monitors(router).create(
        name="Checkout", type="BROWSER", environment=ENV, code=MEMORY_CODE
    )
    assert not any(p.startswith("/api/v1/environments") for _, p in router.paths())
    assert body_of(router.last("POST", "/api/v1/monitors"))["environmentId"] == ENV


def test_snake_and_camel_kwargs_both_accepted(router: Router) -> None:
    router.add("POST", "/api/v1/monitors", single(monitor(type="HTTP")), status=201)
    config = {"url": "https://example.com", "method": "GET"}
    monitors(router).create(name="A", type="HTTP", config=config, frequency_seconds=300)
    monitors(router).create(name="B", type="HTTP", config=config, frequencySeconds=300)
    first, second = (body_of(r) for r in router.calls)
    assert first["frequencySeconds"] == second["frequencySeconds"] == 300


def test_http_config_on_browser_is_refused_before_any_call(router: Router) -> None:
    with pytest.raises(ValidationError) as exc:
        monitors(router).create(
            name="Checkout",
            type="BROWSER",
            environment_id=ENV,
            config=HttpMonitorConfig(url="https://example.com", method="GET"),
        )
    assert exc.value.code == "MONITOR_CONFIG_TYPE_MISMATCH"
    assert router.calls == []


def test_unknown_config_key_is_refused_before_any_call(router: Router) -> None:
    with pytest.raises(ValidationError) as exc:
        monitors(router).create(
            name="Checkout",
            type="BROWSER",
            environment_id=ENV,
            config={"url": "https://example.com"},
        )
    assert exc.value.code == "FIELD_UNKNOWN"
    assert exc.value.errors[0].field == "config.url"
    assert router.calls == []


def test_unknown_top_level_field_is_refused(router: Router) -> None:
    with pytest.raises(DevhelmValidationError):
        monitors(router).create(name="Checkout", type="HTTP", bogus_field=1)
    assert router.calls == []


def test_update_with_code_publishes_through_put(router: Router) -> None:
    add_bundles(router)
    router.add("PUT", f"/api/v1/monitors/{MID}", single(monitor()))
    monitors(router).update(MID, code=MEMORY_CODE, expected_updated_at=TS)
    put = body_of(router.last("PUT", f"/api/v1/monitors/{MID}"))
    assert put["code"]["bundle"] == CLOSURE  # type: ignore[index]
    assert "expectedUpdatedAt" in put


def test_list_by_exact_name(router: Router) -> None:
    router.add(
        "GET",
        "/api/v1/monitors",
        table([monitor(), monitor(id=LIVE, name="Checkout 2")]),
    )
    found = monitors(router).list(name="Checkout")
    assert [m.name for m in found] == ["Checkout"]
    assert router.calls[0].url.params["name"] == "Checkout"


def test_list_environment_slug_and_types(router: Router) -> None:
    router.add(
        "GET", "/api/v1/environments/staging", single(environment(slug="staging"))
    )
    router.add("GET", "/api/v1/monitors", table([]))
    monitors(router).list(environment="staging", types=["BROWSER", "MULTI_STEP_API"])
    params = router.last("GET", "/api/v1/monitors").url.params
    assert params["environmentId"] == ENV
    assert params["types"] == "BROWSER,MULTI_STEP_API"


# -- revisions ----------------------------------------------------------------


def test_revision_create_uploads_and_drafts(router: Router) -> None:
    add_bundles(router)
    router.add(
        "POST", f"/api/v1/monitors/{MID}/revisions", single({"revision": revision()})
    )
    out = monitors(router).revisions.create(MID, code=MEMORY_CODE)
    assert str(out.revision.id) == REV
    draft = body_of(router.last("POST", f"/api/v1/monitors/{MID}/revisions"))
    code = draft["code"]
    assert isinstance(code, dict)
    assert code["bundle"] == CLOSURE
    assert code["entrypoint"] == "checkout.spec.ts"


def test_revision_test_queues_a_run(router: Router) -> None:
    path = f"/api/v1/monitors/{MID}/revisions/{REV}/test"
    router.add("POST", path, single(run()), status=202)
    out = monitors(router).revisions.test(MID, REV, region="eu-west")
    assert isinstance(out, RunDto)
    assert body_of(router.calls[0]) == {"region": "eu-west"}


def test_revision_list_joins_states(router: Router) -> None:
    router.add("GET", f"/api/v1/monitors/{MID}/revisions", table([revision()]))
    page = monitors(router).revisions.list(MID, state=["draft", "live"])
    assert isinstance(page, Page)
    params = router.calls[0].url.params
    assert params["state"] == "draft,live"
    assert params["page"] == "0"


def test_revision_get_files_keep_discard_purge(router: Router) -> None:
    router.add("GET", f"/api/v1/revisions/{REV}", single(revision()))
    router.add(
        "GET",
        f"/api/v1/revisions/{REV}/files",
        single({"entrypoint": "checkout.spec.ts", "files": {"checkout.spec.ts": "x"}}),
    )
    router.add(
        "POST", f"/api/v1/monitors/{MID}/revisions/{REV}/keep", single(revision())
    )
    router.add("DELETE", f"/api/v1/monitors/{MID}/revisions/{REV}", status=204)
    router.add("POST", f"/api/v1/revisions/{REV}/purge", single(revision()))
    m = monitors(router)
    assert str(m.revisions.get(MID, REV).id) == REV
    assert m.revisions.files(MID, REV).files == {"checkout.spec.ts": "x"}
    m.revisions.keep(MID, REV)
    m.revisions.discard(MID, REV)
    m.revisions.purge(MID, REV, reason="leaked a token")
    assert body_of(router.last("POST", f"/api/v1/revisions/{REV}/purge")) == {
        "reason": "leaked a token"
    }


def test_revision_diff_defaults_to_live(router: Router) -> None:
    router.add("GET", f"/api/v1/monitors/{MID}", single(monitor()))
    router.add(
        "GET",
        f"/api/v1/revisions/{REV}/diff/{LIVE}",
        single({"left": revision(), "right": revision(LIVE), "hunks": []}),
    )
    out = monitors(router).revisions.diff(MID, REV)
    assert str(out.right.id) == LIVE
    assert router.paths()[0] == ("GET", f"/api/v1/monitors/{MID}")


def test_revision_diff_explicit_other_skips_monitor_lookup(router: Router) -> None:
    router.add(
        "GET",
        f"/api/v1/revisions/{REV}/diff/{LIVE}",
        single({"left": revision(), "right": revision(LIVE), "hunks": []}),
    )
    monitors(router).revisions.diff(MID, REV, LIVE)
    assert router.paths() == [("GET", f"/api/v1/revisions/{REV}/diff/{LIVE}")]


# -- publish / rollback / ownership -----------------------------------------


def test_publish_sends_camel_case(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/publish", single(head()))
    out = monitors(router).publish(
        MID, revision_id=REV, expected_live_revision_id=LIVE, require_tested=True
    )
    assert isinstance(out, DefinitionHeadDto)
    assert body_of(router.calls[0]) == {
        "revisionId": REV,
        "expectedLiveRevisionId": LIVE,
        "requireTested": True,
    }


def test_rollback_and_preview(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/rollback", single(head()))
    router.add(
        "GET",
        f"/api/v1/monitors/{MID}/rollback-preview",
        single({"target": revision(), "affectedMonitors": [monitor()]}),
    )
    m = monitors(router)
    m.rollback(MID, reason="checkout broke", revision_id=REV)
    assert body_of(router.calls[0]) == {"reason": "checkout broke", "revisionId": REV}
    preview = m.rollback_preview(MID, revision_id=REV)
    assert len(preview.affected_monitors) == 1
    assert router.calls[1].url.params["revisionId"] == REV


def test_transfer_takeover_drift_restore(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/transfer", single(monitor()))
    router.add("POST", f"/api/v1/monitors/{MID}/takeover", single(monitor()))
    router.add("GET", f"/api/v1/monitors/{MID}/drift", single({"fields": []}))
    router.add("POST", f"/api/v1/monitors/{MID}/restore", single(monitor()))
    m = monitors(router)
    m.transfer(MID, to="TERRAFORM", reason="moving to terraform")
    assert body_of(router.calls[0]) == {
        "to": "TERRAFORM",
        "reason": "moving to terraform",
    }
    m.takeover(MID, field="muted")
    assert body_of(router.calls[1]) == {"field": "muted"}
    assert m.drift(MID).fields == []
    m.restore(MID, environment=ENV)
    assert body_of(router.calls[3]) == {"environmentId": ENV}


def test_overlay_verbs(router: Router) -> None:
    for verb in (
        "pause",
        "resume",
        "mute",
        "unmute",
        "quarantine",
        "release-quarantine",
    ):
        router.add("POST", f"/api/v1/monitors/{MID}/{verb}", single(monitor()))
    m = monitors(router)
    m.pause(MID, reason="maintenance")
    m.resume(MID)
    m.mute(MID, reason="noisy", expires_at=TS)
    m.unmute(MID)
    m.quarantine(MID, reason="flaky", expires_at=TS)
    m.release_quarantine(MID)
    bodies = [r.content for r in router.calls]
    assert json.loads(bodies[0]) == {"reason": "maintenance"}
    assert bodies[1] == b""
    assert json.loads(bodies[2])["reason"] == "noisy"
    assert json.loads(bodies[4])["reason"] == "flaky"
    assert [p for _, p in router.paths()][-1].endswith("/release-quarantine")


def test_quarantine_requires_its_fields(router: Router) -> None:
    with pytest.raises(DevhelmValidationError):
        monitors(router).quarantine(MID, reason="flaky")
    assert router.calls == []


# -- test / probe / adhoc / run_now / trigger -----------------------------


def test_test_returns_run_on_202(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/test", single(run()), status=202)
    out = monitors(router).test(MID)
    assert isinstance(out, RunDto)


def test_test_on_uptime_raises_use_probe(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/test", single(PROBE))
    with pytest.raises(ValidationError) as exc:
        monitors(router).test(MID)
    assert exc.value.code == "USE_PROBE"
    assert exc.value.next is not None
    assert exc.value.next.command == "monitors.probe(id)"


def test_probe(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/test", single(PROBE))
    out = monitors(router).probe(MID)
    assert isinstance(out, MonitorTestResultDto)
    assert out.passed is True


def test_probe_on_code_monitor_carries_the_run(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/test", single(run()), status=202)
    with pytest.raises(DevhelmMonitorTestQueuedError) as exc:
        monitors(router).probe(MID)
    assert str(exc.value.run.id) == RUN_ID


def test_test_adhoc_code(router: Router) -> None:
    add_bundles(router)
    router.add(
        "POST", "/api/v1/monitors/test", single(run()), status=202
    )  # monitorId becomes nullable in W0-3
    out = monitors(router).test_adhoc(type="BROWSER", environment=ENV, code=MEMORY_CODE)
    assert isinstance(out, RunDto)
    sent = body_of(router.last("POST", "/api/v1/monitors/test"))
    assert sent["type"] == "BROWSER"
    assert sent["environmentId"] == ENV
    assert sent["code"]["bundle"] == CLOSURE  # type: ignore[index]


def test_test_adhoc_uptime(router: Router) -> None:
    router.add("POST", "/api/v1/monitors/test", single(PROBE))
    out = monitors(router).test_adhoc(
        type="HTTP", config={"url": "https://example.com", "method": "GET"}
    )
    assert isinstance(out, MonitorTestResultDto)
    assert body_of(router.calls[0])["config"] == {
        "url": "https://example.com",
        "method": "GET",
    }


def test_run_now(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/runs", single(run()), status=202)
    out = monitors(router).run_now(MID)
    assert str(out.id) == RUN_ID
    # Every POST carries an idempotency key, even on a bare client.
    assert router.calls[0].headers["idempotency-key"]


def _trigger_body() -> dict[str, object]:
    return {
        "triggerId": DEF,
        "billedRuns": 2,
        "runs": [
            {"id": RUN_ID, "region": "us-east", "phase": "queued", "url": "/r/1"},
            {"id": RUN_ID_2, "region": "eu-west", "phase": "queued", "url": "/r/2"},
        ],
    }


def test_trigger_returns_trigger(router: Router) -> None:
    router.add(
        "POST", f"/api/v1/monitors/{MID}/triggers", single(_trigger_body()), status=202
    )
    out = monitors(router).trigger(MID, regions=["us-east", "eu-west"])
    assert isinstance(out, TriggerRunsResponse)
    assert body_of(router.calls[0]) == {"regions": ["us-east", "eu-west"]}


def test_trigger_wait_returns_finished_runs(
    router: Router, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("devhelm._sync.wait.sleep", lambda _s: None)
    router.add(
        "POST", f"/api/v1/monitors/{MID}/triggers", single(_trigger_body()), status=202
    )
    router.add("GET", f"/api/v1/runs/{RUN_ID}", single(run(RUN_ID, "finished")))
    router.add("GET", f"/api/v1/runs/{RUN_ID_2}", single(run(RUN_ID_2, "finished")))
    out = monitors(router).trigger(MID, signal=False, wait=True)
    assert isinstance(out, TriggeredRuns)
    assert out.billed_runs == 2
    assert [r.phase for r in out.runs] == ["finished", "finished"]


def test_test_wait_polls_when_events_are_unavailable(
    router: Router, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("devhelm._sync.wait.sleep", lambda _s: None)
    router.add("POST", f"/api/v1/monitors/{MID}/test", single(run()), status=202)
    phases = iter(["queued", "running", "finished"])

    def get_run(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=single(run(RUN_ID, next(phases))))

    router.add("GET", f"/api/v1/runs/{RUN_ID}", handler=get_run)
    out = monitors(router).test(MID, wait=True)
    assert out.phase == "finished"
    assert ("GET", f"/api/v1/runs/{RUN_ID}/events") in router.paths()


# -- deprecated aliases -----------------------------------------------------


def test_versions_call_is_deprecated_but_works(router: Router) -> None:
    router.add("GET", f"/api/v1/monitors/{MID}/versions", table([]))
    with pytest.warns(DeprecationWarning, match="2027-01-31"):
        page = monitors(router).versions(MID)
    assert page.data == []


def test_results_is_deprecated_but_works(router: Router) -> None:
    router.add(
        "GET",
        f"/api/v1/monitors/{MID}/results",
        cursor([{"id": RUN_ID, "region": "us-east", "timestamp": TS, "passed": True}]),
    )
    with pytest.warns(DeprecationWarning):
        page = monitors(router).results(MID)
    assert isinstance(page, CursorPage)
    assert len(page.data) == 1


def test_test_run_is_deprecated_but_works(router: Router) -> None:
    router.add("POST", f"/api/v1/monitors/{MID}/test", single(run()), status=202)
    with pytest.warns(DeprecationWarning):
        out = monitors(router).test_run(MID)
    assert isinstance(out, RunDto)


def test_deprecation_warns_once_per_process(router: Router) -> None:
    import warnings

    router.add("GET", f"/api/v1/monitors/{MID}/versions", table([]))
    m = monitors(router)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        m.versions(MID)
        m.versions(MID)
    assert len([w for w in caught if w.category is DeprecationWarning]) == 1


# -- versions / history / trash / secret requests / sessions ----------------


def _version() -> dict[str, object]:
    return {
        "id": DEF,
        "monitorId": MID,
        "version": 3,
        "snapshot": monitor(),
        "changedVia": "API",
        "createdAt": TS,
    }


def test_versions_list_and_get(router: Router) -> None:
    router.add("GET", f"/api/v1/monitors/{MID}/versions", table([_version()]))
    router.add("GET", f"/api/v1/monitors/{MID}/versions/3", single(_version()))
    m = monitors(router)
    assert m.versions.list(MID, page=1, size=5).data[0].version == 3
    assert router.calls[0].url.params["size"] == "5"
    assert m.versions.get(MID, 3).version == 3


def _history(reason: str) -> dict[str, object]:
    return {
        "kind": "skipped",
        "monitorId": MID,
        "reason": reason,
        "from": TS,
        "to": TS,
        "count": 1,
    }


def test_history_list_and_list_all(router: Router) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("cursor") == "c2":
            return httpx.Response(200, json=cursor([_history("b")]))
        return httpx.Response(200, json=cursor([_history("a")], "c2"))

    router.add("GET", f"/api/v1/monitors/{MID}/history", handler=handler)
    m = monitors(router)
    first = m.history.list(MID, limit=1)
    assert first.next_cursor == "c2" and first.has_more
    every = m.history.list_all(MID)
    assert [e.reason for e in every] == ["a", "b"]


def test_trash_list(router: Router) -> None:
    router.add("GET", "/api/v1/monitors/trash", table([monitor()]))
    assert len(monitors(router).trash.list()) == 1


def _secret_requests() -> dict[str, object]:
    return {
        "environment": environment(),
        "requests": [{"key": "CARD_TOKEN", "readiness": "missing"}],
    }


def test_secret_requests(router: Router) -> None:
    base = f"/api/v1/monitors/{MID}/secret-requests"
    router.add("GET", base, single(_secret_requests()))
    router.add("PUT", f"{base}/CARD_TOKEN", single(_secret_requests()))
    router.add("POST", f"{base}/rescan", single(_secret_requests()))
    m = monitors(router)
    assert m.secret_requests.list(MID, revision_id=REV).requests[0].key == "CARD_TOKEN"
    assert router.calls[0].url.params["revisionId"] == REV
    m.secret_requests.remap(MID, "CARD_TOKEN", secret_id=ENV)
    assert body_of(router.calls[1]) == {"secretId": ENV}
    m.secret_requests.rescan(MID)


def _session() -> dict[str, object]:
    return {
        "setupFile": "auth.setup.ts",
        "reusePolicy": "reuse",
        "lifecycle": "active",
        "cookieNames": [],
        "storageKeys": [],
    }


def test_sessions(router: Router) -> None:
    base = f"/api/v1/monitors/{MID}/sessions"
    router.add("GET", base, table([_session()]))
    router.add("PUT", base, single(_session()))
    router.add("POST", f"{base}/renew", single(run()), status=202)
    router.add("POST", f"{base}/revoke", single(_session()))
    m = monitors(router)
    assert m.sessions.list(MID)[0].setup_file == "auth.setup.ts"
    m.sessions.upsert(MID, setup_file="auth.setup.ts", reuse_policy="reuse")
    assert body_of(router.calls[1]) == {
        "setupFile": "auth.setup.ts",
        "reusePolicy": "reuse",
    }
    m.sessions.renew(MID, setup_file="auth.setup.ts")
    assert router.calls[2].url.params["setupFile"] == "auth.setup.ts"
    m.sessions.revoke(MID)
    assert "setupFile" not in router.calls[3].url.params


def test_unknown_monitor_type_config_passes_through() -> None:
    from devhelm._authoring import check_config

    config = {"anything": 1}
    assert check_config("NEW_TYPE", config) is config
