"""Status Data catalog: third-party service status, components, incidents,
uptime, and maintenances.

These are the read-only ``/api/v1/services`` + ``/api/v1/categories``
endpoints backing DevHelm's vendor-status catalog (the data the dependency
tracker subscribes to). Services are addressed by slug (``"github"``) or
UUID interchangeably — every ``slug_or_id`` parameter accepts either.
"""

from __future__ import annotations

import builtins
from datetime import date, datetime
from typing import TypeVar

import httpx
from pydantic import BaseModel

from devhelm._generated import (
    BatchComponentUptimeDto,
    CategoryDto,
    ComponentUptimeDayDto,
    GlobalStatusSummaryDto,
    ScheduledMaintenanceDto,
    ServiceCatalogDto,
    ServiceComponentDto,
    ServiceDayDetailDto,
    ServiceDetailDto,
    ServiceIncidentDetailDto,
    ServiceIncidentDto,
    ServiceLiveStatusDto,
    ServiceUptimeResponse,
)
from devhelm._http import api_get, path_param
from devhelm._pagination import CursorPage, Page, _validate_page, fetch_cursor_page
from devhelm._validation import parse_list, parse_single

M = TypeVar("M", bound=BaseModel)

# Explicit primitive-only param dict avoids mypy's ``disallow_any_explicit``
# in strict mode while still accepting the shapes httpx serialises for us.
# List values serialise as repeated query keys (``status=a&status=b``).
_ParamValue = str | int | bool | list[str] | None
_ParamDict = dict[str, _ParamValue]


def _format_date(value: date | datetime | str) -> str:
    """Normalise ``from``/``to`` calendar params to the ISO ``yyyy-MM-dd``
    the API expects. ``datetime`` is truncated to its calendar day because
    the endpoints reject full timestamps.
    """
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _window_params(
    period: str, from_: date | datetime | str | None, to: date | datetime | str | None
) -> _ParamDict:
    """Pack the shared uptime-window params. ``period`` is always sent (the
    API documents that an explicit ``from``/``to`` window wins over it when
    both are supplied, so forwarding the default is harmless).
    """
    params: _ParamDict = {"period": period}
    if from_ is not None:
        params["from"] = _format_date(from_)
    if to is not None:
        params["to"] = _format_date(to)
    return params


_BASE = "/api/v1/services"


def _service_path(slug_or_id: str) -> str:
    return f"{_BASE}/{path_param(slug_or_id)}"


