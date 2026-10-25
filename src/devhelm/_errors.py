"""Error taxonomy for the DevHelm SDK.

Every API refusal carries an ``ErrorResponse`` envelope whose ``category`` is
the machine contract (doc 32 D-1). The SDK raises exactly one class per
category, chosen from ``category`` and never from the HTTP status:

  ========================  ==========================  =====================
  category                  class                       also an instance of
  ========================  ==========================  =====================
  ``validation``            ValidationError             DevhelmApiError
  ``blocked``               BlockedError                DevhelmConflictError
  ``auth``                  AuthError                   DevhelmAuthError
  ``permission``            PermissionError             DevhelmAuthError
  ``ownership``             OwnershipError              DevhelmConflictError
  ``plan``                  PlanLimitError              DevhelmApiError
  ``quota``                 QuotaError                  DevhelmApiError
  ``rate_limit``            RateLimitError              DevhelmRateLimitError
  ``conflict``              ConflictError               DevhelmConflictError
  ``confirmation_required`` ConfirmationRequiredError   DevhelmConflictError
  ``not_found``             NotFoundError               DevhelmNotFoundError
  ``gone``                  GoneError                   DevhelmApiError
  ``platform``              PlatformError               DevhelmServerError
  ``transport``             TransportError              DevhelmError
  ========================  ==========================  =====================

The right-hand column keeps ``except DevhelmAuthError:`` (and the other
HTTP-class names that shipped before categories existed) working. A body
with no known category falls back to the class its HTTP status implies.

Three other classes sit beside the category classes:

  DevhelmValidationError
      A request or response failed local shape validation (pydantic). Raised
      before any HTTP I/O for requests. Carries pydantic's ``errors``.

  WaitTimeoutError
      ``wait`` ran out of time before the run finished. Carries ``run_id``
      and the last ``phase`` seen. The run keeps going.

  DevhelmError
      The umbrella class every SDK error inherits from.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import JsonValue
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from devhelm._generated import ErrorEntry, ErrorNext, ErrorResponse

if TYPE_CHECKING:
    from devhelm._generated import RunDto


class DevhelmError(Exception):
    """Umbrella class: every typed SDK error inherits from this.

    ``code`` is the stable machine code (``NOT_FOUND``,
    ``SYNTHETICS_USAGE_CAPPED``, ``USE_PROBE``, …) and ``category`` the
    error class (``validation``, ``quota``, ``transport``, …). Switch on
    those, never on ``message``.
    """

    code: str = "ERROR"
    category: str = "platform"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DevhelmValidationError(DevhelmError):
    """A request or response failed local shape validation.

    ``errors`` mirrors ``pydantic.ValidationError.errors()`` when the source
    is a pydantic failure; otherwise it holds one entry per problem with
    ``type``, ``loc``, ``msg`` and ``input``.
    """

    code = "VALIDATION"
    category = "validation"

    def __init__(
        self,
        message: str,
        *,
        errors: Sequence[ErrorDetails] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.errors: list[ErrorDetails] = list(errors) if errors else []
        self.__cause__ = cause


class DevhelmApiError(DevhelmError):
    """Raised for every refusal the API answered with an ``ErrorResponse``.

    Every envelope field is an attribute (snake_case). ``envelope`` is the
    parsed generated ``ErrorResponse`` (``None`` when the body was not an
    envelope, such as an HTML page from a proxy). ``body`` is the raw body.

    Client-side refusals in the same categories (``NO_TOKEN``, ``USE_PROBE``,
    ``BUNDLE_DIGEST_MISMATCH``, …) use the same classes with ``status = 0``.
    """

    status: int
    detail: str | None
    body: dict[str, JsonValue] | str | None
    code: str
    category: str
    request_id: str | None
    retry_after: int | None
    envelope: ErrorResponse | None
    errors: list[ErrorEntry]

    def __init__(
        self,
        message: str,
        *,
        status: int,
        detail: str | None = None,
        body: dict[str, JsonValue] | str | None = None,
        code: str | None = None,
        category: str | None = None,
        request_id: str | None = None,
        retry_after: int | None = None,
        envelope: ErrorResponse | None = None,
        errors: Sequence[ErrorEntry] | None = None,
        next: ErrorNext | None = None,
        details: dict[str, JsonValue] | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail
        self.body = body
        # Server-supplied code wins; fall back to a generic label so
        # ``err.code`` is never empty for callers switching on it.
        self.code = code or (envelope.code if envelope else None) or "API_ERROR"
        self.category = (
            category
            or (envelope.category.root if envelope else None)
            or type(self).category
        )
        self.request_id = request_id or (envelope.request_id if envelope else None)
        self.envelope = envelope
        # ``Retry-After`` header (seconds) wins over ``retryAfterSeconds``.
        self.retry_after = (
            retry_after
            if retry_after is not None
            else (envelope.retry_after_seconds if envelope else None)
        )
        if errors is not None:
            self.errors = list(errors)
        else:
            self.errors = list(envelope.errors or []) if envelope else []
        if not self.errors and field is not None:
            self.errors = [ErrorEntry(code=self.code, field=field, message=message)]
        self._next = next
        self._details = details

    # -- the remaining ErrorResponse fields -----------------------------------

    @property
    def retryable(self) -> bool:
        return self.envelope.retryable if self.envelope else False

    @property
    def timestamp(self) -> int | None:
        return self.envelope.timestamp if self.envelope else None

    @property
    def retry_after_seconds(self) -> int | None:
        return self.retry_after

    @property
    def resource(self) -> str | None:
        return self.envelope.resource if self.envelope else None

    @property
    def used(self) -> int | None:
        return self.envelope.used if self.envelope else None

    @property
    def limit(self) -> int | None:
        return self.envelope.limit if self.envelope else None

    @property
    def resets_at(self) -> str | None:
        return self.envelope.resets_at if self.envelope else None

    @property
    def plan(self) -> str | None:
        return self.envelope.plan if self.envelope else None

    @property
    def upgrade_url(self) -> str | None:
        return self.envelope.upgrade_url if self.envelope else None

    @property
    def can_raise(self) -> str | None:
        return self.envelope.can_raise if self.envelope else None

    @property
    def owner(self) -> str | None:
        return self.envelope.owner if self.envelope else None

    @property
    def required(self) -> str | None:
        return self.envelope.required if self.envelope else None

    @property
    def have(self) -> int | None:
        return self.envelope.have if self.envelope else None

    @property
    def reason(self) -> str | None:
        return self.envelope.reason if self.envelope else None

    @property
    def next(self) -> ErrorNext | None:
        if self._next is not None:
            return self._next
        return self.envelope.next if self.envelope else None

    @property
    def details(self) -> dict[str, JsonValue] | None:
        if self._details is not None:
            return self._details
        return self.envelope.details if self.envelope else None

    @property
    def expired_at(self) -> datetime | None:
        return self.envelope.expired_at if self.envelope else None

    @property
    def policy(self) -> str | None:
        return self.envelope.policy if self.envelope else None


# -- HTTP-class names that shipped before categories (kept as bases) ---------


class DevhelmAuthError(DevhelmApiError):
    """401 or 403 from the API. Prefer :class:`AuthError` / :class:`PermissionError`."""

    category = "auth"


class DevhelmNotFoundError(DevhelmApiError):
    """404 from the API. Prefer :class:`NotFoundError`."""

    category = "not_found"


class DevhelmConflictError(DevhelmApiError):
    """409 from the API. Prefer the category classes."""

    category = "conflict"


class DevhelmRateLimitError(DevhelmApiError):
    """429 from the API. Prefer :class:`RateLimitError`."""

    category = "rate_limit"


class DevhelmServerError(DevhelmApiError):
    """5xx from the API. Prefer :class:`PlatformError`."""

    category = "platform"


# -- one class per category ---------------------------------------------------


class ValidationError(DevhelmApiError):
    """The request was refused as invalid (category ``validation``)."""

    category = "validation"


class BlockedError(DevhelmConflictError):
    """A precondition such as a missing secret value blocks the call."""

    category = "blocked"


class AuthError(DevhelmAuthError):
    """The credential is missing, invalid, expired or revoked."""

    category = "auth"


class PermissionError(DevhelmAuthError):  # noqa: A001 (the D-1 class name)
    """The credential lacks a scope or role. ``reason`` is ``scope`` or ``role``."""

    category = "permission"


class OwnershipError(DevhelmConflictError):
    """Another tool owns this monitor. ``owner`` names it."""

    category = "ownership"


class PlanLimitError(DevhelmApiError):
    """The plan does not include this, or a plan limit is reached."""

    category = "plan"


class QuotaError(DevhelmApiError):
    """A usage quota for the period is used up. ``resets_at`` says when it resumes."""

    category = "quota"


class RateLimitError(DevhelmRateLimitError):
    """Too many requests. Retried automatically; raised once retries run out."""

    category = "rate_limit"


class ConflictError(DevhelmConflictError):
    """The call collides with current state (stale revision, lock, draft cap, …)."""

    category = "conflict"


class ConfirmationRequiredError(DevhelmConflictError):
    """The write needs an explicit confirmation before it runs."""

    category = "confirmation_required"


class NotFoundError(DevhelmNotFoundError):
    """The monitor, run, revision or environment does not exist."""

    category = "not_found"


class GoneError(DevhelmApiError):
    """The run or its evidence expired past retention."""

    category = "gone"


class PlatformError(DevhelmServerError):
    """DevHelm failed; retrying later can succeed."""

    category = "platform"


class DevhelmTransportError(DevhelmError):
    """The request never produced a server response.

    Connection refused, DNS failure, TLS failure, timeouts. The httpx
    exception is on ``__cause__``.
    """

    code = "TRANSPORT"
    category = "transport"

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause


TransportError = DevhelmTransportError


class WaitTimeoutError(DevhelmError):
    """``wait`` gave up before the run finished. The run keeps going.

    ``phase`` is the last phase observed. ``aborted`` is true when the
    caller's ``signal`` stopped the wait rather than the clock.
    """

    code = "WAIT_TIMEOUT"
    category = "timeout"

    def __init__(
        self, run_id: str, phase: str, *, timeout_ms: int, aborted: bool = False
    ) -> None:
        verb = "was stopped" if aborted else f"timed out after {timeout_ms} ms"
        super().__init__(
            f"Waiting for run {run_id} {verb} (phase: {phase}). The run continues."
        )
        self.run_id = run_id
        self.phase = phase
        self.timeout_ms = timeout_ms
        self.aborted = aborted


class DevhelmMonitorTestQueuedError(DevhelmValidationError):
    """Raised by ``monitors.probe()`` when the API queued a run instead.

    The monitor is a browser or multi-step API monitor, so the API answered
    202 with a validation run rather than a probe result. That run is on
    ``run``. Use ``monitors.test()`` for these monitors.
    """

    code = "USE_TEST"

    def __init__(self, run: RunDto) -> None:
        super().__init__(
            f"The API queued a validation run ({run.id}) instead of returning a "
            "probe result: this is a browser or multi-step API monitor. Use "
            "monitors.test() for it."
        )
        self.run = run


CATEGORY_CLASSES: dict[str, type[DevhelmApiError]] = {
    "validation": ValidationError,
    "blocked": BlockedError,
    "auth": AuthError,
    "permission": PermissionError,
    "ownership": OwnershipError,
    "plan": PlanLimitError,
    "quota": QuotaError,
    "rate_limit": RateLimitError,
    "conflict": ConflictError,
    "confirmation_required": ConfirmationRequiredError,
    "not_found": NotFoundError,
    "gone": GoneError,
    "platform": PlatformError,
}


def _class_for_status(status: int) -> type[DevhelmApiError]:
    by_status: dict[int, type[DevhelmApiError]] = {
        400: ValidationError,
        401: AuthError,
        402: PlanLimitError,
        403: PermissionError,
        404: NotFoundError,
        409: ConflictError,
        410: GoneError,
        429: RateLimitError,
    }
    if status in by_status:
        return by_status[status]
    return PlatformError if status >= 500 else DevhelmApiError


def client_error(
    category: str,
    code: str,
    message: str,
    *,
    field: str | None = None,
    next_command: str | None = None,
    details: dict[str, JsonValue] | None = None,
) -> DevhelmApiError:
    """Build a category error raised by the SDK itself (``status = 0``)."""
    cls = CATEGORY_CLASSES.get(category, DevhelmApiError)
    return cls(
        message,
        status=0,
        code=code,
        category=category,
        field=field,
        next=ErrorNext(command=next_command) if next_command else None,
        details=details,
    )


def _parse_retry_after(value: str | None) -> int | None:
    """Parse a ``Retry-After`` header value into whole seconds.

    Any non-integer value (an HTTP-date, or garbage from a proxy) yields
    ``None`` rather than raising, so a malformed header never breaks error
    construction.
    """
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_envelope(parsed: dict[str, JsonValue]) -> ErrorResponse | None:
    try:
        return ErrorResponse.model_validate(parsed)
    except PydanticValidationError:
        return None


def error_from_response(
    status: int,
    body: str,
    *,
    request_id: str | None = None,
    retry_after: str | None = None,
) -> DevhelmApiError:
    """Map an HTTP error response to the typed error for its category.

    ``request_id`` is the ``X-Request-Id`` header and ``retry_after`` the raw
    ``Retry-After`` header, read at the call site so they survive a non-JSON
    body. The header request id wins over the body's.
    """
    message = f"HTTP {status}"
    detail: str | None = None
    code: str | None = None
    category: str | None = None
    envelope: ErrorResponse | None = None
    parsed_body: dict[str, JsonValue] | str | None = body or None

    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        parsed_body = parsed
        envelope = _parse_envelope(parsed)
        message = str(parsed.get("message") or parsed.get("error") or message)
        raw_detail = parsed.get("detail")
        if raw_detail is not None:
            detail = str(raw_detail)
        raw_code = parsed.get("code")
        if isinstance(raw_code, str):
            code = raw_code
        raw_category = parsed.get("category")
        if isinstance(raw_category, str):
            category = raw_category
        if request_id is None:
            raw_request_id = parsed.get("requestId") or parsed.get("request_id")
            if isinstance(raw_request_id, str):
                request_id = raw_request_id

    cls = CATEGORY_CLASSES.get(category or "") or _class_for_status(status)
    return cls(
        message,
        status=status,
        detail=detail,
        body=parsed_body,
        code=code,
        category=category,
        request_id=request_id,
        retry_after=_parse_retry_after(retry_after),
        envelope=envelope,
    )
