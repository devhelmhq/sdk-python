"""HTTP contract tests for ``client.status_pages.maintenance``.

Locks the split from mono #875: maintenance goes to
``/api/v1/status-pages/{id}/maintenance``, never ``/incidents``.
"""

from __future__ import annotations

import json

import httpx
import pytest

from devhelm._errors import DevhelmValidationError
from devhelm.resources.status_pages import _Maintenance

_PAGE = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_WINDOW = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

_VALID_WINDOW = {
    "id": _WINDOW,
    "statusPageId": _PAGE,
    "title": "DB upgrade",
    "status": "SCHEDULED",
    "impact": "MINOR",
    "scheduled": True,
    "scheduledFor": "2026-08-24T02:00:00Z",
    "scheduledUntil": "2026-08-24T04:00:00Z",
    "autoResolve": False,
    "startedAt": "2026-08-24T02:00:00Z",
    "createdAt": "2026-08-23T12:00:00Z",
    "updatedAt": "2026-08-23T12:00:00Z",
}

_CREATE_BODY = {
    "title": "DB upgrade",
    "impact": "MINOR",
    "body": "We'll be upgrading the primary database.",
    "scheduledFor": "2026-08-24T02:00:00Z",
}


def _stub_transport(captured: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        method = request.method
        path = request.url.path
        prefix = f"/api/v1/status-pages/{_PAGE}/maintenance"
        if method == "GET" and path == prefix:
            return httpx.Response(
                200,
                json={"data": [_VALID_WINDOW], "hasNext": False, "hasPrev": False},
            )
        if method == "POST" and path == prefix:
            return httpx.Response(201, json={"data": _VALID_WINDOW})
        if method == "GET" and path == f"{prefix}/{_WINDOW}":
            return httpx.Response(200, json={"data": _VALID_WINDOW})
        if method == "PUT" and path == f"{prefix}/{_WINDOW}":
            return httpx.Response(200, json={"data": _VALID_WINDOW})
        if method == "POST" and path == f"{prefix}/{_WINDOW}/publish":
            return httpx.Response(200, json={"data": _VALID_WINDOW})
        if method == "POST" and path == f"{prefix}/{_WINDOW}/updates":
            return httpx.Response(200, json={"data": _VALID_WINDOW})
        if method == "POST" and path == f"{prefix}/{_WINDOW}/dismiss":
            return httpx.Response(204)
        if method == "DELETE" and path == f"{prefix}/{_WINDOW}":
            return httpx.Response(204)
        raise AssertionError(f"unexpected {method} {path}")

    return httpx.MockTransport(handler)


def _resource(transport: httpx.MockTransport) -> _Maintenance:
    http_client = httpx.Client(transport=transport, base_url="http://localhost:8080")
    return _Maintenance(http_client)


class TestStatusPageMaintenance:
    def test_create_posts_to_maintenance_not_incidents(self) -> None:
        captured: list[httpx.Request] = []
        maintenance = _resource(_stub_transport(captured))

        result = maintenance.create(_PAGE, _CREATE_BODY)

        assert len(captured) == 1
        request = captured[0]
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/status-pages/{_PAGE}/maintenance"
        assert "/incidents" not in request.url.path
        body = json.loads(request.content)
        assert body["title"] == "DB upgrade"
        assert body["impact"] == "MINOR"
        assert body["body"] == "We'll be upgrading the primary database."
        assert body["scheduledFor"] == "2026-08-24T02:00:00Z"
        assert str(result.id) == _WINDOW

    def test_create_rejects_missing_scheduled_for(self) -> None:
        captured: list[httpx.Request] = []
        maintenance = _resource(_stub_transport(captured))

        with pytest.raises(DevhelmValidationError, match="scheduledFor"):
            maintenance.create(
                _PAGE,
                {
                    "title": "DB upgrade",
                    "impact": "MINOR",
                    "body": "missing schedule",
                },
            )
        assert captured == []

    def test_list_gets_maintenance_collection(self) -> None:
        captured: list[httpx.Request] = []
        maintenance = _resource(_stub_transport(captured))

        page = maintenance.list(_PAGE)

        assert len(captured) == 1
        assert captured[0].method == "GET"
        assert captured[0].url.path == f"/api/v1/status-pages/{_PAGE}/maintenance"
        assert len(page.data) == 1
        assert str(page.data[0].id) == _WINDOW

    def test_publish_posts_maintenance_publish(self) -> None:
        captured: list[httpx.Request] = []
        maintenance = _resource(_stub_transport(captured))

        maintenance.publish(_PAGE, _WINDOW)

        assert len(captured) == 1
        assert captured[0].method == "POST"
        assert (
            captured[0].url.path
            == f"/api/v1/status-pages/{_PAGE}/maintenance/{_WINDOW}/publish"
        )

    def test_delete_hits_maintenance_window(self) -> None:
        captured: list[httpx.Request] = []
        maintenance = _resource(_stub_transport(captured))

        maintenance.delete(_PAGE, _WINDOW)

        assert len(captured) == 1
        assert captured[0].method == "DELETE"
        assert (
            captured[0].url.path
            == f"/api/v1/status-pages/{_PAGE}/maintenance/{_WINDOW}"
        )
