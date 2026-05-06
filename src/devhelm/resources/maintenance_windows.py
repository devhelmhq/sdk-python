from __future__ import annotations

import httpx

from devhelm._generated import (
    CreateMaintenanceWindowRequest,
    MaintenanceWindowDto,
    UpdateMaintenanceWindowRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import RequestBody, parse_single, validate_request

# Query-param values for ``GET /api/v1/maintenance-windows``. Both
# documented filters (``monitorId``, ``filter``) are single-valued strings;
# spelt as a concrete alias rather than ``Any`` so the resource layer stays
# ``Any``-free per ``tests/test_typing.py``.
_ListFilterValue = str


def _build_list_filters(
    monitor_id: str | None, status: str | None
) -> dict[str, _ListFilterValue]:
    """Pack the documented ``GET /api/v1/maintenance-windows`` query
    params into a single dict, dropping anything left at the default
    ``None`` so the wire request stays minimal and the API's defaults
    apply.

    Accepts snake_case at the Python boundary and emits the camelCase
    spelling the API expects (``monitor_id`` → ``monitorId``). The
    ergonomic ``status`` kwarg is mapped to the API's ``filter`` query
    param (which selects ``"active"`` or ``"upcoming"`` windows).
    """
    filters: dict[str, _ListFilterValue] = {}
    if monitor_id is not None:
        filters["monitorId"] = monitor_id
    if status is not None:
        filters["filter"] = status
    return filters


class MaintenanceWindows:
    """Scheduled maintenance windows that suppress alerts during planned downtime."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(
        self, *, monitor_id: str | None = None, status: str | None = None
    ) -> list[MaintenanceWindowDto]:
        """List all maintenance windows for the authenticated org (auto-paginates).

        Optional server-side filters mirror the documented
        ``GET /api/v1/maintenance-windows`` query params:

        * ``monitor_id`` — only return windows attached to this monitor.
        * ``status`` — ``"active"`` (currently in window) or
          ``"upcoming"`` (starts in the future).

        Examples:
            >>> client.maintenance_windows.list()
            [MaintenanceWindowDto(...), ...]
            >>> client.maintenance_windows.list(status="upcoming")
            [...]
        """
        # The API's documented query string omits ``page``/``size``, but the
        # response envelope is the standard ``TableValueResult`` shape that
        # all paginated lists in this codebase use, so the server accepts
        # those keys and ignores them where unused. Reusing
        # ``fetch_all_pages`` keeps the iterator semantics consistent with
        # every other ``MaintenanceWindows.list``-style method on this SDK.
        return fetch_all_pages(
            self._client,
            "/api/v1/maintenance-windows",
            MaintenanceWindowDto,
            extra_params=_build_list_filters(monitor_id, status),
        )

    def list_page(
        self,
        page: int,
        size: int,
        *,
        monitor_id: str | None = None,
        status: str | None = None,
    ) -> Page[MaintenanceWindowDto]:
        """List maintenance windows with manual page control.

        Accepts the same filter kwargs as :meth:`list` so callers using
        manual pagination get the same server-side filtering.
        """
        return fetch_page(
            self._client,
            "/api/v1/maintenance-windows",
            MaintenanceWindowDto,
            page,
            size,
            extra_params=_build_list_filters(monitor_id, status),
        )

    def get(self, id: str) -> MaintenanceWindowDto:
        """Get a single maintenance window by ID.

        Examples:
            >>> client.maintenance_windows.get("a8e3...")
            MaintenanceWindowDto(...)
        """
        return parse_single(
            MaintenanceWindowDto,
            api_get(self._client, f"/api/v1/maintenance-windows/{path_param(id)}"),
            f"GET /api/v1/maintenance-windows/{id}",
        )

    def create(
        self, body: RequestBody[CreateMaintenanceWindowRequest]
    ) -> MaintenanceWindowDto:
        """Create a new maintenance window.

        Pass ``monitorId=None`` to create an org-wide window that
        suppresses alerts for every monitor in the organisation; pass a
        UUID to scope the window to a single monitor.

        Examples:
            >>> from datetime import datetime, timedelta, timezone
            >>> start = datetime.now(timezone.utc) + timedelta(hours=1)
            >>> client.maintenance_windows.create({
            ...     "startsAt": start.isoformat(),
            ...     "endsAt": (start + timedelta(hours=2)).isoformat(),
            ...     "reason": "Quarterly DB upgrade",
            ...     "monitorId": "a8e3...",
            ... })
            MaintenanceWindowDto(...)
        """
        body = validate_request(
            CreateMaintenanceWindowRequest, body, "maintenanceWindows.create"
        )
        return parse_single(
            MaintenanceWindowDto,
            api_post(self._client, "/api/v1/maintenance-windows", body),
            "POST /api/v1/maintenance-windows",
        )

    def update(
        self, id: str, body: RequestBody[UpdateMaintenanceWindowRequest]
    ) -> MaintenanceWindowDto:
        """Update an existing maintenance window.

        Examples:
            >>> client.maintenance_windows.update("a8e3...", {
            ...     "startsAt": "2026-06-01T00:00:00Z",
            ...     "endsAt":   "2026-06-01T02:00:00Z",
            ...     "reason":   "Rescheduled DB upgrade",
            ... })
            MaintenanceWindowDto(...)
        """
        body = validate_request(
            UpdateMaintenanceWindowRequest, body, "maintenanceWindows.update"
        )
        return parse_single(
            MaintenanceWindowDto,
            api_put(
                self._client, f"/api/v1/maintenance-windows/{path_param(id)}", body
            ),
            f"PUT /api/v1/maintenance-windows/{id}",
        )

    def delete(self, id: str) -> None:
        """Delete (cancel) a maintenance window.

        The API exposes a ``DELETE`` operation for this resource; if you
        prefer the cancellation-style verb in your code, see
        :meth:`cancel`, which is a thin alias.
        """
        api_delete(self._client, f"/api/v1/maintenance-windows/{path_param(id)}")

    def cancel(self, id: str) -> None:
        """Cancel a scheduled maintenance window.

        Semantic alias for :meth:`delete` — both call the same underlying
        ``DELETE /api/v1/maintenance-windows/{id}`` endpoint, but
        ``cancel`` reads better in automation scripts that schedule and
        later cancel planned downtime.

        Examples:
            >>> client.maintenance_windows.cancel("a8e3...")
        """
        self.delete(id)
