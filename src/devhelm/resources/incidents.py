# Generated from src/devhelm/_async/resources/incidents.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from devhelm._generated import (
    AcknowledgeAllIncidentsResponse,
    AddIncidentUpdateRequest,
    CreateManualIncidentRequest,
    IncidentActivityEventDto,
    IncidentDetailDto,
    IncidentDto,
    IncidentTriggerDto,
    RelatedIncidentsResponse,
    ResolveIncidentRequest,
    RunDto,
    UpdateIncidentRequest,
)
from devhelm._pages import CursorPage, Page
from devhelm._sync.pagination import fetch_all_pages, fetch_cursor_page, fetch_page
from devhelm._sync.transport import Client, api_get, api_patch, api_post, as_transport
from devhelm._transport import path_param
from devhelm._validation import (
    RequestBody,
    RequestValue,
    build_request,
    parse_model,
    parse_single,
    validate_request,
)


class Incidents:
    """Manual and auto-detected incidents."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def list(self) -> list[IncidentDto]:
        """List all incidents (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/incidents", IncidentDto)

    def list_page(self, page: int, size: int) -> Page[IncidentDto]:
        """List incidents with manual page control."""
        return fetch_page(self._client, "/api/v1/incidents", IncidentDto, page, size)

    def get(self, id: int | str) -> IncidentDetailDto:
        """Get a single incident by ID."""
        return parse_single(
            IncidentDetailDto,
            api_get(self._client, f"/api/v1/incidents/{path_param(id)}"),
            f"GET /api/v1/incidents/{id}",
        )

    def create(
        self, body: RequestBody[CreateManualIncidentRequest]
    ) -> IncidentDetailDto:
        """Create a manual incident."""
        body = validate_request(CreateManualIncidentRequest, body, "incidents.create")
        return parse_single(
            IncidentDetailDto,
            api_post(self._client, "/api/v1/incidents", body),
            "POST /api/v1/incidents",
        )

    def resolve(
        self, id: int | str, body: RequestBody[ResolveIncidentRequest] | None = None
    ) -> IncidentDetailDto:
        """Resolve an incident."""
        if body is not None:
            body = validate_request(ResolveIncidentRequest, body, "incidents.resolve")
        return parse_single(
            IncidentDetailDto,
            api_post(self._client, f"/api/v1/incidents/{path_param(id)}/resolve", body),
            f"POST /api/v1/incidents/{id}/resolve",
        )

    def update(
        self,
        id: int | str,
        body: RequestBody[UpdateIncidentRequest] | None = None,
        **fields: RequestValue,
    ) -> IncidentDetailDto:
        """Change an incident's title, severity or other fields."""
        req = build_request(UpdateIncidentRequest, body, fields, "incidents.update")
        path = f"/api/v1/incidents/{path_param(id)}"
        return parse_single(
            IncidentDetailDto, api_patch(self._client, path, req), f"PATCH {path}"
        )

    def acknowledge(self, id: int | str) -> AcknowledgeAllIncidentsResponse:
        """Acknowledge an incident (stops escalation)."""
        path = f"/api/v1/incidents/{path_param(id)}/acknowledge"
        return parse_single(
            AcknowledgeAllIncidentsResponse,
            api_post(self._client, path),
            f"POST {path}",
        )

    def add_update(
        self,
        id: int | str,
        request: RequestBody[AddIncidentUpdateRequest] | None = None,
        **fields: RequestValue,
    ) -> IncidentDetailDto:
        """Post a timeline update on an incident."""
        req = build_request(
            AddIncidentUpdateRequest, request, fields, "incidents.add_update"
        )
        path = f"/api/v1/incidents/{path_param(id)}/updates"
        return parse_single(
            IncidentDetailDto, api_post(self._client, path, req), f"POST {path}"
        )

    def runs(
        self, id: int | str, *, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[RunDto]:
        """Runs in the incident's window."""
        return fetch_cursor_page(
            self._client,
            f"/api/v1/incidents/{path_param(id)}/runs",
            RunDto,
            cursor,
            limit,
        )

    def events(
        self, id: int | str, *, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[IncidentActivityEventDto]:
        """The incident's activity feed."""
        return fetch_cursor_page(
            self._client,
            f"/api/v1/incidents/{path_param(id)}/events",
            IncidentActivityEventDto,
            cursor,
            limit,
        )

    def related(
        self, id: int | str, *, window_days: int | None = None, limit: int | None = None
    ) -> RelatedIncidentsResponse:
        """Incidents on the same monitors or services around the same time."""
        path = f"/api/v1/incidents/{path_param(id)}/related"
        params = {"windowDays": window_days, "limit": limit}
        return parse_model(
            RelatedIncidentsResponse, api_get(self._client, path, params), f"GET {path}"
        )

    def trigger(self, id: int | str) -> IncidentTriggerDto:
        """The run or check that opened the incident."""
        path = f"/api/v1/incidents/{path_param(id)}/trigger"
        return parse_single(
            IncidentTriggerDto, api_get(self._client, path), f"GET {path}"
        )
