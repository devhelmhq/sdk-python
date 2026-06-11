from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from devhelm._errors import (
    DevhelmTransportError,
    DevhelmValidationError,
    error_from_response,
)

DEFAULT_BASE_URL = "https://api.devhelm.io"
DEFAULT_PAGE_SIZE = 200

# Default surface identifier sent on every authenticated request. Wrappers
# (e.g. the MCP server) override this at construction time so the API can
# attribute usage to the right devtool. See ``DevhelmConfig.surface``.
DEFAULT_SURFACE = "sdk-py"


def _sdk_version() -> str:
    """Resolve the installed package version once at import time.

    Uses ``importlib.metadata`` instead of hardcoding so a single source of
    truth (``pyproject.toml``) flows through to the wire telemetry header.
    Falls back to ``"unknown"`` for editable / source-tree installs that
    don't yet have a dist-info directory; the API treats that as "no version
    reported" rather than rejecting the request.
    """
    try:
        return _pkg_version("devhelm")
    except PackageNotFoundError:
        return "unknown"


@dataclass(frozen=True)
class DevhelmConfig:
    """Configuration for the DevHelm API client."""

    token: str
    base_url: str = DEFAULT_BASE_URL
    org_id: str | None = None
    workspace_id: str | None = None
    timeout: float = 30.0
    # Devtool surface identifier reported to the API for adoption and
    # version-distribution telemetry. Defaults to ``"sdk-py"``; wrappers
    # such as the MCP server pass ``"mcp"`` instead so their traffic is
    # attributed correctly. See https://devhelm.io/telemetry for the full
    # contract and opt-out semantics.
    surface: str = DEFAULT_SURFACE
    # Surface version. Defaults to the installed ``devhelm`` package
    # version; wrappers should pass their own package version.
    surface_version: str | None = None
    # Surface-specific metadata forwarded as ``X-DevHelm-*`` headers (e.g.
    # the MCP server attaches ``mcp_client``). Keys are normalised to
    # lower-kebab-case and mapped onto ``X-DevHelm-<key>`` on the wire.
    surface_metadata: dict[str, str] = field(default_factory=dict)


def _resolve(value: str | None, env_key: str, label: str) -> str:
    result = value or os.environ.get(env_key)
    if not result:
        raise DevhelmValidationError(
            f"{label} is required. Pass it to Devhelm() or set {env_key}."
        )
    return result


def _resolve_optional(value: str | None, env_key: str, default: str) -> str:
    return value or os.environ.get(env_key) or default


def _telemetry_headers(config: DevhelmConfig) -> dict[str, str]:
    """Build the ``X-DevHelm-Surface*`` headers for one client instance.

    Returns an empty dict when ``DEVHELM_TELEMETRY=0`` so the API receives
    no surface signal at all. The opt-out is intentionally a single env var
    rather than a constructor flag — users opt out once for the whole
    process, not per call site. See https://devhelm.io/telemetry.
    """
    if os.environ.get("DEVHELM_TELEMETRY", "").strip() == "0":
        return {}
    headers: dict[str, str] = {
        "X-DevHelm-Surface": config.surface,
        "X-DevHelm-Surface-Version": config.surface_version or _sdk_version(),
        # Always identify the underlying SDK so the API can distinguish
        # "raw SDK call" from "wrapper-on-top-of-SDK call" (the latter
        # overrides ``Surface`` to e.g. ``mcp`` but the SDK fingerprint
        # stays available for debugging client-version skew).
        "X-DevHelm-Sdk-Name": "sdk-py",
    }
    for key, value in config.surface_metadata.items():
        headers[f"X-DevHelm-{key}"] = value
    return headers


def build_client(config: DevhelmConfig) -> httpx.Client:
    """Create a configured httpx.Client with auth and tenant headers."""
    base_url = config.base_url.rstrip("/")
    token = _resolve(config.token, "DEVHELM_API_TOKEN", "token")
    org_id = _resolve_optional(config.org_id, "DEVHELM_ORG_ID", "1")
    workspace_id = _resolve_optional(config.workspace_id, "DEVHELM_WORKSPACE_ID", "1")

    return httpx.Client(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-phelm-org-id": org_id,
            "x-phelm-workspace-id": workspace_id,
            **_telemetry_headers(config),
        },
        timeout=config.timeout,
    )


def path_param(value: str | int) -> str:
    """URL-encode a path parameter."""
    return quote(str(value), safe="")


