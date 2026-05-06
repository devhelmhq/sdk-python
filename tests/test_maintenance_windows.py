"""Tests for the ``MaintenanceWindows`` resource module.

The shape of these tests mirrors ``test_client.TestMonitorsListFilters``:
spin up an ``httpx.MockTransport``, point a real resource instance at it,
and assert the resulting ``httpx.Request`` carries the wire-level URL,
method, query-string, and JSON body the API documents.

The aim is twofold:

* Confirm that ergonomic snake_case kwargs (``monitor_id``, ``status``)
  are projected onto the camelCase / API-specific names
  (``monitorId``, ``filter``) the server expects.
* Lock in the URL-and-verb contract for ``create`` / ``update`` /
  ``delete`` / ``cancel`` so a future refactor can't silently change
  what the SDK sends to production.
"""

from __future__ import annotations

import json

import httpx
import pytest

from devhelm.resources.maintenance_windows import MaintenanceWindows

# ---------------------------------------------------------------------------
# Fixtures: shared mock transport + resource builder
# ---------------------------------------------------------------------------


_VALID_WINDOW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "monitorId": "22222222-2222-2222-2222-222222222222",
    "organizationId": 1,
    "startsAt": "2026-06-01T00:00:00Z",
    "endsAt": "2026-06-01T02:00:00Z",
    "repeatRule": None,
    "reason": "Quarterly DB upgrade",
    "suppressAlerts": True,
    "createdAt": "2026-05-01T12:00:00Z",
}


