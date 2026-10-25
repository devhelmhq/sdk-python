"""Unit tests for runs, bundles, runtimes, account, audit, secrets values,
incident extensions and status-page component overrides (doc 42 §8/§9)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from devhelm import (
    CursorPage,
    DevhelmValidationError,
    RunDto,
    ValidationError,
    bundle_digest,
)
from devhelm.resources.account import Account
from devhelm.resources.audit import Audit
from devhelm.resources.bundles import Bundles
from devhelm.resources.incidents import Incidents
from devhelm.resources.runs import Runs
from devhelm.resources.runtimes import Runtimes
from devhelm.resources.secrets import Secrets
from devhelm.resources.status_pages import StatusPages
from tests.test_synthetics_monitors import (
    CLOSURE,
    ENV,
    MID,
    RUN_ID,
    RUN_ID_2,
    TS,
    Router,
    body_of,
    cursor,
    environment,
    monitor,
    run,
    single,
    table,
)

ART = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
ROW = "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff"
INC = "cccccccc-dddd-4eee-8fff-000000000000"
PAGE = "dddddddd-eeee-4fff-8000-111111111111"
COMP = "eeeeeeee-ffff-4000-8111-222222222222"


@pytest.fixture
def router() -> Router:
    return Router()


# -- runs ----------------------------------------------------------------------


def test_runs_list_flattens_filters_with_default_limit(router: Router) -> None:
    router.add("GET", "/api/v1/runs", cursor([run()], "next"))
    page = Runs(router.client()).list(
        monitor_id=MID, outcome="failed", from_="2026-10-24T00:00:00Z"
    )
    assert isinstance(page, CursorPage)
    assert page.next_cursor == "next"
    params = router.calls[0].url.params
    assert params["limit"] == "50"
    assert params["monitorId"] == MID
    assert params["outcome"] == "failed"
    assert params["from"].startswith("2026-10-24T00:00:00")
    assert "params" not in params


def test_runs_list_accepts_dict_and_explicit_limit(router: Router) -> None:
    router.add("GET", "/api/v1/runs", cursor([]))
    Runs(router.client()).list({"limit": 10, "phase": "not_finished"})
    params = router.calls[0].url.params
    assert params["limit"] == "10"
    assert params["phase"] == "not_finished"


def test_runs_list_rejects_unknown_filter(router: Router) -> None:
    with pytest.raises(DevhelmValidationError):
        Runs(router.client()).list(outcomez="failed")
    assert router.calls == []


def test_runs_list_all_follows_cursor(router: Router) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("cursor") == "c2":
            return httpx.Response(200, json=cursor([run(RUN_ID_2)]))
        return httpx.Response(200, json=cursor([run()], "c2"))

    router.add("GET", "/api/v1/runs", handler=handler)
    runs = Runs(router.client()).list_all(limit=1)
    assert [str(r.id) for r in runs] == [RUN_ID, RUN_ID_2]
    assert len(router.calls) == 2


def test_runs_get_and_cancel(router: Router) -> None:
    router.add("GET", f"/api/v1/runs/{RUN_ID}", single(run()))
    router.add(
        "POST", f"/api/v1/runs/{RUN_ID}/cancel", single(run(cancelRequested=True))
    )
    runs = Runs(router.client())
    assert isinstance(runs.get(RUN_ID), RunDto)
    assert runs.cancel(RUN_ID).cancel_requested is True


def test_runs_steps_reads_cases(router: Router) -> None:
    case = {
        "id": ROW,
        "organizationId": 1,
        "runId": RUN_ID,
        "attempt": 1,
        "index": 0,
        "title": "checkout",
        "status": "failed",
        "steps": [],
    }
    router.add("GET", f"/api/v1/runs/{RUN_ID}/cases", table([case]))
    cases = Runs(router.client()).steps(RUN_ID, attempt=2)
    assert cases[0].title == "checkout"
    assert router.calls[0].url.params["attempt"] == "2"


def test_runs_console_network_trace(router: Router) -> None:
    router.add(
        "GET",
        f"/api/v1/runs/{RUN_ID}/console",
        single({"state": "complete", "groups": []}),
    )
    row = {
        "id": ROW,
        "method": "GET",
        "url": "https://example.com",
        "resourceType": "document",
        "source": "browser",
        "curl": "curl https://example.com",
        "requestHeaders": {},
        "responseHeaders": {},
        "requestBody": "",
        "responseBody": "",
        "isNavigation": True,
        "requestBodyTruncated": False,
        "responseBodyTruncated": False,
    }
    router.add("GET", f"/api/v1/runs/{RUN_ID}/network", {"data": [], "hasMore": False})
    router.add("GET", f"/api/v1/runs/{RUN_ID}/network/{ROW}", single(row))
    router.add(
        "GET",
        f"/api/v1/runs/{RUN_ID}/trace-summary",
        single(
            {
                "runId": RUN_ID,
                "failedActions": [],
                "failedRequests": [],
                "consoleErrors": [],
                "text": "all good",
                "truncated": False,
            }
        ),
    )
    runs = Runs(router.client())
    assert runs.console(RUN_ID, level="error").state == "complete"
    assert router.calls[0].url.params["level"] == "error"
    assert runs.network(RUN_ID, failed=True).has_more is False
    assert router.calls[1].url.params["failed"] == "true"
    assert runs.network_row(RUN_ID, ROW).method == "GET"
    assert runs.trace_summary(RUN_ID).text == "all good"


def test_runs_diff_export_pin_purge(router: Router) -> None:
    router.add(
        "GET",
        f"/api/v1/runs/{RUN_ID}/diff",
        single(
            {"baselineKind": "last_pass", "picker": [], "readsAs": "same", "rows": []}
        ),
    )

    def export(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"PK\x03\x04zip")

    router.add("GET", f"/api/v1/runs/{RUN_ID}/export", handler=export)
    router.add("POST", f"/api/v1/runs/{RUN_ID}/pin", single(run(pinnedAt=TS)))
    router.add("DELETE", f"/api/v1/runs/{RUN_ID}/pin", single(run()))
    router.add("POST", f"/api/v1/runs/{RUN_ID}/purge", single(run(purgedAt=TS)))
    runs = Runs(router.client())
    assert runs.diff(RUN_ID, baseline_run_id=RUN_ID_2).baseline_kind == "last_pass"
    assert router.calls[0].url.params["baselineRunId"] == RUN_ID_2
    assert runs.export(RUN_ID) == b"PK\x03\x04zip"
    assert runs.pin(RUN_ID).pinned_at is not None
    assert runs.unpin(RUN_ID).pinned_at is None
    runs.purge(RUN_ID, reason="customer request")
    assert body_of(router.calls[-1]) == {"reason": "customer request"}


def test_run_artifacts(router: Router, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = {
        "id": ART,
        "organizationId": 1,
        "runId": RUN_ID,
        "kind": "screenshot",
        "lifecycle": "available",
        "createdAt": TS,
    }
    router.add("GET", f"/api/v1/runs/{RUN_ID}/artifacts", table([artifact]))
    router.add(
        "GET",
        f"/api/v1/artifacts/{ART}/download",
        single({"url": "https://files.example/shot.png", "expiresAt": TS}),
    )
    downloaded: list[str] = []

    def fake_get(_self: httpx.Client, url: str, **_kwargs: Any) -> httpx.Response:
        downloaded.append(url)
        return httpx.Response(200, content=b"\x89PNG")

    runs = Runs(router.client())
    assert runs.artifacts.list(RUN_ID)[0].kind == "screenshot"
    assert runs.artifacts.link(ART).url == "https://files.example/shot.png"
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    assert runs.artifacts.download(ART) == b"\x89PNG"
    assert downloaded == ["https://files.example/shot.png"]
    # The signed URL is fetched without the API token.
    assert all("files.example" not in str(r.url) for r in router.calls)


def test_run_wait_follows_the_event_stream(router: Router) -> None:
    phases = iter(["running", "finished"])

    def get_run(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=single(run(phase=next(phases))))

    def events(_req: httpx.Request) -> httpx.Response:
        stream = (
            'id: 1\ndata: {"type": "phase", "payload": {"phase": "running"}}\n\n'
            'id: 2\ndata: {"type": "finished", "payload": {}}\n\n'
        )
        return httpx.Response(
            200, content=stream.encode(), headers={"content-type": "text/event-stream"}
        )

    router.add("GET", f"/api/v1/runs/{RUN_ID}", handler=get_run)
    router.add("GET", f"/api/v1/runs/{RUN_ID}/events", handler=events)
    out = Runs(router.client()).wait(RUN_ID, timeout_ms=5_000)
    assert out.phase == "finished"
    assert router.paths().count(("GET", f"/api/v1/runs/{RUN_ID}/events")) == 1


# -- bundles / runtimes / account / audit ------------------------------------


def test_bundles_create_and_check(router: Router) -> None:
    files = {"a.spec.ts": b"import './b'\n", "b.ts": b"export {}\n"}

    def upload(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            201,
            json=single(
                {
                    "digest": CLOSURE,
                    "uploadDigest": bundle_digest(files),
                    "files": sorted(files),
                    "keys": [],
                    "size": 20,
                }
            ),
        )

    router.add("POST", "/api/v1/bundles", handler=upload)
    router.add(
        "POST",
        "/api/v1/bundles/check",
        single(
            {
                "findings": [
                    {
                        "code": "IMPORT_NOT_IN_BUNDLE",
                        "file": "a.spec.ts",
                        "line": 1,
                        "message": "x",
                    }
                ]
            }
        ),
    )
    bundles = Bundles(router.client())
    out = bundles.create(
        {"entrypoint": "a.spec.ts", "files": {k: v.decode() for k, v in files.items()}},
        runtime_id="2026.11",
    )
    assert out.digest == CLOSURE
    assert body_of(router.calls[0])["runtimeId"] == "2026.11"
    result = bundles.check({"a.spec.ts": "import './c'"}, entrypoint="a.spec.ts")
    assert result.findings[0].code == "IMPORT_NOT_IN_BUNDLE"
    assert body_of(router.calls[1]) == {
        "files": {"a.spec.ts": "import './c'"},
        "entrypoint": "a.spec.ts",
    }


def test_bundles_refuse_dotfiles_client_side(router: Router) -> None:
    with pytest.raises(ValidationError) as exc:
        Bundles(router.client()).create(
            {"entrypoint": "a.spec.ts", "files": {"a.spec.ts": "", ".env": "X=1"}}
        )
    assert exc.value.code == "MONITOR_PACKAGE_PATH_INVALID"
    assert router.calls == []


def test_runtimes(router: Router) -> None:
    profile = {
        "id": "2026.11",
        "nodeVersion": "22",
        "playwrightVersion": "1.56",
        "status": "available",
    }
    router.add("GET", "/api/v1/synthetics/runtime-profiles", table([profile]))
    router.add("GET", "/api/v1/synthetics/runtime-profiles/2026.11", single(profile))
    runtimes = Runtimes(router.client())
    assert runtimes.list()[0].id == "2026.11"
    assert runtimes.get("2026.11").status == "available"


def test_account(router: Router) -> None:
    meter = {"used": 3, "testRuns": 1}
    router.add(
        "GET",
        "/api/v1/synthetics/usage",
        single(
            {
                "periodStart": TS,
                "periodEnd": TS,
                "browser": meter,
                "api": meter,
                "monitors": [],
            }
        ),
    )
    router.add(
        "GET",
        "/api/v1/entitlements",
        single(
            {
                "tier": "FREE",
                "entitlements": {},
                "usage": {},
                "usagePeriodStart": TS,
                "trialActive": False,
            }
        ),
    )
    account = Account(router.client())
    assert account.usage().browser.used == 3
    assert account.entitlements().tier == "FREE"


def test_audit_list_params(router: Router) -> None:
    router.add(
        "GET",
        "/api/v1/audit-log",
        table([{"id": 1, "action": "monitor.publish", "createdAt": TS}]),
    )
    page = Audit(router.client()).list(
        action="monitor.publish", resource_id=MID, size=10
    )
    assert page.data[0].action == "monitor.publish"
    params = router.calls[0].url.params
    assert params["action"] == "monitor.publish"
    assert params["resourceId"] == MID
    assert params["size"] == "10"
    assert "actorId" not in params


# -- secrets ---------------------------------------------------------------


def test_secrets_list_environment_usage_values(router: Router) -> None:
    secret = {
        "id": MID,
        "key": "CARD_TOKEN",
        "dekVersion": 1,
        "valueHash": "h",
        "createdAt": TS,
        "updatedAt": TS,
    }
    router.add(
        "GET", "/api/v1/environments/staging", single(environment(slug="staging"))
    )
    router.add("GET", "/api/v1/secrets", table([secret]))
    router.add(
        "GET", "/api/v1/secrets/CARD_TOKEN/usage", single({"monitors": [monitor()]})
    )
    router.add("PUT", f"/api/v1/secrets/CARD_TOKEN/environments/{ENV}", status=204)
    router.add("DELETE", f"/api/v1/secrets/CARD_TOKEN/environments/{ENV}", status=204)
    secrets = Secrets(router.client())
    assert secrets.list(environment="staging")[0].key == "CARD_TOKEN"
    assert router.last("GET", "/api/v1/secrets").url.params["environmentId"] == ENV
    assert len(secrets.usage("CARD_TOKEN").monitors) == 1
    secrets.values.set("CARD_TOKEN", environment=ENV, value="tok_123")
    put = router.last("PUT", f"/api/v1/secrets/CARD_TOKEN/environments/{ENV}")
    assert body_of(put) == {"value": "tok_123"}
    assert "tok_123" not in str(put.url)
    secrets.values.delete("CARD_TOKEN", environment=ENV)
    assert router.paths()[-1] == (
        "DELETE",
        f"/api/v1/secrets/CARD_TOKEN/environments/{ENV}",
    )


# -- incidents -------------------------------------------------------------


def _incident() -> dict[str, object]:
    return {
        "id": INC,
        "organizationId": 1,
        "status": "CONFIRMED",
        "severity": "DOWN",
        "source": "AUTOMATIC",
        "affectedRegions": [],
        "reopenCount": 0,
        "statusPageVisible": False,
        "suppressDispatch": False,
        "createdAt": TS,
        "updatedAt": TS,
    }


def test_incident_extensions(router: Router) -> None:
    detail = single({"incident": _incident(), "updates": []})
    base = f"/api/v1/incidents/{INC}"
    router.add("PATCH", base, detail)
    router.add(
        "POST", f"{base}/acknowledge", single({"acknowledged": [], "skipped": []})
    )
    router.add("POST", f"{base}/updates", detail, status=201)
    router.add("GET", f"{base}/runs", cursor([run()]))
    router.add(
        "GET",
        f"{base}/events",
        cursor([{"id": ROW, "at": TS, "kind": "opened", "summary": "opened"}]),
    )
    router.add("GET", f"{base}/related", {"data": [_incident()], "total": 1})
    router.add("GET", f"{base}/trigger", single({"source": "run"}))
    incidents = Incidents(router.client())
    incidents.update(INC, title="Checkout down")
    assert body_of(router.calls[0]) == {"title": "Checkout down"}
    assert incidents.acknowledge(INC).acknowledged == []
    # The request model has a ``body`` field, which collides with the
    # method's ``body`` parameter, so pass it as a mapping.
    incidents.add_update(INC, {"body": "Investigating"}, notify_subscribers=False)
    assert body_of(router.calls[2]) == {
        "body": "Investigating",
        "notifySubscribers": False,
    }
    assert len(incidents.runs(INC, limit=5).data) == 1
    assert router.calls[3].url.params["limit"] == "5"
    assert incidents.events(INC).data[0].kind == "opened"
    assert incidents.related(INC, window_days=7).total == 1
    assert router.calls[5].url.params["windowDays"] == "7"
    assert "limit" not in router.calls[5].url.params
    assert incidents.trigger(INC).source == "run"


# -- status pages ----------------------------------------------------------


def test_component_override(router: Router) -> None:
    component = {
        "id": COMP,
        "statusPageId": PAGE,
        "name": "API",
        "type": "STATIC",
        "currentStatus": "OPERATIONAL",
        "showUptime": True,
        "displayOrder": 0,
        "pageOrder": 0,
        "excludeFromOverall": False,
        "createdAt": TS,
        "updatedAt": TS,
    }
    path = f"/api/v1/status-pages/{PAGE}/components/{COMP}/override"
    router.add("PUT", path, single(component))
    router.add("DELETE", path, single(component))
    components = StatusPages(router.client()).components
    components.set_override(PAGE, COMP, status="MAJOR_OUTAGE", expires_at=TS)
    assert body_of(router.calls[0]) == {"status": "MAJOR_OUTAGE", "expiresAt": TS}
    components.clear_override(PAGE, COMP)
    assert router.paths()[-1] == ("DELETE", path)
