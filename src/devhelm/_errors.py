"""Error taxonomy for the DevHelm SDK.

Three top-level classes (P4 — see `mono/cowork/design/040-codegen-policies.md`):

  DevhelmValidationError
      Local request/response shape validation failed. Raised before any HTTP
      I/O for request validation, and after a response is received but before
      it's returned to the caller for response validation.

  DevhelmApiError
      The API returned a non-2xx status. Always carries an HTTP status code
      and the parsed error body. Subclassed by HTTP class for ergonomics.

  DevhelmTransportError
      The HTTP request never made it to a server response — connection
      refused, DNS failure, timeout, TLS error, etc. Wraps the underlying
      httpx exception.

All three inherit from `DevhelmError`, the legacy umbrella class kept around
for `except DevhelmError:` catch-all sites. Callers should prefer catching
the specific subclass.
"""

from __future__ import annotations

import json
from typing import Any, Sequence


class DevhelmError(Exception):
    """Umbrella class — every typed SDK error inherits from this.

    Use this in catch-all sites; otherwise prefer the specific subclass.

    Every subclass populates ``code`` so callers can switch on the error
    category without ``isinstance`` chains:

    - :class:`DevhelmValidationError` → ``"VALIDATION"``
    - :class:`DevhelmTransportError` → ``"TRANSPORT"``
    - :class:`DevhelmApiError` → server-supplied (e.g. ``"NOT_FOUND"``)
    """

    code: str = "ERROR"


class DevhelmValidationError(DevhelmError):
    """Raised when local validation of a request or response fails.

    `errors` mirrors `pydantic.ValidationError.errors()` when the source is
    a Pydantic failure; otherwise it's a single-element list with `loc`,
    `msg`, and `type`.
    """

    code = "VALIDATION"

    def __init__(
        self,
        message: str,
        *,
        errors: Sequence[Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        # `Sequence[Any]` so we accept both the structured Pydantic
        # `ErrorDetails` records and plain dicts callers may build by hand.
        self.errors: list[Any] = list(errors) if errors else []
        self.__cause__ = cause


class DevhelmApiError(DevhelmError):
    """Raised when the API returns a non-2xx response.

    Always carries the HTTP status code and the (best-effort parsed) error
    body. Use the subclasses below for HTTP-class-specific handling.

    The optional `code` field is the API's coarse machine-readable error
    category (e.g. `NOT_FOUND`, `RATE_LIMITED`); see the `ErrorResponse`
    schema in the OpenAPI spec. Surface clients should switch on `code`,
    not the human-readable `message`.

    The optional `request_id` field is the per-request id emitted by the
    API as the `X-Request-Id` response header and embedded in the JSON
    error body. Always include it in support tickets.
    """

    status: int
    message: str
    detail: str | None
    body: dict[str, Any] | str | None
    # mypy infers `code: str` from the parent default, but we always populate
    # it in __init__ — declaring it again here is documentation, not a
    # narrowing. (Subclasses still inherit the same `str` type.)
    code: str
    request_id: str | None

    def __init__(
        self,
        message: str,
        *,
        status: int,
        detail: str | None = None,
        body: dict[str, Any] | str | None = None,
        code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.detail = detail
        self.body = body
        # Server-supplied code wins; fall back to a generic API-error label so
        # `err.code` is never ``None`` for callers switching on category.
        self.code = code or "API_ERROR"
        self.request_id = request_id


class DevhelmAuthError(DevhelmApiError):
    """401 or 403 from the API."""


class DevhelmNotFoundError(DevhelmApiError):
    """404 from the API."""


class DevhelmConflictError(DevhelmApiError):
    """409 from the API — typically idempotency or unique-constraint conflicts."""


class DevhelmRateLimitError(DevhelmApiError):
    """429 from the API. Caller should back off."""


class DevhelmServerError(DevhelmApiError):
    """5xx from the API — transient or upstream failures."""


class DevhelmTransportError(DevhelmError):
    """The HTTP request did not produce a server response.

    Connection refused, DNS resolution failure, TLS handshake failure,
    request/read/write timeout, etc. Wraps the underlying httpx exception
    on `__cause__` for full traceback.
    """

    code = "TRANSPORT"

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        if cause is not None:
            self.__cause__ = cause


def error_from_response(
    status: int, body: str, *, request_id: str | None = None
) -> DevhelmApiError:
    """Map an HTTP error response to a typed DevhelmApiError subclass.

    `request_id` is the value of the `X-Request-Id` response header. It is
    pulled out at the call site (rather than re-parsed from the body) so the
    SDK still surfaces the id even when the server returns a non-JSON body
    (e.g. an HTML error page from a misconfigured proxy).
    """
    message = f"HTTP {status}"
    detail: str | None = None
    code: str | None = None
    body_request_id: str | None = None
    parsed_body: dict[str, Any] | str | None = body or None

    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            parsed_body = parsed
            message = str(parsed.get("message") or parsed.get("error") or message)
            raw_detail = parsed.get("detail")
            if raw_detail is not None:
                detail = str(raw_detail)
            raw_code = parsed.get("code")
            if isinstance(raw_code, str):
                code = raw_code
            raw_request_id = parsed.get("requestId") or parsed.get("request_id")
            if isinstance(raw_request_id, str):
                body_request_id = raw_request_id
    except (json.JSONDecodeError, ValueError):
        pass

    # Header value wins: the body may be missing/non-JSON, but the header is
    # always present (set by RequestCorrelationFilter on the API side).
    resolved_request_id = request_id or body_request_id

    kwargs: dict[str, Any] = {
        "status": status,
        "detail": detail,
        "body": parsed_body,
        "code": code,
        "request_id": resolved_request_id,
    }

    if status in (401, 403):
        return DevhelmAuthError(message, **kwargs)
    if status == 404:
        return DevhelmNotFoundError(message, **kwargs)
    if status == 409:
        return DevhelmConflictError(message, **kwargs)
    if status == 429:
        return DevhelmRateLimitError(message, **kwargs)
    if status >= 500:
        return DevhelmServerError(message, **kwargs)
    return DevhelmApiError(message, **kwargs)
