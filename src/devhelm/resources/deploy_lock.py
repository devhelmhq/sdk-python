from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import api_delete, api_get, api_post, path_param, unwrap_single


class DeployLock:
    """Deploy lock for safe deployments."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def acquire(self, body: dict[str, Any]) -> Any:
        """Acquire a deploy lock."""
        return unwrap_single(api_post(self._client, "/api/v1/deploy/lock", body))

    def current(self) -> Any | None:
        """Get the current deploy lock, or None if unlocked."""
        resp = api_get(self._client, "/api/v1/deploy/lock")
        if isinstance(resp, dict):
            return resp.get("data")
        return None

    def release(self, lock_id: int | str) -> None:
        """Release a deploy lock by ID."""
        api_delete(self._client, f"/api/v1/deploy/lock/{path_param(lock_id)}")

    def force_release(self) -> None:
        """Force-release any active deploy lock."""
        api_delete(self._client, "/api/v1/deploy/lock/force")
