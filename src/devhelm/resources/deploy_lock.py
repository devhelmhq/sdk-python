from __future__ import annotations

import httpx

from devhelm._generated import AcquireDeployLockRequest, DeployLockDto
from devhelm._http import api_delete, api_get, api_post, path_param
from devhelm._validation import (
    RequestBody,
    parse_single,
    parse_strict_envelope,
    validate_request,
)


class DeployLock:
    """Deploy lock for safe deployments."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def acquire(self, body: RequestBody[AcquireDeployLockRequest]) -> DeployLockDto:
        """Acquire a deploy lock."""
        body = validate_request(AcquireDeployLockRequest, body, "deployLock.acquire")
        return parse_single(
            DeployLockDto,
            api_post(self._client, "/api/v1/deploy/lock", body),
            "POST /api/v1/deploy/lock",
        )

    def current(self) -> DeployLockDto | None:
        """Get the current deploy lock, or ``None`` if unlocked.

        Uses :func:`parse_strict_envelope` so unknown top-level fields fail
        loud (P1) — the API returns ``{"data": null}`` when no lock is held,
        which is the only place in the SDK where ``data`` is legitimately
        nullable.
        """
        resp = api_get(self._client, "/api/v1/deploy/lock")
        return parse_strict_envelope(
            DeployLockDto, resp, optional=True, context="GET /api/v1/deploy/lock"
        )

    def release(self, lock_id: int | str) -> None:
        """Release a deploy lock by ID."""
        api_delete(self._client, f"/api/v1/deploy/lock/{path_param(lock_id)}")

    def force_release(self) -> None:
        """Force-release any active deploy lock."""
        api_delete(self._client, "/api/v1/deploy/lock/force")
