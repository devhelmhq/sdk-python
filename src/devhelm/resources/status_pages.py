from __future__ import annotations

import httpx

from devhelm._generated import (
    AddCustomDomainRequest,
    AdminAddSubscriberRequest,
    CreateStatusPageComponentGroupRequest,
    CreateStatusPageComponentRequest,
    CreateStatusPageIncidentRequest,
    CreateStatusPageIncidentUpdateRequest,
    CreateStatusPageRequest,
    ReorderComponentsRequest,
    StatusPageComponentDto,
    StatusPageComponentGroupDto,
    StatusPageCustomDomainDto,
    StatusPageDto,
    StatusPageIncidentDto,
    StatusPageSubscriberDto,
    UpdateStatusPageComponentGroupRequest,
    UpdateStatusPageComponentRequest,
    UpdateStatusPageIncidentRequest,
    UpdateStatusPageRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import RequestBody, parse_single, validate_request

_BASE = "/api/v1/status-pages"


def _page_path(page_id: int | str) -> str:
    return f"{_BASE}/{path_param(page_id)}"


class _Components:
    """Status page component operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self, page_id: int | str) -> list[StatusPageComponentDto]:
        """List all components on a status page."""
        return fetch_all_pages(
            self._client, f"{_page_path(page_id)}/components", StatusPageComponentDto
        )

    def create(
        self, page_id: int | str, body: RequestBody[CreateStatusPageComponentRequest]
    ) -> StatusPageComponentDto:
        """Add a component to a status page."""
        body = validate_request(
            CreateStatusPageComponentRequest, body, "statusPages.components.create"
        )
        return parse_single(
            StatusPageComponentDto,
            api_post(self._client, f"{_page_path(page_id)}/components", body),
            f"POST {_page_path(page_id)}/components",
        )

    def update(
        self,
        page_id: int | str,
        component_id: int | str,
        body: RequestBody[UpdateStatusPageComponentRequest],
    ) -> StatusPageComponentDto:
        """Update a component."""
        body = validate_request(
            UpdateStatusPageComponentRequest, body, "statusPages.components.update"
        )
        return parse_single(
            StatusPageComponentDto,
            api_put(
                self._client,
                f"{_page_path(page_id)}/components/{path_param(component_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/components/{component_id}",
        )

    def delete(self, page_id: int | str, component_id: int | str) -> None:
        """Remove a component from a status page."""
        api_delete(
            self._client, f"{_page_path(page_id)}/components/{path_param(component_id)}"
        )

    def reorder(
        self, page_id: int | str, body: RequestBody[ReorderComponentsRequest]
    ) -> None:
        """Batch reorder components."""
        body = validate_request(
            ReorderComponentsRequest, body, "statusPages.components.reorder"
        )
        api_put(self._client, f"{_page_path(page_id)}/components/reorder", body)


class _Groups:
    """Status page component group operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self, page_id: int | str) -> list[StatusPageComponentGroupDto]:
        """List all component groups (with nested components)."""
        return fetch_all_pages(
            self._client, f"{_page_path(page_id)}/groups", StatusPageComponentGroupDto
        )

    def create(
        self,
        page_id: int | str,
        body: RequestBody[CreateStatusPageComponentGroupRequest],
    ) -> StatusPageComponentGroupDto:
        """Create a component group."""
        body = validate_request(
            CreateStatusPageComponentGroupRequest, body, "statusPages.groups.create"
        )
        return parse_single(
            StatusPageComponentGroupDto,
            api_post(self._client, f"{_page_path(page_id)}/groups", body),
            f"POST {_page_path(page_id)}/groups",
        )

    def update(
        self,
        page_id: int | str,
        group_id: int | str,
        body: RequestBody[UpdateStatusPageComponentGroupRequest],
    ) -> StatusPageComponentGroupDto:
        """Update a component group."""
        body = validate_request(
            UpdateStatusPageComponentGroupRequest, body, "statusPages.groups.update"
        )
        return parse_single(
            StatusPageComponentGroupDto,
            api_put(
                self._client,
                f"{_page_path(page_id)}/groups/{path_param(group_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/groups/{group_id}",
        )

    def delete(self, page_id: int | str, group_id: int | str) -> None:
        """Delete a component group."""
        api_delete(self._client, f"{_page_path(page_id)}/groups/{path_param(group_id)}")


class _Incidents:
    """Status page incident operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(
        self, page_id: int | str, *, page: int = 0, size: int = 20
    ) -> Page[StatusPageIncidentDto]:
        """List incidents on a status page (paginated)."""
        return fetch_page(
            self._client,
            f"{_page_path(page_id)}/incidents",
            StatusPageIncidentDto,
            page,
            size,
        )

    def get(self, page_id: int | str, incident_id: int | str) -> StatusPageIncidentDto:
        """Get a single incident with timeline."""
        return parse_single(
            StatusPageIncidentDto,
            api_get(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}",
            ),
            f"GET {_page_path(page_id)}/incidents/{incident_id}",
        )

    def create(
        self, page_id: int | str, body: RequestBody[CreateStatusPageIncidentRequest]
    ) -> StatusPageIncidentDto:
        """Create a status page incident."""
        body = validate_request(
            CreateStatusPageIncidentRequest, body, "statusPages.incidents.create"
        )
        return parse_single(
            StatusPageIncidentDto,
            api_post(self._client, f"{_page_path(page_id)}/incidents", body),
            f"POST {_page_path(page_id)}/incidents",
        )

    def update(
        self,
        page_id: int | str,
        incident_id: int | str,
        body: RequestBody[UpdateStatusPageIncidentRequest],
    ) -> StatusPageIncidentDto:
        """Update an incident."""
        body = validate_request(
            UpdateStatusPageIncidentRequest, body, "statusPages.incidents.update"
        )
        return parse_single(
            StatusPageIncidentDto,
            api_put(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/incidents/{incident_id}",
        )

    def post_update(
        self,
        page_id: int | str,
        incident_id: int | str,
        body: RequestBody[CreateStatusPageIncidentUpdateRequest],
    ) -> StatusPageIncidentDto:
        """Post a timeline update on an incident."""
        body = validate_request(
            CreateStatusPageIncidentUpdateRequest,
            body,
            "statusPages.incidents.postUpdate",
        )
        return parse_single(
            StatusPageIncidentDto,
            api_post(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/updates",
                body,
            ),
            f"POST {_page_path(page_id)}/incidents/{incident_id}/updates",
        )

    def publish(
        self, page_id: int | str, incident_id: int | str
    ) -> StatusPageIncidentDto:
        """Publish a draft incident."""
        return parse_single(
            StatusPageIncidentDto,
            api_post(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/publish",
            ),
            f"POST {_page_path(page_id)}/incidents/{incident_id}/publish",
        )

    def dismiss(self, page_id: int | str, incident_id: int | str) -> None:
        """Dismiss a draft incident."""
        api_post(
            self._client,
            f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/dismiss",
        )

    def delete(self, page_id: int | str, incident_id: int | str) -> None:
        """Delete an incident."""
        api_delete(
            self._client, f"{_page_path(page_id)}/incidents/{path_param(incident_id)}"
        )


class _Subscribers:
    """Status page subscriber operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(
        self, page_id: int | str, *, page: int = 0, size: int = 20
    ) -> Page[StatusPageSubscriberDto]:
        """List confirmed subscribers (paginated)."""
        return fetch_page(
            self._client,
            f"{_page_path(page_id)}/subscribers",
            StatusPageSubscriberDto,
            page,
            size,
        )

    def add(
        self, page_id: int | str, body: RequestBody[AdminAddSubscriberRequest]
    ) -> StatusPageSubscriberDto:
        """Add a subscriber (admin)."""
        body = validate_request(
            AdminAddSubscriberRequest, body, "statusPages.subscribers.add"
        )
        return parse_single(
            StatusPageSubscriberDto,
            api_post(self._client, f"{_page_path(page_id)}/subscribers", body),
            f"POST {_page_path(page_id)}/subscribers",
        )

    def remove(self, page_id: int | str, subscriber_id: int | str) -> None:
        """Remove a subscriber."""
        api_delete(
            self._client,
            f"{_page_path(page_id)}/subscribers/{path_param(subscriber_id)}",
        )


class _Domains:
    """Status page custom domain operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self, page_id: int | str) -> list[StatusPageCustomDomainDto]:
        """List custom domains on a status page."""
        return fetch_all_pages(
            self._client, f"{_page_path(page_id)}/domains", StatusPageCustomDomainDto
        )

    def add(
        self, page_id: int | str, body: RequestBody[AddCustomDomainRequest]
    ) -> StatusPageCustomDomainDto:
        """Add a custom domain."""
        body = validate_request(AddCustomDomainRequest, body, "statusPages.domains.add")
        return parse_single(
            StatusPageCustomDomainDto,
            api_post(self._client, f"{_page_path(page_id)}/domains", body),
            f"POST {_page_path(page_id)}/domains",
        )

    def verify(
        self, page_id: int | str, domain_id: int | str
    ) -> StatusPageCustomDomainDto:
        """Trigger domain verification check."""
        return parse_single(
            StatusPageCustomDomainDto,
            api_post(
                self._client,
                f"{_page_path(page_id)}/domains/{path_param(domain_id)}/verify",
            ),
            f"POST {_page_path(page_id)}/domains/{domain_id}/verify",
        )

    def remove(self, page_id: int | str, domain_id: int | str) -> None:
        """Remove a custom domain."""
        api_delete(
            self._client, f"{_page_path(page_id)}/domains/{path_param(domain_id)}"
        )


class StatusPages:
    """Status page management with sub-resources for components, groups,
    incidents, subscribers, and custom domains."""

    components: _Components
    groups: _Groups
    incidents: _Incidents
    subscribers: _Subscribers
    domains: _Domains

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self.components = _Components(client)
        self.groups = _Groups(client)
        self.incidents = _Incidents(client)
        self.subscribers = _Subscribers(client)
        self.domains = _Domains(client)

    def list(self) -> list[StatusPageDto]:
        """List all status pages in the workspace."""
        return fetch_all_pages(self._client, _BASE, StatusPageDto)

    def get(self, id: int | str) -> StatusPageDto:
        """Get a status page by ID."""
        return parse_single(
            StatusPageDto,
            api_get(self._client, _page_path(id)),
            f"GET {_page_path(id)}",
        )

    def create(self, body: RequestBody[CreateStatusPageRequest]) -> StatusPageDto:
        """Create a status page."""
        body = validate_request(CreateStatusPageRequest, body, "statusPages.create")
        return parse_single(
            StatusPageDto,
            api_post(self._client, _BASE, body),
            "POST /api/v1/status-pages",
        )

    def update(
        self, id: int | str, body: RequestBody[UpdateStatusPageRequest]
    ) -> StatusPageDto:
        """Update a status page."""
        body = validate_request(UpdateStatusPageRequest, body, "statusPages.update")
        return parse_single(
            StatusPageDto,
            api_put(self._client, _page_path(id), body),
            f"PUT {_page_path(id)}",
        )

    def delete(self, id: int | str) -> None:
        """Delete a status page."""
        api_delete(self._client, _page_path(id))
