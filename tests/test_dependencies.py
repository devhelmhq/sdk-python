"""Tests for the ``Dependencies`` resource module (service subscriptions).

Same shape as ``test_maintenance_windows``: a capturing
``httpx.MockTransport`` plus assertions on the wire-level method, URL, and
JSON body — locking in the contract that ``track`` only sends a body when
the caller actually provided subscription options.
"""

from __future__ import annotations

import json

import httpx
import pytest

from devhelm.resources.dependencies import Dependencies

_SUBSCRIPTION = {
    "subscriptionId": "11111111-1111-1111-1111-111111111111",
    "serviceId": "22222222-2222-2222-2222-222222222222",
    "slug": "github",
    "name": "GitHub",
    "adapterType": "statuspage",
    "pollingIntervalSeconds": 300,
    "enabled": True,
    "alertSensitivity": "AWARENESS",
    "subscribedAt": "2026-06-01T00:00:00Z",
}


def _stub_transport(captured: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        method = request.method
        path = request.url.path
        if method == "POST" and path.startswith("/api/v1/service-subscriptions/"):
            return httpx.Response(201, json={"data": _SUBSCRIPTION})
        if method == "PATCH" and path.endswith("/alert-sensitivity"):
            return httpx.Response(
                200, json={"data": {**_SUBSCRIPTION, "alertSensitivity": "MAJOR_ONLY"}}
            )
        raise AssertionError(f"unexpected {method} {path}")

    return httpx.MockTransport(handler)


def _resource(transport: httpx.MockTransport) -> Dependencies:
    http_client = httpx.Client(transport=transport, base_url="http://localhost:8080")
    return Dependencies(http_client)


# ---------------------------------------------------------------------------
# track — body presence/shape contract
# ---------------------------------------------------------------------------


class TestTrack:
    def test_track_without_options_sends_no_body(self) -> None:
        """The bare ``track(slug)`` call predates the optional body — it
        must keep producing a body-less POST so the API's defaults apply
        unchanged (whole-service subscription, AWARENESS sensitivity).
        """
        captured: list[httpx.Request] = []
        deps = _resource(_stub_transport(captured))

        result = deps.track("github")

        assert len(captured) == 1
        request = captured[0]
        assert request.method == "POST"
        assert request.url.path == "/api/v1/service-subscriptions/github"
        assert request.content == b""
        assert result.slug == "github"

    def test_track_with_options_sends_json_body(self) -> None:
        captured: list[httpx.Request] = []
        deps = _resource(_stub_transport(captured))

        deps.track(
            "github",
            component_id="33333333-3333-3333-3333-333333333333",
            alert_sensitivity="INCIDENTS_ONLY",
        )

        assert len(captured) == 1
        body = json.loads(captured[0].content)
        assert body == {
            "componentId": "33333333-3333-3333-3333-333333333333",
            "alertSensitivity": "INCIDENTS_ONLY",
        }

    def test_track_with_only_sensitivity_omits_component_key(self) -> None:
        captured: list[httpx.Request] = []
        deps = _resource(_stub_transport(captured))

        deps.track("github", alert_sensitivity="ALL")

        body = json.loads(captured[0].content)
        # ``componentId`` must be absent (not ``null``) so the API treats
        # this as a whole-service subscription.
        assert body == {"alertSensitivity": "ALL"}

    def test_track_rejects_invalid_sensitivity_before_http(self) -> None:
        captured: list[httpx.Request] = []
        deps = _resource(_stub_transport(captured))

        with pytest.raises(Exception, match="Request validation failed"):
            deps.track("github", alert_sensitivity="wrong")
        assert captured == []


# ---------------------------------------------------------------------------
# update_alert_sensitivity — verb, URL, body, envelope unwrap
# ---------------------------------------------------------------------------


class TestUpdateAlertSensitivity:
    def test_update_patches_alert_sensitivity_endpoint(self) -> None:
        captured: list[httpx.Request] = []
        deps = _resource(_stub_transport(captured))

        result = deps.update_alert_sensitivity(
            "11111111-1111-1111-1111-111111111111", "MAJOR_ONLY"
        )

        assert len(captured) == 1
        request = captured[0]
        assert request.method == "PATCH"
        assert request.url.path == (
            "/api/v1/service-subscriptions/"
            "11111111-1111-1111-1111-111111111111/alert-sensitivity"
        )
        assert json.loads(request.content) == {"alertSensitivity": "MAJOR_ONLY"}
        assert result.alert_sensitivity == "MAJOR_ONLY"

    def test_update_rejects_invalid_sensitivity_before_http(self) -> None:
        captured: list[httpx.Request] = []
        deps = _resource(_stub_transport(captured))

        with pytest.raises(Exception, match="Request validation failed"):
            deps.update_alert_sensitivity("11111111", "sometimes")
        assert captured == []
