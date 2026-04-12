from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from devhelm._errors import DevhelmError, error_from_response

DEFAULT_BASE_URL = "https://api.devhelm.io"
DEFAULT_PAGE_SIZE = 200


@dataclass(frozen=True)
class DevhelmConfig:
    """Configuration for the DevHelm API client."""

    token: str
    base_url: str = DEFAULT_BASE_URL
    org_id: str | None = None
    workspace_id: str | None = None
    timeout: float = 30.0


def _resolve(value: str | None, env_key: str, label: str) -> str:
    result = value or os.environ.get(env_key)
    if not result:
        raise DevhelmError(
            "VALIDATION",
            f"{label} is required. Pass it to Devhelm() or set {env_key}.",
            0,
        )
    return result


def _resolve_optional(value: str | None, env_key: str, default: str) -> str:
    return value or os.environ.get(env_key) or default


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
        },
        timeout=config.timeout,
    )


def path_param(value: str | int) -> str:
    """URL-encode a path parameter."""
    return quote(str(value), safe="")


def checked_fetch(response: httpx.Response) -> Any:
    """Check an httpx response and raise DevhelmError on failure."""
    if response.is_success:
        if response.status_code == 204:
            return None
        return response.json()
    raise error_from_response(response.status_code, response.text)


def unwrap_single(resp: Any) -> Any:
    """Unwrap a SingleValueResponse envelope: {data: T} -> T."""
    if isinstance(resp, dict) and "data" in resp:
        return resp["data"]
    return resp


def api_get(
    client: httpx.Client, path: str, params: dict[str, Any] | None = None
) -> Any:
    return checked_fetch(client.get(path, params=params))


def api_post(client: httpx.Client, path: str, body: Any = None) -> Any:
    if body is None:
        return checked_fetch(client.post(path))
    return checked_fetch(client.post(path, json=body))


def api_put(client: httpx.Client, path: str, body: Any) -> Any:
    return checked_fetch(client.put(path, json=body))


def api_patch(client: httpx.Client, path: str, body: Any) -> Any:
    return checked_fetch(client.patch(path, json=body))


def api_delete(client: httpx.Client, path: str) -> None:
    checked_fetch(client.delete(path))
