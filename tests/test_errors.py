"""Tests for error_from_response and error hierarchy."""

from __future__ import annotations

import json

from devhelm._errors import AuthError, DevhelmError, error_from_response


class TestErrorFromResponse:
    def test_401_returns_auth_error(self) -> None:
        err = error_from_response(401, json.dumps({"message": "Unauthorized"}))
        assert isinstance(err, AuthError)
        assert err.code == "AUTH"
        assert err.status == 401
        assert err.message == "Unauthorized"

    def test_403_returns_auth_error(self) -> None:
        err = error_from_response(403, json.dumps({"message": "Forbidden"}))
        assert isinstance(err, AuthError)
        assert err.code == "AUTH"
        assert err.status == 403

    def test_404_returns_not_found(self) -> None:
        err = error_from_response(
            404, json.dumps({"message": "Not found", "detail": "Monitor 99"})
        )
        assert isinstance(err, DevhelmError)
        assert not isinstance(err, AuthError)
        assert err.code == "NOT_FOUND"
        assert err.detail == "Monitor 99"

    def test_409_returns_conflict(self) -> None:
        err = error_from_response(409, json.dumps({"message": "Already exists"}))
        assert err.code == "CONFLICT"

    def test_400_returns_validation(self) -> None:
        err = error_from_response(400, json.dumps({"message": "Bad request"}))
        assert err.code == "VALIDATION"

    def test_422_returns_validation(self) -> None:
        err = error_from_response(422, json.dumps({"message": "Unprocessable"}))
        assert err.code == "VALIDATION"

    def test_500_returns_api(self) -> None:
        err = error_from_response(500, json.dumps({"message": "Internal error"}))
        assert err.code == "API"
        assert err.status == 500

    def test_non_json_body(self) -> None:
        err = error_from_response(502, "Bad Gateway")
        assert err.code == "API"
        assert err.message == "Bad Gateway"

    def test_empty_body(self) -> None:
        err = error_from_response(503, "")
        assert err.code == "API"
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
    def test_is_exception(self) -> None:
        err = DevhelmError("API", "test", 500)
        assert isinstance(err, Exception)

    def test_auth_error_is_devhelm_error(self) -> None:
        err = AuthError("test", 401)
        assert isinstance(err, DevhelmError)
        assert isinstance(err, Exception)

    def test_str_shows_message(self) -> None:
        err = DevhelmError("NOT_FOUND", "Monitor not found", 404)
        assert str(err) == "Monitor not found"
