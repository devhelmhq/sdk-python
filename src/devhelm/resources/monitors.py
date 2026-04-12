from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import (
    api_delete,
    api_get,
    api_post,
    api_put,
    path_param,
    unwrap_single,
)
from devhelm._pagination import (
    CursorPage,
    Page,
    fetch_all_pages,
    fetch_cursor_page,
    fetch_page,
)


class Monitors:
    """HTTP, DNS, TCP, ICMP, MCP, and Heartbeat monitors."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all monitors (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/monitors")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List monitors with manual page control."""
        return fetch_page(self._client, "/api/v1/monitors", page, size)

    def get(self, id: int | str) -> Any:
        """Get a single monitor by ID."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/monitors/{path_param(id)}")
        )

    def create(self, body: dict[str, Any]) -> Any:
        """Create a new monitor."""
        return unwrap_single(api_post(self._client, "/api/v1/monitors", body))

    def update(self, id: int | str, body: dict[str, Any]) -> Any:
        """Update an existing monitor."""
        return unwrap_single(
            api_put(self._client, f"/api/v1/monitors/{path_param(id)}", body)
        )

    def delete(self, id: int | str) -> None:
        """Delete a monitor."""
        api_delete(self._client, f"/api/v1/monitors/{path_param(id)}")

    def pause(self, id: int | str) -> Any:
        """Pause a monitor."""
        return unwrap_single(
            api_post(self._client, f"/api/v1/monitors/{path_param(id)}/pause")
        )

    def resume(self, id: int | str) -> Any:
        """Resume a paused monitor."""
        return unwrap_single(
            api_post(self._client, f"/api/v1/monitors/{path_param(id)}/resume")
        )

    def test(self, id: int | str) -> Any:
        """Trigger an ad-hoc test run for a monitor."""
        return unwrap_single(
            api_post(self._client, f"/api/v1/monitors/{path_param(id)}/test")
        )

    def results(
        self, id: int | str, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[Any]:
        """List check results (cursor-paginated)."""
        return fetch_cursor_page(
            self._client,
            f"/api/v1/monitors/{path_param(id)}/results",
            cursor=cursor,
            limit=limit,
        )

    def versions(self, id: int | str, page: int = 0, size: int = 20) -> Page[Any]:
        """List monitor version history."""
        return fetch_page(
            self._client, f"/api/v1/monitors/{path_param(id)}/versions", page, size
        )
