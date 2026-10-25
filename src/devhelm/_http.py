"""Client configuration: credentials, base URL, tenant and surface headers.

Resolution order (doc 42 §5.2):

* token: explicit option → ``DEVHELM_API_TOKEN`` → the CLI's current context
  in ``~/.devhelm/contexts.json``. No token is a client-side
  ``ValidationError`` with code ``NO_TOKEN``.
* base URL: explicit option → ``DEVHELM_API_URL`` → the CLI context's URL
  (when the token came from it) → ``https://api.devhelm.io``.
* ``x-phelm-org-id`` / ``x-phelm-workspace-id``: explicit options →
  ``DEVHELM_ORG_ID`` / ``DEVHELM_WORKSPACE_ID``.

Every request also carries ``X-DevHelm-Client: <surface>/<version>``
(``sdk-python/1.13.0``; wrappers such as the MCP server pass their own
surface), which the API records as the revision's ``createdByKind``.

The ``api_*`` helpers here are the blocking request functions from
``devhelm._sync.transport``, kept importable from this module.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

import httpx

from devhelm._errors import client_error
from devhelm._sync.transport import (
    Transport,
    api_delete,
    api_get,
    api_post,
    api_post_with_status,
    api_put,
)
from devhelm._sync.transport import api_patch as api_patch
from devhelm._transport import (
    CLIENT_HEADER,
    JsonResponse,
    checked_json,
    decode_body,
    path_param,
    serialize_body,
)

DEFAULT_BASE_URL = "https://api.devhelm.io"
DEFAULT_PAGE_SIZE = 200

# Default surface identifier for the telemetry headers. Wrappers (the MCP
# server) override it at construction time.
DEFAULT_SURFACE = "sdk-py"
# ``X-DevHelm-Client`` names surfaces as doc 42 §5.2 lists them.
CLIENT_NAMES = {"sdk-py": "sdk-python"}

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_SURFACE",
    "DevhelmConfig",
    "Transport",
    "api_delete",
    "api_get",
    "api_patch",
    "api_post",
    "api_post_with_status",
    "api_put",
    "build_async_client",
    "build_client",
    "checked_fetch",
    "path_param",
]


def _sdk_version() -> str:
    """The installed package version (``unknown`` for a source tree)."""
    try:
        return _pkg_version("devhelm")
    except PackageNotFoundError:
        return "unknown"


@dataclass(frozen=True)
class DevhelmConfig:
    """Configuration for the DevHelm API client."""

    token: str
    base_url: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None
    timeout: float = 30.0
    # Devtool surface identifier reported to the API. Defaults to
    # ``"sdk-py"``; wrappers such as the MCP server pass ``"mcp"``.
    surface: str = DEFAULT_SURFACE
    # Surface version. Defaults to the installed ``devhelm`` version.
    surface_version: str | None = None
    # Surface-specific metadata forwarded as ``X-DevHelm-<key>`` headers.
    surface_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class _CliContext:
    token: str
    api_url: str


def _cli_context() -> _CliContext | None:
    """The CLI's current context from ``~/.devhelm/contexts.json``, if any.

    Read-only and best effort: a missing or malformed file means no context.
    """
    path = Path.home() / ".devhelm" / "contexts.json"
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    contexts = raw.get("contexts")
    current = raw.get("current")
    if not isinstance(contexts, dict) or not isinstance(current, str):
        return None
    ctx = contexts.get(current)
    if not isinstance(ctx, dict):
        return None
    token = ctx.get("token")
    api_url = ctx.get("apiUrl")
    if not isinstance(token, str) or not token:
        return None
    return _CliContext(token=token, api_url=api_url if isinstance(api_url, str) else "")


def resolve_credentials(config: DevhelmConfig) -> tuple[str, str]:
    """Return ``(token, base_url)`` per the resolution order above."""
    token = config.token or os.environ.get("DEVHELM_API_TOKEN") or ""
    context = None if token else _cli_context()
    if context is not None:
        token = context.token
    if not token:
        raise client_error(
            "validation",
            "NO_TOKEN",
            "No API token. Pass token= to Devhelm(), set DEVHELM_API_TOKEN, "
            "or run `devhelm auth login`.",
            next_command="devhelm auth login",
        )
    base_url = (
        config.base_url
        or os.environ.get("DEVHELM_API_URL")
        or (context.api_url if context is not None else "")
        or DEFAULT_BASE_URL
    )
    return token, base_url.rstrip("/")


def _telemetry_headers(config: DevhelmConfig) -> dict[str, str]:
    """``X-DevHelm-Surface*`` headers; none when ``DEVHELM_TELEMETRY=0``."""
    if os.environ.get("DEVHELM_TELEMETRY", "").strip() == "0":
        return {}
    headers: dict[str, str] = {
        "X-DevHelm-Surface": config.surface,
        "X-DevHelm-Surface-Version": config.surface_version or _sdk_version(),
        # Always identify the underlying SDK so the API can tell a raw SDK
        # call from a wrapper built on it.
        "X-DevHelm-Sdk-Name": "sdk-py",
    }
    for key, value in config.surface_metadata.items():
        headers[f"X-DevHelm-{key}"] = value
    return headers


def client_header(config: DevhelmConfig) -> str:
    """``X-DevHelm-Client`` value: ``sdk-python/<version>`` or the wrapper's."""
    name = CLIENT_NAMES.get(config.surface, config.surface)
    return f"{name}/{config.surface_version or _sdk_version()}"


def _headers(config: DevhelmConfig, token: str) -> dict[str, str]:
    org_id = config.org_id or os.environ.get("DEVHELM_ORG_ID") or "1"
    workspace_id = config.workspace_id or os.environ.get("DEVHELM_WORKSPACE_ID")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-phelm-org-id": org_id,
        CLIENT_HEADER: client_header(config),
        **_telemetry_headers(config),
    }
    if workspace_id:
        headers["x-phelm-workspace-id"] = workspace_id
    return headers


def build_client(config: DevhelmConfig) -> httpx.Client:
    """Create a configured ``httpx.Client`` with auth and tenant headers."""
    token, base_url = resolve_credentials(config)
    return httpx.Client(
        base_url=base_url, headers=_headers(config, token), timeout=config.timeout
    )


def build_async_client(config: DevhelmConfig) -> httpx.AsyncClient:
    """Create a configured ``httpx.AsyncClient`` with auth and tenant headers."""
    token, base_url = resolve_credentials(config)
    return httpx.AsyncClient(
        base_url=base_url, headers=_headers(config, token), timeout=config.timeout
    )


# Kept for callers of the pre-transport helpers.
_JsonResponse = JsonResponse
_serialize_body = serialize_body
_decode_body = decode_body
checked_fetch = checked_json