def _stub_transport(
    captured: list[httpx.Request],
    *,
    list_response: dict[str, object] | None = None,
    single_response: dict[str, object] | None = None,
    delete_status: int = 204,
) -> httpx.MockTransport:
    """Capture every outgoing request and return JSON shaped like the API.

    Routes to the right canned response based on method + path so a
    single transport can serve every test below without each test having
    to define its own handler.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        method = request.method
        path = request.url.path
        if method == "GET" and path == "/api/v1/maintenance-windows":
            body = list_response or {
                "data": [_VALID_WINDOW],
                "hasNext": False,
                "hasPrev": False,
            }
            return httpx.Response(200, json=body)
        if method == "GET" and path.startswith("/api/v1/maintenance-windows/"):
            return httpx.Response(200, json=single_response or {"data": _VALID_WINDOW})
        if method == "POST" and path == "/api/v1/maintenance-windows":
            return httpx.Response(201, json=single_response or {"data": _VALID_WINDOW})
        if method == "PUT" and path.startswith("/api/v1/maintenance-windows/"):
            return httpx.Response(200, json=single_response or {"data": _VALID_WINDOW})
        if method == "DELETE" and path.startswith("/api/v1/maintenance-windows/"):
            return httpx.Response(delete_status)
        # Surface routing mistakes loudly rather than silently 404'ing.
        raise AssertionError(f"unexpected {method} {path}")

    return httpx.MockTransport(handler)


def _resource(transport: httpx.MockTransport) -> MaintenanceWindows:
    http_client = httpx.Client(transport=transport, base_url="http://localhost:8080")
    return MaintenanceWindows(http_client)


# ---------------------------------------------------------------------------
# list / list_page — query-param threading
# ---------------------------------------------------------------------------


class TestList:
    """The two documented filters (``monitorId``, ``filter``) must reach
    the wire under their server-expected names so callers don't have to
    drop down to ``httpx`` for server-side filtering.
    """

    def test_list_threads_filters_to_query_string(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        windows.list(
            monitor_id="22222222-2222-2222-2222-222222222222", status="upcoming"
        )

        assert len(captured) == 1
        params = captured[0].url.params
        # snake_case ``monitor_id`` must be projected onto camelCase wire
        # name; ergonomic ``status`` kwarg must map to API's ``filter`` key.
        assert params["monitorId"] == "22222222-2222-2222-2222-222222222222"
        assert params["filter"] == "upcoming"

    def test_list_omits_unspecified_filters(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        windows.list()

        assert len(captured) == 1
        params = captured[0].url.params
        assert "monitorId" not in params
        assert "filter" not in params
        # Pagination keys are always sent so ``fetch_all_pages`` can drive
        # the iterator deterministically.
        assert params["page"] == "0"

    def test_list_returns_parsed_models(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        result = windows.list()

        assert len(result) == 1
        assert str(result[0].id) == "11111111-1111-1111-1111-111111111111"
        assert result[0].reason == "Quarterly DB upgrade"

    def test_list_page_threads_filters(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        page = windows.list_page(2, 50, monitor_id="abc", status="active")

        assert page.total_elements is None  # not returned by stub
        assert len(captured) == 1
        params = captured[0].url.params
        assert params["monitorId"] == "abc"
        assert params["filter"] == "active"
        assert params["page"] == "2"
        assert params["size"] == "50"


# ---------------------------------------------------------------------------
# get — URL templating + envelope unwrap
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_hits_resource_url(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        result = windows.get("11111111-1111-1111-1111-111111111111")

        assert len(captured) == 1
        assert captured[0].method == "GET"
        assert (
            captured[0].url.path
            == "/api/v1/maintenance-windows/11111111-1111-1111-1111-111111111111"
        )
        assert str(result.id) == "11111111-1111-1111-1111-111111111111"


# ---------------------------------------------------------------------------
# create — body validation + JSON shape
# ---------------------------------------------------------------------------


class TestCreate:
    def test_create_posts_validated_body(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        result = windows.create(
            {
                "startsAt": "2026-06-01T00:00:00Z",
                "endsAt": "2026-06-01T02:00:00Z",
                "reason": "Quarterly DB upgrade",
                "monitorId": "22222222-2222-2222-2222-222222222222",
                "suppressAlerts": True,
            }
        )

        assert len(captured) == 1
        request = captured[0]
        assert request.method == "POST"
        assert request.url.path == "/api/v1/maintenance-windows"
        body = json.loads(request.content)
        # Keys go on the wire as the camelCase aliases the API documents.
        assert body["startsAt"] == "2026-06-01T00:00:00Z"
        assert body["endsAt"] == "2026-06-01T02:00:00Z"
        assert body["reason"] == "Quarterly DB upgrade"
        assert body["monitorId"] == "22222222-2222-2222-2222-222222222222"
        assert body["suppressAlerts"] is True
        # The ``data`` envelope must be unwrapped into a typed model so
        # callers don't get a raw dict.
        assert str(result.id) == "11111111-1111-1111-1111-111111111111"

    def test_create_rejects_missing_required_fields(self) -> None:
        # Missing ``endsAt`` — Pydantic must reject before the HTTP call,
        # so ``captured`` stays empty.
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        # ``DevhelmValidationError`` extends ``DevhelmError`` which extends
        # ``Exception``; checking for ``Exception`` keeps the assertion
        # robust against future re-shuffles of the error hierarchy while
        # still ensuring *something* failed loudly before any network IO.
        with pytest.raises(Exception, match="Request validation failed"):
            windows.create({"startsAt": "2026-06-01T00:00:00Z"})
        assert captured == []


# ---------------------------------------------------------------------------
# update — URL templating + body shape
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_update_puts_to_resource_url(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        windows.update(
            "11111111-1111-1111-1111-111111111111",
            {
                "startsAt": "2026-06-02T00:00:00Z",
                "endsAt": "2026-06-02T02:00:00Z",
                "reason": "Rescheduled DB upgrade",
            },
        )

        assert len(captured) == 1
        request = captured[0]
        assert request.method == "PUT"
        assert (
            request.url.path
            == "/api/v1/maintenance-windows/11111111-1111-1111-1111-111111111111"
        )
        body = json.loads(request.content)
        assert body["startsAt"] == "2026-06-02T00:00:00Z"
        assert body["reason"] == "Rescheduled DB upgrade"


# ---------------------------------------------------------------------------
# delete / cancel — both must hit the same endpoint
# ---------------------------------------------------------------------------


class TestDeleteAndCancel:
    """``cancel`` is a thin alias for ``delete`` so users can pick the
    verb that reads better in their automation script. They must produce
    identical wire requests.
    """

    def test_delete_hits_resource_url(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        result = windows.delete("11111111-1111-1111-1111-111111111111")

        assert result is None
        assert len(captured) == 1
        assert captured[0].method == "DELETE"
        assert (
            captured[0].url.path
            == "/api/v1/maintenance-windows/11111111-1111-1111-1111-111111111111"
        )

    def test_cancel_aliases_delete(self) -> None:
        captured: list[httpx.Request] = []
        windows = _resource(_stub_transport(captured))

        windows.cancel("11111111-1111-1111-1111-111111111111")

        assert len(captured) == 1
        assert captured[0].method == "DELETE"
        assert (
            captured[0].url.path
            == "/api/v1/maintenance-windows/11111111-1111-1111-1111-111111111111"
        )
