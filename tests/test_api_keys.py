"""Tests for the ``ApiKeys`` resource module.

Mirrors ``test_maintenance_windows`` / ``test_services``: spin up an
``httpx.MockTransport``, point a real ``ApiKeys`` instance at it, and
assert the resulting ``httpx.Request`` carries the wire-level URL and
method the API documents — plus that responses are unwrapped into typed
models.
"""

from __future__ import annotations

import httpx

from devhelm.resources.api_keys import ApiKeys

# ---------------------------------------------------------------------------
# Fixtures: canned API payload (camelCase wire shape)
# ---------------------------------------------------------------------------


_API_KEY = {
    "id": 42,
    "name": "CI pipeline",
    "key": "dh_live_abc123",
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-06-01T00:00:00Z",
    "lastUsedAt": None,
    "revokedAt": None,
    "expiresAt": None,
}


def _stub_transport(captured: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        method = request.method
        path = request.url.path
        if method == "GET" and path.startswith("/api/v1/api-keys/"):
            return httpx.Response(200, json={"data": _API_KEY})
        raise AssertionError(f"unexpected {method} {path}")

    return httpx.MockTransport(handler)


def _resource(transport: httpx.MockTransport) -> ApiKeys:
    http_client = httpx.Client(transport=transport, base_url="http://localhost:8080")
    return ApiKeys(http_client)


class TestGet:
    def test_get_is_callable(self) -> None:
        api_keys = _resource(_stub_transport([]))
        assert callable(api_keys.get)

    def test_get_hits_resource_url_and_unwraps(self) -> None:
        captured: list[httpx.Request] = []
        api_keys = _resource(_stub_transport(captured))

        result = api_keys.get(42)

        assert len(captured) == 1
        assert captured[0].method == "GET"
        assert captured[0].url.path == "/api/v1/api-keys/42"
        assert result.id == 42
        assert result.name == "CI pipeline"
        assert result.key == "dh_live_abc123"

    def test_get_encodes_path_param(self) -> None:
        captured: list[httpx.Request] = []
        api_keys = _resource(_stub_transport(captured))

        api_keys.get("a b")

        # ``url.path`` is percent-decoded by httpx; assert on the raw bytes
        # to confirm ``path_param`` encoded the space before it hit the wire.
        assert b"/api/v1/api-keys/a%20b" == captured[0].url.raw_path
