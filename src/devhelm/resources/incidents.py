from __future__ import annotations

import httpx

from devhelm._generated import (
    CreateManualIncidentRequest,
    IncidentDetailDto,
    IncidentDto,
    ResolveIncidentRequest,
)
from devhelm._http import api_delete, api_get, api_post, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single, validate_request


class Incidents:
    """Manual and auto-detected incidents."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

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

    def create(self, body: CreateManualIncidentRequest) -> IncidentDetailDto:
        """Create a manual incident."""
        body = validate_request(CreateManualIncidentRequest, body, "incidents.create")
        return parse_single(
            IncidentDetailDto,
            api_post(self._client, "/api/v1/incidents", body),
            "POST /api/v1/incidents",
        )

    def resolve(
        self, id: int | str, body: ResolveIncidentRequest | None = None
    ) -> IncidentDetailDto:
        """Resolve an incident."""
        if body is not None:
            body = validate_request(ResolveIncidentRequest, body, "incidents.resolve")
        return parse_single(
            IncidentDetailDto,
            api_post(self._client, f"/api/v1/incidents/{path_param(id)}/resolve", body),
            f"POST /api/v1/incidents/{id}/resolve",
        )

    def delete(self, id: int | str) -> None:
        """Delete an incident."""
        api_delete(self._client, f"/api/v1/incidents/{path_param(id)}")
