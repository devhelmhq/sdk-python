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
from devhelm._validation import RequestBody, parse_single, validate_request

# Query-param values are scalar by construction here — every documented
# filter on ``GET /api/v1/monitors`` is a single bool/string. Spelt as a
# concrete union (rather than ``Any``) so the resource layer stays
# ``Any``-free per ``tests/test_typing.py``.
_ListFilterValue = str | bool


def _build_list_filters(
    enabled: bool | None,
    type: str | None,
    managed_by: str | None,
    tags: str | None,
    search: str | None,
    environment_id: str | None,
) -> dict[str, _ListFilterValue]:
    """Pack the documented ``GET /api/v1/monitors`` query params into a
    single dict, dropping anything left at the default ``None`` so the
    wire request stays minimal and the API's defaults apply.

    Accepts snake_case at the Python boundary and emits the camelCase
    spelling the API expects (``managed_by`` → ``managedBy``,
    ``environment_id`` → ``environmentId``).
    """
    filters: dict[str, _ListFilterValue] = {}
    if enabled is not None:
        filters["enabled"] = enabled
    if type is not None:
        filters["type"] = type
    if managed_by is not None:
        filters["managedBy"] = managed_by
    if tags is not None:
        filters["tags"] = tags
    if search is not None:
        filters["search"] = search
    if environment_id is not None:
        filters["environmentId"] = environment_id
    return filters


class Monitors:
    """HTTP, DNS, TCP, ICMP, MCP, and Heartbeat monitors."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(
        self,
        *,
        enabled: bool | None = None,
        type: str | None = None,
        managed_by: str | None = None,
        tags: str | None = None,
        search: str | None = None,
        environment_id: str | None = None,
    ) -> list[MonitorDto]:
        """List all monitors (auto-paginates).

        Optional server-side filters mirror the documented
        ``GET /api/v1/monitors`` query params. ``tags`` is a
        comma-separated list (``"prod,critical"``); the rest are
        single-valued.
        """
        return fetch_all_pages(
            self._client,
            "/api/v1/monitors",
            MonitorDto,
            extra_params=_build_list_filters(
                enabled, type, managed_by, tags, search, environment_id
            ),
        )

    def list_page(
        self,
        page: int,
        size: int,
        *,
        enabled: bool | None = None,
        type: str | None = None,
        managed_by: str | None = None,
        tags: str | None = None,
        search: str | None = None,
        environment_id: str | None = None,
    ) -> Page[MonitorDto]:
        """List monitors with manual page control.

        Accepts the same filter kwargs as :meth:`list` so callers using
        manual pagination get the same server-side filtering.
        """
        return fetch_page(
            self._client,
            "/api/v1/monitors",
            MonitorDto,
            page,
            size,
            extra_params=_build_list_filters(
                enabled, type, managed_by, tags, search, environment_id
            ),
        )

    def get(self, id: int | str) -> MonitorDto:
        """Get a single monitor by ID."""
        return parse_single(
            MonitorDto,
            api_get(self._client, f"/api/v1/monitors/{path_param(id)}"),
            f"GET /api/v1/monitors/{id}",
        )

    def create(self, body: RequestBody[CreateMonitorRequest]) -> MonitorDto:
        """Create a new monitor."""
        body = validate_request(CreateMonitorRequest, body, "monitors.create")
        return parse_single(
            MonitorDto,
            api_post(self._client, "/api/v1/monitors", body),
            "POST /api/v1/monitors",
        )

    def update(
        self, id: int | str, body: RequestBody[UpdateMonitorRequest]
    ) -> MonitorDto:
        """Update an existing monitor."""
        body = validate_request(UpdateMonitorRequest, body, "monitors.update")
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
