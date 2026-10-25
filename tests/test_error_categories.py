"""One typed error per ErrorResponse ``category`` (doc 32 D-1)."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

import devhelm
from devhelm import errors
from devhelm._errors import (
    AuthError,
    BlockedError,
    ConfirmationRequiredError,
    ConflictError,
    DevhelmApiError,
    DevhelmAuthError,
    DevhelmConflictError,
    DevhelmError,
    DevhelmNotFoundError,
    DevhelmRateLimitError,
    DevhelmServerError,
    DevhelmTransportError,
    GoneError,
    NotFoundError,
    OwnershipError,
    PermissionError,
    PlanLimitError,
    PlatformError,
    QuotaError,
    RateLimitError,
    TransportError,
    ValidationError,
    WaitTimeoutError,
    client_error,
    error_from_response,
)
from devhelm._generated import ErrorEntry, ErrorNext


def _envelope(status: int, category: str, code: str = "SOME_CODE") -> str:
    return json.dumps(
        {
            "status": status,
            "code": code,
            "category": category,
            "retryable": False,
            "message": f"{category} refusal",
            "timestamp": 1737302400000,
            "requestId": "req-1",
        }
    )


# (status, category, expected class, legacy base)
CASES: list[tuple[int, str, type[DevhelmApiError], type[DevhelmApiError]]] = [
    (400, "validation", ValidationError, DevhelmApiError),
    (409, "blocked", BlockedError, DevhelmConflictError),
    (401, "auth", AuthError, DevhelmAuthError),
    (403, "permission", PermissionError, DevhelmAuthError),
    (409, "ownership", OwnershipError, DevhelmConflictError),
    (402, "plan", PlanLimitError, DevhelmApiError),
    (402, "quota", QuotaError, DevhelmApiError),
    (429, "rate_limit", RateLimitError, DevhelmRateLimitError),
    (409, "conflict", ConflictError, DevhelmConflictError),
    (409, "confirmation_required", ConfirmationRequiredError, DevhelmConflictError),
    (404, "not_found", NotFoundError, DevhelmNotFoundError),
    (410, "gone", GoneError, DevhelmApiError),
    (500, "platform", PlatformError, DevhelmServerError),
]


@pytest.mark.parametrize("status,category,cls,legacy", CASES, ids=[c[1] for c in CASES])
def test_category_picks_class(
    status: int,
    category: str,
    cls: type[DevhelmApiError],
    legacy: type[DevhelmApiError],
) -> None:
    err = error_from_response(status, _envelope(status, category))
    assert type(err) is cls
    assert isinstance(err, legacy)
    assert isinstance(err, DevhelmApiError)
    assert isinstance(err, DevhelmError)
    assert err.category == category
    assert err.status == status
    assert err.code == "SOME_CODE"
    assert err.message == f"{category} refusal"


def test_category_wins_over_http_status() -> None:
    assert type(error_from_response(409, _envelope(409, "ownership"))) is OwnershipError
    assert type(error_from_response(400, _envelope(400, "quota"))) is QuotaError
    assert type(error_from_response(403, _envelope(403, "plan"))) is PlanLimitError
    assert type(error_from_response(503, _envelope(503, "conflict"))) is ConflictError


@pytest.mark.parametrize(
    "status,cls",
    [
        (400, ValidationError),
        (401, AuthError),
        (402, PlanLimitError),
        (403, PermissionError),
        (404, NotFoundError),
        (409, ConflictError),
        (410, GoneError),
        (429, RateLimitError),
        (500, PlatformError),
        (503, PlatformError),
        (422, DevhelmApiError),
    ],
)
def test_status_fallback_without_category(
    status: int, cls: type[DevhelmApiError]
) -> None:
    err = error_from_response(status, json.dumps({"message": "x"}))
    assert type(err) is cls


def test_unknown_category_falls_back_to_status() -> None:
    err = error_from_response(404, _envelope(404, "brand_new_category"))
    assert type(err) is NotFoundError
    # The server's category string is preserved even when unknown.
    assert err.category == "brand_new_category"


def test_non_json_body_falls_back_to_status() -> None:
    err = error_from_response(502, "<html>Bad Gateway</html>")
    assert type(err) is PlatformError
    assert err.envelope is None
    assert err.retryable is False
    assert err.timestamp is None
    assert err.errors == []


def test_every_envelope_field_is_an_attribute() -> None:
    body = {
        "status": 402,
        "code": "SYNTHETICS_USAGE_CAPPED",
        "category": "quota",
        "retryable": True,
        "message": "browser_runs: 1000/1000 used on FREE",
        "timestamp": 1737302400000,
        "requestId": "req_8f21c0",
        "errors": [{"code": "FIELD_REQUIRED", "field": "name", "message": "required"}],
        "retryAfterSeconds": 30,
        "resource": "browser_runs",
        "used": 1000,
        "limit": 1000,
        "resetsAt": "2026-11-01T00:00:00Z",
        "plan": "FREE",
        "upgradeUrl": "https://app.devhelm.io/settings/billing",
        "canRaise": "org admin",
        "owner": "TERRAFORM",
        "required": "monitors:deploy",
        "have": 10,
        "reason": "scope",
        "next": {
            "command": "devhelm account usage",
            "docs": "https://docs.devhelm.io/errors/SYNTHETICS_USAGE_CAPPED",
        },
        "details": {
            "owner": "CLI",
            "drafts": ["a", "b"],
            "count": 3,
            "nested": {"x": None},
        },
        "expiredAt": "2026-10-01T00:00:00Z",
        "policy": "P7D",
    }
    err = error_from_response(402, json.dumps(body))
    assert isinstance(err, QuotaError)
    assert err.status == 402
    assert err.code == "SYNTHETICS_USAGE_CAPPED"
    assert err.category == "quota"
    assert err.retryable is True
    assert err.message == "browser_runs: 1000/1000 used on FREE"
    assert err.timestamp == 1737302400000
    assert err.request_id == "req_8f21c0"
    assert len(err.errors) == 1
    assert isinstance(err.errors[0], ErrorEntry)
    assert err.errors[0].field == "name"
    assert err.retry_after_seconds == 30
    assert err.retry_after == 30
    assert err.resource == "browser_runs"
    assert err.used == 1000
    assert err.limit == 1000
    assert err.resets_at == "2026-11-01T00:00:00Z"
    assert err.plan == "FREE"
    assert err.upgrade_url == "https://app.devhelm.io/settings/billing"
    assert err.can_raise == "org admin"
    assert err.owner == "TERRAFORM"
    assert err.required == "monitors:deploy"
    assert err.have == 10
    assert err.reason == "scope"
    assert err.next is not None
    assert err.next.command == "devhelm account usage"
    assert err.next.docs == "https://docs.devhelm.io/errors/SYNTHETICS_USAGE_CAPPED"
    assert err.details == {
        "owner": "CLI",
        "drafts": ["a", "b"],
        "count": 3,
        "nested": {"x": None},
    }
    assert isinstance(err.expired_at, datetime)
    assert err.policy == "P7D"
    assert err.envelope is not None


def test_retry_after_header_wins_over_body() -> None:
    body = json.loads(_envelope(429, "rate_limit"))
    body["retryAfterSeconds"] = 5
    err = error_from_response(429, json.dumps(body), retry_after="12")
    assert err.retry_after == 12
    assert err.retry_after_seconds == 12


def test_header_request_id_wins_over_envelope() -> None:
    err = error_from_response(404, _envelope(404, "not_found"), request_id="hdr")
    assert err.request_id == "hdr"


def test_transport_error_is_the_transport_category() -> None:
    assert TransportError is DevhelmTransportError
    err = TransportError("refused", cause=OSError("boom"))
    assert err.category == "transport"
    assert err.code == "TRANSPORT"
    assert isinstance(err, DevhelmError)
    assert not isinstance(err, DevhelmApiError)
    assert isinstance(err.__cause__, OSError)


def test_wait_timeout_error_fields() -> None:
    err = WaitTimeoutError("run-1", "running", timeout_ms=5000)
    assert err.run_id == "run-1"
    assert err.phase == "running"
    assert err.timeout_ms == 5000
    assert err.aborted is False
    assert err.code == "WAIT_TIMEOUT"
    assert isinstance(err, DevhelmError)
    assert "5000 ms" in str(err)
    aborted = WaitTimeoutError("run-1", "queued", timeout_ms=1, aborted=True)
    assert aborted.aborted is True
    assert "stopped" in str(aborted)


def test_client_error_builds_status_zero_errors() -> None:
    err = client_error(
        "validation",
        "USE_PROBE",
        "use probe",
        field="code",
        next_command="monitors.probe(id)",
        details={"k": "v"},
    )
    assert type(err) is ValidationError
    assert err.status == 0
    assert err.code == "USE_PROBE"
    assert err.category == "validation"
    assert err.errors[0].field == "code"
    assert err.errors[0].code == "USE_PROBE"
    assert isinstance(err.next, ErrorNext)
    assert err.next.command == "monitors.probe(id)"
    assert err.details == {"k": "v"}
    assert err.envelope is None


def test_client_error_without_field_has_no_entries() -> None:
    err = client_error("quota", "X", "msg")
    assert type(err) is QuotaError
    assert err.errors == []
    assert err.next is None


def test_errors_module_re_exports() -> None:
    for name in errors.__all__:
        assert hasattr(errors, name)
    assert errors.PermissionError is PermissionError
    assert errors.ValidationError is ValidationError
    assert errors.WaitTimeoutError is WaitTimeoutError
    assert set(errors.CATEGORY_CLASSES) == {c[1] for c in CASES}
    # The package root re-exports the same classes.
    assert devhelm.PermissionError is PermissionError
    assert devhelm.TransportError is DevhelmTransportError
