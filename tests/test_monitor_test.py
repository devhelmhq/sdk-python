"""Tests for ``Monitors.test`` and ``Monitors.test_run``.

``POST /api/v1/monitors/{id}/test`` answers 200 with the probe result for
uptime monitors and 202 with a queued validation run for browser and
multi-step API monitors. ``test()`` returns the probe result and raises
``DevhelmMonitorTestQueuedError`` on 202; ``test_run()`` returns the run and
sends the optional target body only when given.
"""

from __future__ import annotations

import json

import httpx
import pytest

from devhelm import (
    DevhelmApiError,
    DevhelmMonitorTestQueuedError,
    DevhelmValidationError,
    MonitorTestResultDto,
    RunDto,
)
from devhelm.resources.monitors import Monitors

MONITOR_ID = "550e8400-e29b-41d4-a716-446655440000"

_PROBE_RESULT: dict[str, object] = {
    "passed": True,
    "error": None,
    "statusCode": 200,
    "responseTimeMs": 42,
    "responseHeaders": {"content-type": ["application/json"]},
    "bodyPreview": '{"ok":true}',
    "responseSizeBytes": 11,
    "redirectCount": 0,
    "finalUrl": "https://example.com/health",
    "assertionResults": [],
    "warnings": None,
}

_QUEUED_RUN: dict[str, object] = {
    "id": "6f1c2a3b-4d5e-4f60-8a7b-9c0d1e2f3a4b",
    "organizationId": 1,
    "monitorId": MONITOR_ID,
    "monitorName": "Checkout flow",
    "monitorType": "BROWSER",
    "revisionId": "7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d",
    "region": "us-east",
    "source": "VALIDATION",
    "countsTowardHealth": False,
    "enqueuedAt": "2026-10-21T10:00:00Z",
    "phase": "QUEUED",
    "cancelRequested": False,
    "bundleDigest": "sha256:abc",
    "capturePolicySnapshot": {},
    "bindingVersionSnapshot": {},
    "stream": False,
    "evidence": [],
    "tabCounts": {"steps": 0, "assets": 0, "diff": 0},
    "attempt": 1,
    "attemptOf": 1,
    "attempts": [],
    "executionAttempts": [],
    "billable": False,
}


def _monitors(
    captured: list[httpx.Request], status: int, body: dict[str, object]
) -> Monitors:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/monitors/{MONITOR_ID}/test"
        return httpx.Response(status, json=body)

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://localhost:8080"
    )
    return Monitors(client)


def test_test_returns_probe_result_on_200() -> None:
    captured: list[httpx.Request] = []
    out = _monitors(captured, 200, {"data": _PROBE_RESULT}).test(MONITOR_ID)
    assert isinstance(out, MonitorTestResultDto)
    assert out.passed is True
    assert out.status_code == 200
    assert captured[0].content == b""


def test_test_raises_queued_error_on_202_with_the_run() -> None:
    captured: list[httpx.Request] = []
    with pytest.raises(DevhelmMonitorTestQueuedError) as exc:
        _monitors(captured, 202, {"data": _QUEUED_RUN}).test(MONITOR_ID)
    # Same base class code monitors got before the API queued runs.
    assert isinstance(exc.value, DevhelmValidationError)
    assert str(exc.value.run.id) == _QUEUED_RUN["id"]
    assert "monitors.test_run()" in str(exc.value)


def test_test_still_rejects_a_200_body_that_is_not_a_probe_result() -> None:
    captured: list[httpx.Request] = []
    with pytest.raises(DevhelmValidationError):
        _monitors(captured, 200, {"data": _QUEUED_RUN}).test(MONITOR_ID)


def test_test_run_returns_run_on_202() -> None:
    captured: list[httpx.Request] = []
    out = _monitors(captured, 202, {"data": _QUEUED_RUN}).test_run(MONITOR_ID)
    assert isinstance(out, RunDto)
    assert str(out.id) == _QUEUED_RUN["id"]
    assert out.counts_toward_health is False
    assert captured[0].content == b""


def test_test_run_sends_target_body_when_given() -> None:
    captured: list[httpx.Request] = []
    env_id = "8b9c0d1e-2f3a-4b4c-9d5e-6f7a8b9c0d1e"
    _monitors(captured, 202, {"data": _QUEUED_RUN}).test_run(
        MONITOR_ID, {"environmentId": env_id, "region": "eu-west"}
    )
    assert json.loads(captured[0].content) == {
        "environmentId": env_id,
        "region": "eu-west",
    }


def test_test_run_rejects_unknown_target_key_before_sending() -> None:
    captured: list[httpx.Request] = []
    monitors = _monitors(captured, 202, {"data": _QUEUED_RUN})
    with pytest.raises(DevhelmValidationError):
        monitors.test_run(MONITOR_ID, {"region": "eu-west", "regoin": "typo"})
    assert captured == []


def test_test_run_rejects_probe_result_and_names_test() -> None:
    captured: list[httpx.Request] = []
    with pytest.raises(DevhelmValidationError, match=r"use monitors\.test\(\)"):
        _monitors(captured, 200, {"data": _PROBE_RESULT}).test_run(MONITOR_ID)


def test_test_run_decodes_additive_run_fields() -> None:
    captured: list[httpx.Request] = []
    body = {"data": {**_QUEUED_RUN, "phase": "FUTURE_PHASE", "newField": 1}}
    out = _monitors(captured, 202, body).test_run(MONITOR_ID)
    assert out.phase == "FUTURE_PHASE"


def test_error_body_keeps_unknown_category_and_next_keys() -> None:
    captured: list[httpx.Request] = []
    error = {
        "status": 429,
        "code": "SOMETHING_NEW",
        "category": "future_category",
        "retryable": True,
        "message": "Slow down",
        "timestamp": 1700000000000,
        "next": {"command": "devhelm account usage", "docs": None, "video": "x"},
    }
    with pytest.raises(DevhelmApiError) as exc:
        _monitors(captured, 429, error).test(MONITOR_ID)
    assert exc.value.code == "SOMETHING_NEW"


def test_error_response_model_decodes_unknown_category_and_next_keys() -> None:
    # Postel's Law: ErrorCategory and ErrorNext are reached only from
    # ErrorResponse, so the generated models accept values and keys this
    # SDK has never seen.
    from devhelm._generated import ErrorResponse

    parsed = ErrorResponse.model_validate(
        {
            "status": 429,
            "code": "SOMETHING_NEW",
            "category": "future_category",
            "retryable": True,
            "message": "Slow down",
            "timestamp": 1700000000000,
            "next": {"command": "devhelm account usage", "docs": None, "video": "x"},
        }
    )
    assert parsed.category.root == "future_category"
    assert parsed.next is not None
    assert parsed.next.command == "devhelm account usage"
