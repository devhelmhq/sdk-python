from __future__ import annotations

import httpx

from devhelm._generated import (
    AssertionTestResultDto,
    CheckResultDto,
    CreateMonitorRequest,
    MonitorDto,
    MonitorVersionDto,
    UpdateMonitorRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import (
    CursorPage,
    Page,
    fetch_all_pages,
    fetch_cursor_page,
    fetch_page,
)
from devhelm._validation import parse_single


class Monitors:
    """HTTP, DNS, TCP, ICMP, MCP, and Heartbeat monitors."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[MonitorDto]:
        """List all monitors (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/monitors", MonitorDto)

    def list_page(self, page: int, size: int) -> Page[MonitorDto]:
        """List monitors with manual page control."""
        return fetch_page(self._client, "/api/v1/monitors", MonitorDto, page, size)

    def get(self, id: int | str) -> MonitorDto:
        """Get a single monitor by ID."""
        return parse_single(
            MonitorDto,
            api_get(self._client, f"/api/v1/monitors/{path_param(id)}"),
            f"GET /api/v1/monitors/{id}",
        )

    def create(self, body: CreateMonitorRequest) -> MonitorDto:
        """Create a new monitor."""
        return parse_single(
            MonitorDto,
            api_post(self._client, "/api/v1/monitors", body),
            "POST /api/v1/monitors",
        )

    def update(self, id: int | str, body: UpdateMonitorRequest) -> MonitorDto:
        """Update an existing monitor."""
        return parse_single(
            MonitorDto,
            api_put(self._client, f"/api/v1/monitors/{path_param(id)}", body),
            f"PUT /api/v1/monitors/{id}",
        )

    def delete(self, id: int | str) -> None:
        """Delete a monitor."""
        api_delete(self._client, f"/api/v1/monitors/{path_param(id)}")

    def pause(self, id: int | str) -> MonitorDto:
        """Pause a monitor."""
        return parse_single(
            MonitorDto,
            api_post(self._client, f"/api/v1/monitors/{path_param(id)}/pause"),
            f"POST /api/v1/monitors/{id}/pause",
        )

    def resume(self, id: int | str) -> MonitorDto:
        """Resume a paused monitor."""
        return parse_single(
            MonitorDto,
            api_post(self._client, f"/api/v1/monitors/{path_param(id)}/resume"),
            f"POST /api/v1/monitors/{id}/resume",
        )

    def test(self, id: int | str) -> AssertionTestResultDto:
        """Trigger an ad-hoc test run for a monitor."""
        return parse_single(
            AssertionTestResultDto,
            api_post(self._client, f"/api/v1/monitors/{path_param(id)}/test"),
            f"POST /api/v1/monitors/{id}/test",
        )

    def results(
        self, id: int | str, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[CheckResultDto]:
        """List check results (cursor-paginated)."""
        return fetch_cursor_page(
            self._client,
            f"/api/v1/monitors/{path_param(id)}/results",
            CheckResultDto,
            cursor=cursor,
            limit=limit,
        )

    def versions(
        self, id: int | str, page: int = 0, size: int = 20
    ) -> Page[MonitorVersionDto]:
        """List monitor version history."""
        return fetch_page(
            self._client,
            f"/api/v1/monitors/{path_param(id)}/versions",
            MonitorVersionDto,
            page,
            size,
        )
