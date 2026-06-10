"""Tests for the ``Services`` resource module (Status Data catalog).

Mirrors ``test_maintenance_windows``: spin up an ``httpx.MockTransport``,
point a real ``Services`` instance at it, and assert the resulting
``httpx.Request`` carries the wire-level URL, method, and query string the
API documents — plus that responses are unwrapped into typed models.
"""

from __future__ import annotations

import httpx

from devhelm.resources.services import Services

# ---------------------------------------------------------------------------
# Fixtures: canned API payloads (camelCase wire shape)
# ---------------------------------------------------------------------------


_SERVICE = {
    "id": "11111111-1111-1111-1111-111111111111",
    "slug": "github",
    "name": "GitHub",
    "category": "Developer Tools",
    "adapterType": "statuspage",
    "pollingIntervalSeconds": 300,
    "lifecycleStatus": "ACTIVE",
    "enabled": True,
    "published": True,
    "overallStatus": "operational",
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-06-01T00:00:00Z",
    "componentCount": 5,
    "activeIncidentCount": 0,
    "dataCompleteness": "full",
}

_SERVICE_DETAIL = {
    "id": "11111111-1111-1111-1111-111111111111",
    "slug": "github",
    "name": "GitHub",
    "adapterType": "statuspage",
    "pollingIntervalSeconds": 300,
    "lifecycleStatus": "ACTIVE",
    "enabled": True,
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-06-01T00:00:00Z",
    "recentIncidents": [],
    "components": [],
    "activeMaintenances": [],
    "dataCompleteness": "full",
}

_INCIDENT = {
    "id": "33333333-3333-3333-3333-333333333333",
    "serviceId": "11111111-1111-1111-1111-111111111111",
    "serviceSlug": "github",
    "title": "Elevated API error rates",
    "status": "resolved",
}


def _table(items: list[dict[str, object]]) -> dict[str, object]:
    return {"data": items, "hasNext": False, "hasPrev": False}


def _stub_transport(captured: list[httpx.Request]) -> httpx.MockTransport:
    """Capture every outgoing request and return JSON shaped like the API.

    Routes on method + path so a single transport serves every test below;
    routing mistakes surface loudly instead of silently 404'ing.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        path = request.url.path
        if request.method != "GET":
            raise AssertionError(f"unexpected {request.method} {path}")
        if path == "/api/v1/services":
            return httpx.Response(
                200, json={"data": [_SERVICE], "nextCursor": "abc123", "hasMore": True}
            )
        if path == "/api/v1/categories":
            return httpx.Response(
                200, json=_table([{"category": "Developer Tools", "serviceCount": 12}])
            )
        if path == "/api/v1/services/incidents" or path.endswith("/incidents"):
            return httpx.Response(200, json=_table([_INCIDENT]))
        if path.endswith("/live-status"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "overallStatus": "operational",
                        "componentStatuses": [],
                        "activeIncidentCount": 0,
                    }
                },
            )
        if path.endswith("/uptime"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "overallUptimePct": 99.95,
                        "period": "30d",
                        "granularity": "daily",
                        "buckets": [],
                    }
                },
            )
        if path == "/api/v1/services/github":
            return httpx.Response(200, json={"data": _SERVICE_DETAIL})
        raise AssertionError(f"unexpected GET {path}")

    return httpx.MockTransport(handler)


def _resource(transport: httpx.MockTransport) -> Services:
    http_client = httpx.Client(transport=transport, base_url="http://localhost:8080")
    return Services(http_client)


# ---------------------------------------------------------------------------
# list — cursor pagination + filter threading
# ---------------------------------------------------------------------------


class TestList:
    def test_list_threads_filters_to_query_string(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        services.list(
            category="Developer Tools",
            status="operational",
            search="git",
            cursor="cursor-1",
            limit=50,
        )

        assert len(captured) == 1
        params = captured[0].url.params
        assert params["category"] == "Developer Tools"
        assert params["status"] == "operational"
        assert params["search"] == "git"
        assert params["cursor"] == "cursor-1"
        assert params["limit"] == "50"

    def test_list_omits_unspecified_filters(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        services.list()

        assert len(captured) == 1
        params = captured[0].url.params
        assert "category" not in params
        assert "status" not in params
        assert "search" not in params
        assert "cursor" not in params
        # The default page size is always sent so server defaults can't
        # silently drift under the SDK's documented signature.
        assert params["limit"] == "20"

    def test_list_returns_cursor_page(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        page = services.list(search="git")

        assert len(page.data) == 1
        assert page.data[0].slug == "github"
        assert page.data[0].lifecycle_status == "ACTIVE"
        assert page.next_cursor == "abc123"
        assert page.has_more is True


# ---------------------------------------------------------------------------
# get — URL templating, summary flag, envelope unwrap
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_hits_resource_url_and_unwraps(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        result = services.get("github")

        assert len(captured) == 1
        assert captured[0].url.path == "/api/v1/services/github"
        # Default mode must not send ``summary`` so the API's full payload
        # behaviour applies.
        assert "summary" not in captured[0].url.params
        assert result.slug == "github"
        assert result.adapter_type == "statuspage"

    def test_get_summary_flag_reaches_wire(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        services.get("github", summary=True)

        assert captured[0].url.params["summary"] == "true"


# ---------------------------------------------------------------------------
# incidents — dual-mode routing (per-service vs cross-service)
# ---------------------------------------------------------------------------


class TestIncidents:
    def test_incidents_with_slug_hits_per_service_endpoint(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        page = services.incidents("github", status="resolved", from_="2026-05-01")

        assert len(captured) == 1
        request = captured[0]
        assert request.url.path == "/api/v1/services/github/incidents"
        assert request.url.params["status"] == "resolved"
        assert request.url.params["from"] == "2026-05-01"
        assert request.url.params["page"] == "0"
        assert request.url.params["size"] == "20"
        assert len(page.data) == 1
        assert page.data[0].title == "Elevated API error rates"

    def test_incidents_without_slug_hits_cross_service_endpoint(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        services.incidents(category="Developer Tools", page=2, size=50)

        assert len(captured) == 1
        request = captured[0]
        assert request.url.path == "/api/v1/services/incidents"
        assert request.url.params["category"] == "Developer Tools"
        assert request.url.params["page"] == "2"
        assert request.url.params["size"] == "50"


# ---------------------------------------------------------------------------
# Singleton + table endpoints — URL contract and envelope handling
# ---------------------------------------------------------------------------


class TestSingleAndTableEndpoints:
    def test_live_status(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        result = services.live_status("github")

        assert captured[0].url.path == "/api/v1/services/github/live-status"
        assert result.overall_status == "operational"

    def test_categories_unwraps_table_envelope(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        result = services.categories()

        assert captured[0].url.path == "/api/v1/categories"
        # Not a paginated endpoint — no page/size noise on the wire.
        assert "page" not in captured[0].url.params
        assert len(result) == 1
        assert result[0].category == "Developer Tools"
        assert result[0].service_count == 12

    def test_uptime_sends_period_and_granularity(self) -> None:
        captured: list[httpx.Request] = []
        services = _resource(_stub_transport(captured))

        result = services.uptime("github", period="7d", granularity="hourly")

        assert captured[0].url.path == "/api/v1/services/github/uptime"
        assert captured[0].url.params["period"] == "7d"
        assert captured[0].url.params["granularity"] == "hourly"
        assert result.overall_uptime_pct == 99.95
