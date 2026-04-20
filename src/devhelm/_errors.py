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
    """


class DevhelmValidationError(DevhelmError):
    """Raised when local validation of a request or response fails.

    `errors` mirrors `pydantic.ValidationError.errors()` when the source is
    a Pydantic failure; otherwise it's a single-element list with `loc`,
    `msg`, and `type`.
    """

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
    """

    status: int
    message: str
    detail: str | None
    body: dict[str, Any] | str | None

    def __init__(
        self,
        message: str,
        *,
        status: int,
        detail: str | None = None,
        body: dict[str, Any] | str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.detail = detail
        self.body = body


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

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        if cause is not None:
            self.__cause__ = cause


def error_from_response(status: int, body: str) -> DevhelmApiError:
    """Map an HTTP error response to a typed DevhelmApiError subclass."""
    message = f"HTTP {status}"
    detail: str | None = None
    parsed_body: dict[str, Any] | str | None = body or None

    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            parsed_body = parsed
            message = str(parsed.get("message") or parsed.get("error") or message)
            raw_detail = parsed.get("detail")
            if raw_detail is not None:
                detail = str(raw_detail)
    except (json.JSONDecodeError, ValueError):
        pass

    if status in (401, 403):
        return DevhelmAuthError(
            message, status=status, detail=detail, body=parsed_body
        )
    if status == 404:
        return DevhelmNotFoundError(
            message, status=status, detail=detail, body=parsed_body
        )
    if status == 409:
        return DevhelmConflictError(
            message, status=status, detail=detail, body=parsed_body
        )
    if status == 429:
        return DevhelmRateLimitError(
            message, status=status, detail=detail, body=parsed_body
        )
    if status >= 500:
        return DevhelmServerError(
            message, status=status, detail=detail, body=parsed_body
        )
    return DevhelmApiError(message, status=status, detail=detail, body=parsed_body)


# ---------------------------------------------------------------------------
# Backwards-compatible aliases (no customers yet, but our own tests + scripts
# still import the legacy names; flip these to deprecation warnings once the
# rest of the codebase is migrated).
# ---------------------------------------------------------------------------

AuthError = DevhelmAuthError
