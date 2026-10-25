"""Transport policy shared by the sync and async clients.

Pure functions only: no I/O. The sync (``devhelm._sync.transport``) and
async (``devhelm._async.transport``) transports both call into this module so
retries, idempotency keys and error decoding behave identically.

Retries (doc 42 §5.2, doc 32 D-7):

* 429 and 503, and 409 envelopes marked ``retryable: true`` (such as
  ``DEPLOY_LOCKED`` or ``IDEMPOTENCY_KEY_IN_PROGRESS``), plus connection
  failures that never reached the server.
* ``Retry-After`` (or the envelope's ``retryAfterSeconds``) is honoured;
  otherwise exponential backoff with full jitter.
* At most 5 attempts. A wait longer than ``max_retry_after_s`` is not slept
  through: the error is raised so the caller decides.
* A POST is retried only when it carries an ``Idempotency-Key``. The SDK
  generates one UUIDv4 per logical call and reuses it only for these
  transport retries, so a retried POST replays instead of running twice.
"""

from __future__ import annotations

import json
import random
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import quote
from uuid import UUID

import httpx
from pydantic import BaseModel

from devhelm._errors import DevhelmValidationError, error_from_response

IDEMPOTENCY_HEADER = "Idempotency-Key"
CLIENT_HEADER = "X-DevHelm-Client"

# Scalar query values plus repeated keys (``?outcome=failed&outcome=timed_out``).
QueryScalar = str | int | float | bool
QueryValue = QueryScalar | Sequence[QueryScalar] | None
QueryParams = Mapping[str, QueryValue]

JsonResponse = dict[str, object] | list[object] | None

# Resource ids: the generated DTOs carry ``UUID``; strings are accepted too.
ResourceId = str | UUID


@dataclass(frozen=True)
class RetryPolicy:
    """How a transport retries. ``max_attempts=1`` disables retries."""

    max_attempts: int = 5
    base_delay_s: float = 0.5
    max_backoff_s: float = 8.0
    max_retry_after_s: float = 60.0


NO_RETRY = RetryPolicy(max_attempts=1)


def path_param(value: str | int | UUID) -> str:
    """URL-encode a path parameter."""
    return quote(str(value), safe="")


def new_idempotency_key() -> str:
    return str(uuid.uuid4())


def request_headers(method: str, headers: Mapping[str, str] | None) -> dict[str, str]:
    """Copy caller headers and add a fresh ``Idempotency-Key`` to a POST."""
    out = dict(headers or {})
    if method.upper() == "POST" and not any(
        k.lower() == IDEMPOTENCY_HEADER.lower() for k in out
    ):
        out[IDEMPOTENCY_HEADER] = new_idempotency_key()
    return out


def can_retry(method: str, headers: Mapping[str, str]) -> bool:
    if method.upper() != "POST":
        return True
    return any(k.lower() == IDEMPOTENCY_HEADER.lower() for k in headers)


def backoff_delay(policy: RetryPolicy, attempt: int) -> float:
    """Full-jitter exponential backoff for ``attempt`` (1-based)."""
    ceiling = min(policy.max_backoff_s, policy.base_delay_s * (2 ** (attempt - 1)))
    return random.uniform(0, ceiling)  # noqa: S311 (jitter, not crypto)


def _retry_after_seconds(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    if raw is not None:
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
    body = _json_body(response)
    if isinstance(body, dict):
        seconds = body.get("retryAfterSeconds")
        if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
            return max(0.0, float(seconds))
    return None


def _json_body(response: httpx.Response) -> object:
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None


def _retryable_conflict(response: httpx.Response) -> bool:
    body = _json_body(response)
    return isinstance(body, dict) and body.get("retryable") is True


def retry_delay(
    policy: RetryPolicy, response: httpx.Response, attempt: int
) -> float | None:
    """Seconds to wait before retrying ``response``, or ``None`` to stop."""
    if attempt >= policy.max_attempts:
        return None
    status = response.status_code
    if status not in (429, 503) and not (
        status == 409 and _retryable_conflict(response)
    ):
        return None
    wait = _retry_after_seconds(response)
    if wait is None:
        return backoff_delay(policy, attempt)
    if wait > policy.max_retry_after_s:
        return None
    # A little jitter so parallel callers told the same Retry-After spread out.
    return wait + random.uniform(0, min(1.0, policy.base_delay_s))  # noqa: S311


def transport_retry_delay(policy: RetryPolicy, attempt: int) -> float | None:
    """Seconds to wait before retrying a request that never got a response."""
    if attempt >= policy.max_attempts:
        return None
    return backoff_delay(policy, attempt)


def serialize_body(body: BaseModel | Mapping[str, object] | None) -> object:
    """Convert a pydantic model to a JSON-serialisable dict.

    Raw dicts are refused so every request body passes through its generated
    model first.
    """
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(body, Mapping):
        raise DevhelmValidationError(
            "Raw dicts are not accepted as request bodies. "
            "Use the generated Pydantic model instead."
        )
    return body


def clean_params(params: QueryParams | None) -> dict[str, QueryValue] | None:
    """Drop ``None`` values so the API's defaults apply."""
    if not params:
        return None
    cleaned: dict[str, QueryValue] = {k: v for k, v in params.items() if v is not None}
    return cleaned or None


def decode_body(response: httpx.Response) -> JsonResponse:
    """Narrow ``httpx.Response.json()`` into the SDK's JSON shape.

    The API answers a JSON object, a JSON array or an empty body. A bare
    scalar is a server bug and raises.
    """
    if not response.content:
        return None
    body = response.json()
    if body is None or isinstance(body, (dict, list)):
        return body
    raise DevhelmValidationError(
        "Expected a JSON object, JSON array, or empty body from the server, "
        f"got {type(body).__name__}."
    )


def raise_for_error(response: httpx.Response) -> None:
    """Raise the typed error for a non-2xx response."""
    if response.is_success:
        return
    raise error_from_response(
        response.status_code,
        response.text,
        request_id=response.headers.get("x-request-id"),
        retry_after=response.headers.get("retry-after"),
    )


def checked_json(response: httpx.Response) -> JsonResponse:
    """Raise for a non-2xx response; otherwise decode the JSON body."""
    raise_for_error(response)
    if response.status_code == 204:
        return None
    return decode_body(response)


def query_from_model(model: BaseModel) -> dict[str, QueryValue]:
    """Flatten a generated ``*Params`` model into query parameters.

    The API reads list filters as flat query keys (``?outcome=failed&limit=25``);
    ``None`` fields are dropped so server defaults apply.
    """
    dumped = model.model_dump(mode="json", by_alias=True, exclude_none=True)
    out: dict[str, QueryValue] = {}
    for key, value in dumped.items():
        if isinstance(value, (str, int, float, bool)):
            out[key] = value
        elif isinstance(value, list) and all(
            isinstance(v, (str, int, float, bool)) for v in value
        ):
            out[key] = value
        else:
            raise DevhelmValidationError(
                f"Query parameter {key!r} must be a scalar or a list of scalars"
            )
    return out
