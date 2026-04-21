"""Tests for the typed error taxonomy."""

from __future__ import annotations

import json

from devhelm._errors import (
    DevhelmApiError,
    DevhelmAuthError,
    DevhelmConflictError,
    DevhelmError,
    DevhelmNotFoundError,
    DevhelmRateLimitError,
    DevhelmServerError,
    DevhelmValidationError,
    error_from_response,
)


class TestErrorFromResponse:
    def test_401_returns_auth_error(self) -> None:
        err = error_from_response(401, json.dumps({"message": "Unauthorized"}))
        assert isinstance(err, DevhelmAuthError)
        assert err.status == 401
        assert err.message == "Unauthorized"

    def test_403_returns_auth_error(self) -> None:
        err = error_from_response(403, json.dumps({"message": "Forbidden"}))
        assert isinstance(err, DevhelmAuthError)
        assert err.status == 403

    def test_404_returns_not_found(self) -> None:
        err = error_from_response(
            404, json.dumps({"message": "Not found", "detail": "Monitor 99"})
        )
        assert isinstance(err, DevhelmNotFoundError)
        assert not isinstance(err, DevhelmAuthError)
        assert err.detail == "Monitor 99"

    def test_409_returns_conflict(self) -> None:
        err = error_from_response(409, json.dumps({"message": "Already exists"}))
        assert isinstance(err, DevhelmConflictError)

    def test_400_returns_api_error_not_validation(self) -> None:
        # 4xx (other than 401/403/404/409/429) is plain DevhelmApiError; the
        # framework no longer conflates server-side "VALIDATION" with our
        # local DevhelmValidationError class (which is reserved for Pydantic
        # failures we raise without ever talking to the server).
        err = error_from_response(400, json.dumps({"message": "Bad request"}))
        assert isinstance(err, DevhelmApiError)
        assert not isinstance(err, DevhelmValidationError)
        assert err.status == 400

    def test_422_returns_api_error_not_validation(self) -> None:
        err = error_from_response(422, json.dumps({"message": "Unprocessable"}))
        assert isinstance(err, DevhelmApiError)
        assert not isinstance(err, DevhelmValidationError)
        assert err.status == 422

    def test_429_returns_rate_limit(self) -> None:
        err = error_from_response(429, json.dumps({"message": "Slow down"}))
        assert isinstance(err, DevhelmRateLimitError)
        assert err.status == 429

    def test_500_returns_server_error(self) -> None:
        err = error_from_response(500, json.dumps({"message": "Internal error"}))
        assert isinstance(err, DevhelmServerError)
        assert err.status == 500

    def test_503_returns_server_error(self) -> None:
        err = error_from_response(503, json.dumps({"message": "Unavailable"}))
        assert isinstance(err, DevhelmServerError)
        assert err.status == 503

    def test_non_json_body(self) -> None:
        err = error_from_response(502, "Bad Gateway")
        assert isinstance(err, DevhelmServerError)
        # Non-JSON bodies surface as DevhelmApiError with the raw text on
        # `body` and the default `HTTP {status}` message.
        assert err.message == "HTTP 502"
        assert err.body == "Bad Gateway"

    def test_empty_body(self) -> None:
        err = error_from_response(503, "")
        assert isinstance(err, DevhelmServerError)
        assert err.message == "HTTP 503"

    def test_json_with_error_field(self) -> None:
        err = error_from_response(400, json.dumps({"error": "validation failed"}))
        assert err.message == "validation failed"

    def test_json_with_detail(self) -> None:
        err = error_from_response(
            400, json.dumps({"message": "Bad request", "detail": "name is required"})
        )
        assert err.detail == "name is required"

    def test_json_without_detail(self) -> None:
        err = error_from_response(400, json.dumps({"message": "Bad request"}))
        assert err.detail is None


class TestDevhelmErrorInheritance:
    def test_api_error_is_devhelm_error(self) -> None:
        err = DevhelmApiError("test", status=500)
        assert isinstance(err, DevhelmError)
        assert isinstance(err, Exception)

    def test_auth_error_is_api_error(self) -> None:
        err = DevhelmAuthError("test", status=401)
        assert isinstance(err, DevhelmApiError)
        assert isinstance(err, DevhelmError)
        assert isinstance(err, Exception)

    def test_validation_error_is_devhelm_error_but_not_api_error(self) -> None:
        err = DevhelmValidationError("nope")
        assert isinstance(err, DevhelmError)
        assert not isinstance(err, DevhelmApiError)

    def test_str_shows_message(self) -> None:
        err = DevhelmNotFoundError("Monitor not found", status=404)
        assert str(err) == "Monitor not found"