class Services:
    """Status Data catalog: vendor services, components, incidents, uptime."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def _fetch_table(
        self, path: str, model_class: type[M], params: _ParamDict | None = None
    ) -> list[M]:
        """Catalog list endpoints return the offset-page envelope
        ``{data, hasNext, hasPrev, …}`` but are not actually paginated
        server-side (no ``page``/``size`` params) — unwrap the envelope and
        hand back the validated items directly.
        """
        resp = api_get(self._client, path, params=params or None)
        envelope = _validate_page(resp)
        return parse_list(model_class, envelope.data, f"GET {path}")

    def list(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> CursorPage[ServiceCatalogDto]:
        """List catalog services (cursor-paginated).

        Optional server-side filters mirror the documented
        ``GET /api/v1/services`` query params: ``category`` (exact
        category name), ``status`` (current overall status, e.g.
        ``"operational"``), and ``search`` (free-text match on name/slug).
        Pass ``cursor`` from a previous page's ``next_cursor`` to continue.
        """
        filters: _ParamDict = {}
        if category is not None:
            filters["category"] = category
        if status is not None:
            filters["status"] = status
        if search is not None:
            filters["search"] = search
        return fetch_cursor_page(
            self._client,
            _BASE,
            ServiceCatalogDto,
            cursor=cursor,
            limit=limit,
            extra_params=filters,
        )

    def get(self, slug_or_id: str, *, summary: bool = False) -> ServiceDetailDto:
        """Get a service's detail view by slug or ID.

        ``summary=True`` requests the trimmed payload (component groups
        without leaf children) used by list-style consumers.
        """
        params: _ParamDict | None = {"summary": True} if summary else None
        return parse_single(
            ServiceDetailDto,
            api_get(self._client, _service_path(slug_or_id), params=params),
            f"GET {_BASE}/{slug_or_id}",
        )

    def live_status(self, slug_or_id: str) -> ServiceLiveStatusDto:
        """Get a service's current live status (overall + per-component)."""
        return parse_single(
            ServiceLiveStatusDto,
            api_get(self._client, f"{_service_path(slug_or_id)}/live-status"),
            f"GET {_BASE}/{slug_or_id}/live-status",
        )

    # ``builtins.list`` below because the ``list`` *method* shadows the
    # builtin inside the class body for everything defined after it.
    def categories(self) -> builtins.list[CategoryDto]:
        """List all service categories with their service counts."""
        return self._fetch_table("/api/v1/categories", CategoryDto)

    def summary(self) -> GlobalStatusSummaryDto:
        """Get the global status summary across the whole catalog."""
        return parse_single(
            GlobalStatusSummaryDto,
            api_get(self._client, f"{_BASE}/summary"),
            f"GET {_BASE}/summary",
        )

    def components(
        self, slug_or_id: str, *, group_id: str | None = None
    ) -> builtins.list[ServiceComponentDto]:
        """List a service's active components.

        ``group_id`` restricts the result to direct children of that group
        component.
        """
        params: _ParamDict = {}
        if group_id is not None:
            params["groupId"] = group_id
        return self._fetch_table(
            f"{_service_path(slug_or_id)}/components", ServiceComponentDto, params
        )

    def component_uptime(
        self,
        slug_or_id: str,
        component_id: str,
        *,
        period: str = "30d",
        from_: date | datetime | str | None = None,
        to: date | datetime | str | None = None,
    ) -> builtins.list[ComponentUptimeDayDto]:
        """Get daily uptime data for one component.

        Pass either a preset ``period`` (``7d``, ``30d``, ``90d``, ``1y``)
        or an explicit ``from_``/``to`` calendar window (ISO ``yyyy-MM-dd``,
        max 730 days; ``to`` defaults to today). The explicit window wins
        when both are supplied.
        """
        return self._fetch_table(
            f"{_service_path(slug_or_id)}/components/{path_param(component_id)}/uptime",
            ComponentUptimeDayDto,
            _window_params(period, from_, to),
        )

    def batch_component_uptime(
        self,
        slug_or_id: str,
        *,
        period: str = "30d",
        from_: date | datetime | str | None = None,
        to: date | datetime | str | None = None,
    ) -> BatchComponentUptimeDto:
        """Get daily uptime for every leaf component in a single request,
        keyed by component ID.

        Accepts the same window kwargs as :meth:`component_uptime`.
        """
        return parse_single(
            BatchComponentUptimeDto,
            api_get(
                self._client,
                f"{_service_path(slug_or_id)}/components/uptime",
                params=_window_params(period, from_, to),
            ),
            f"GET {_BASE}/{slug_or_id}/components/uptime",
        )

    def day(self, slug_or_id: str, date: date | str) -> ServiceDayDetailDto:
        """Get the per-component rollup for one UTC calendar day
        (ISO ``yyyy-MM-dd``).
        """
        return parse_single(
            ServiceDayDetailDto,
            api_get(
                self._client,
                f"{_service_path(slug_or_id)}/days/{path_param(_format_date(date))}",
            ),
            f"GET {_BASE}/{slug_or_id}/days/{date}",
        )

    def incidents(
        self,
        slug_or_id: str | None = None,
        *,
        status: str | None = None,
        from_: date | datetime | str | None = None,
        category: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> Page[ServiceIncidentDto]:
        """List vendor incidents (paginated).

        With ``slug_or_id``, lists incidents for that one service; without
        it, lists incidents across the whole catalog. ``status`` filters by
        incident status (e.g. ``"resolved"``), ``from_`` bounds the window
        start, and ``category`` (cross-service mode only) restricts to one
        service category.
        """
        if slug_or_id is None:
            path = f"{_BASE}/incidents"
        else:
            path = f"{_service_path(slug_or_id)}/incidents"
        params: _ParamDict = {"page": page, "size": size}
        if status is not None:
            params["status"] = status
        if from_ is not None:
            params["from"] = _format_date(from_)
        if category is not None:
            params["category"] = category

        resp = api_get(self._client, path, params=params)
        envelope = _validate_page(resp)
        return Page(
            data=parse_list(ServiceIncidentDto, envelope.data, f"GET {path}"),
            has_next=envelope.hasNext,
            has_prev=envelope.hasPrev,
            total_elements=envelope.totalElements,
            total_pages=envelope.totalPages,
        )

    def incident(self, slug_or_id: str, incident_id: str) -> ServiceIncidentDetailDto:
        """Get one vendor incident with its full update timeline."""
        return parse_single(
            ServiceIncidentDetailDto,
            api_get(
                self._client,
                f"{_service_path(slug_or_id)}/incidents/{path_param(incident_id)}",
            ),
            f"GET {_BASE}/{slug_or_id}/incidents/{incident_id}",
        )

    def uptime(
        self, slug_or_id: str, *, period: str = "30d", granularity: str = "daily"
    ) -> ServiceUptimeResponse:
        """Get a service's uptime with per-bucket breakdown.

        ``period`` is a preset window (``7d``, ``30d``, ``90d``, ``1y``);
        ``granularity`` is ``"hourly"`` or ``"daily"``.
        """
        return parse_single(
            ServiceUptimeResponse,
            api_get(
                self._client,
                f"{_service_path(slug_or_id)}/uptime",
                params={"period": period, "granularity": granularity},
            ),
            f"GET {_BASE}/{slug_or_id}/uptime",
        )

    def maintenances(
        self, slug_or_id: str, *, status: str | builtins.list[str] | None = None
    ) -> builtins.list[ScheduledMaintenanceDto]:
        """List a service's scheduled maintenances.

        ``status`` filters by maintenance status (``scheduled``,
        ``in_progress``, ``completed``); pass a list to match several.
        """
        params: _ParamDict = {}
        if status is not None:
            params["status"] = status
        return self._fetch_table(
            f"{_service_path(slug_or_id)}/maintenances", ScheduledMaintenanceDto, params
        )