_JsonResponse = dict[str, object] | list[object] | None


def _serialize_body(
    body: BaseModel | dict[str, object] | None,
) -> dict[str, object] | None:
    """Convert a Pydantic model to a JSON-serializable dict.

    Rejects raw dicts to prevent callers from bypassing Pydantic
    validation. All request bodies must be validated model instances.
    """
    if isinstance(body, BaseModel):
        return body.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(body, dict):
        raise DevhelmValidationError(
            "Raw dicts are not accepted as request bodies. "
            "Use the generated Pydantic model instead."
        )
    return body


def _decode_body(response: httpx.Response) -> _JsonResponse:
    """Narrow ``httpx.Response.json()`` (typed `Any`) into the SDK's
    declared `_JsonResponse` shape at a single boundary.

    httpx never types its decoded body, so without this funnel every caller
    site would have to suppress mypy's no-any-return diagnostic. Centralising
    the narrowing lets the rest of the SDK keep mypy clean (P5: zero casts
    outside generated files) while preserving honest semantics — a non-JSON
    body still raises through `httpx`/`json` rather than being silently
    re-typed.
    """
    body = response.json()
    if body is None or isinstance(body, (dict, list)):
        return body
    # The API contract is "JSON object, JSON array, or empty body". Anything
    # else (a bare scalar) is a server-side bug we want to surface loudly,
    # not silently reshape into an unknown.
    raise DevhelmValidationError(
        "Expected a JSON object, JSON array, or empty body from the server, "
        f"got {type(body).__name__}."
    )


def checked_fetch(response: httpx.Response) -> _JsonResponse:
    """Check an httpx response and raise a typed DevhelmApiError on failure."""
    if response.is_success:
        if response.status_code == 204:
            return None
        return _decode_body(response)
    raise error_from_response(
        response.status_code,
        response.text,
        request_id=response.headers.get("x-request-id"),
        retry_after=response.headers.get("retry-after"),
    )


# ---------------------------------------------------------------------------
# Transport-error wrapping
# ---------------------------------------------------------------------------


def _wrap_transport_errors(send: Any) -> httpx.Response:
    """Run ``send()`` and translate httpx transport failures into
    `DevhelmTransportError`, preserving ``__cause__``.

    httpx-level exceptions that indicate the request never reached the server
    (or the server's response never reached us) are wrapped here. We let
    `httpx.HTTPStatusError`-style failures fall through unchanged because
    those should not occur — `checked_fetch` reads `response.is_success`
    explicitly rather than calling `.raise_for_status()`.
    """
    try:
        result = send()
    except httpx.HTTPError as exc:
        raise DevhelmTransportError(f"{type(exc).__name__}: {exc}", cause=exc) from exc
    if not isinstance(result, httpx.Response):
        # Defensive: every httpx.Client.{get,post,...} returns httpx.Response.
        # Anyone who feeds `_wrap_transport_errors` a callable that returns
        # something else has a bug we want to surface immediately, not bury.
        raise TypeError(
            f"Expected httpx.Response from transport call, got {type(result).__name__}"
        )
    return result


def api_get(
    client: httpx.Client, path: str, params: dict[str, Any] | None = None
) -> _JsonResponse:
    return checked_fetch(
        _wrap_transport_errors(lambda: client.get(path, params=params))
    )


def api_post(
    client: httpx.Client, path: str, body: BaseModel | dict[str, object] | None = None
) -> _JsonResponse:
    if body is None:
        return checked_fetch(_wrap_transport_errors(lambda: client.post(path)))
    payload = _serialize_body(body)
    return checked_fetch(
        _wrap_transport_errors(lambda: client.post(path, json=payload))
    )


def api_put(
    client: httpx.Client, path: str, body: BaseModel | dict[str, object] | None
) -> _JsonResponse:
    payload = _serialize_body(body)
    return checked_fetch(_wrap_transport_errors(lambda: client.put(path, json=payload)))


def api_patch(
    client: httpx.Client, path: str, body: BaseModel | dict[str, object] | None
) -> _JsonResponse:
    payload = _serialize_body(body)
    return checked_fetch(
        _wrap_transport_errors(lambda: client.patch(path, json=payload))
    )


def api_delete(client: httpx.Client, path: str) -> None:
    checked_fetch(_wrap_transport_errors(lambda: client.delete(path)))
