from __future__ import annotations

from devhelm._async.pagination import fetch_all_pages, fetch_page
from devhelm._async.transport import (
    Client,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._generated import (
    AddCustomDomainRequest,
    AdminAddSubscriberRequest,
    CreateStatusPageComponentGroupRequest,
    CreateStatusPageComponentRequest,
    CreateStatusPageIncidentRequest,
    CreateStatusPageIncidentUpdateRequest,
    CreateStatusPageMaintenanceRequest,
    CreateStatusPageRequest,
    ReorderComponentsRequest,
    ReorderPageLayoutRequest,
    SetStatusPageComponentOverrideRequest,
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
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import (
    RequestBody,
    RequestValue,
    build_request,
    parse_single,
    validate_request,
)

_BASE = "/api/v1/status-pages"


def _page_path(page_id: int | str) -> str:
    return f"{_BASE}/{path_param(page_id)}"


class _Components:
    """Status page component operations."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(self, page_id: int | str) -> list[StatusPageComponentDto]:
        """List all components on a status page."""
        return await fetch_all_pages(
            self._client, f"{_page_path(page_id)}/components", StatusPageComponentDto
        )

    async def create(
        self, page_id: int | str, body: RequestBody[CreateStatusPageComponentRequest]
    ) -> StatusPageComponentDto:
        """Add a component to a status page."""
        body = validate_request(
            CreateStatusPageComponentRequest, body, "statusPages.components.create"
        )
        return parse_single(
            StatusPageComponentDto,
            await api_post(self._client, f"{_page_path(page_id)}/components", body),
            f"POST {_page_path(page_id)}/components",
        )

    async def update(
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
            await api_put(
                self._client,
                f"{_page_path(page_id)}/components/{path_param(component_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/components/{component_id}",
        )

    async def delete(self, page_id: int | str, component_id: int | str) -> None:
        """Remove a component from a status page."""
        await api_delete(
            self._client, f"{_page_path(page_id)}/components/{path_param(component_id)}"
        )

    async def reorder(
        self, page_id: int | str, body: RequestBody[ReorderComponentsRequest]
    ) -> None:
        """Batch reorder components."""
        body = validate_request(
            ReorderComponentsRequest, body, "statusPages.components.reorder"
        )
        await api_put(self._client, f"{_page_path(page_id)}/components/reorder", body)

    async def set_override(
        self,
        page_id: int | str,
        component_id: int | str,
        body: RequestBody[SetStatusPageComponentOverrideRequest] | None = None,
        **fields: RequestValue,
    ) -> StatusPageComponentDto:
        """Pin a component's public status, overriding the monitor's verdict."""
        req = build_request(
            SetStatusPageComponentOverrideRequest,
            body,
            fields,
            "statusPages.components.set_override",
        )
        path = f"{_page_path(page_id)}/components/{path_param(component_id)}/override"
        return parse_single(
            StatusPageComponentDto,
            await api_put(self._client, path, req),
            f"PUT {path}",
        )

    async def clear_override(
        self, page_id: int | str, component_id: int | str
    ) -> StatusPageComponentDto:
        """Let the component follow its monitor again."""
        path = f"{_page_path(page_id)}/components/{path_param(component_id)}/override"
        return parse_single(
            StatusPageComponentDto,
            await api_delete(self._client, path),
            f"DELETE {path}",
        )


class _Groups:
    """Status page component group operations."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self, page_id: int | str) -> list[StatusPageComponentGroupDto]:
        """List all component groups (with nested components)."""
        return await fetch_all_pages(
            self._client, f"{_page_path(page_id)}/groups", StatusPageComponentGroupDto
        )

    async def create(
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
            await api_post(self._client, f"{_page_path(page_id)}/groups", body),
            f"POST {_page_path(page_id)}/groups",
        )

    async def update(
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
            await api_put(
                self._client,
                f"{_page_path(page_id)}/groups/{path_param(group_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/groups/{group_id}",
        )

    async def delete(self, page_id: int | str, group_id: int | str) -> None:
        """Delete a component group."""
        await api_delete(
            self._client, f"{_page_path(page_id)}/groups/{path_param(group_id)}"
        )


class _Incidents:
    """Status page incident operations."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self, page_id: int | str, *, page: int = 0, size: int = 20
    ) -> Page[StatusPageIncidentDto]:
        """List incidents on a status page (paginated)."""
        return await fetch_page(
            self._client,
            f"{_page_path(page_id)}/incidents",
            StatusPageIncidentDto,
            page,
            size,
        )

    async def get(
        self, page_id: int | str, incident_id: int | str
    ) -> StatusPageIncidentDto:
        """Get a single incident with timeline."""
        return parse_single(
            StatusPageIncidentDto,
            await api_get(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}",
            ),
            f"GET {_page_path(page_id)}/incidents/{incident_id}",
        )

    async def create(
        self, page_id: int | str, body: RequestBody[CreateStatusPageIncidentRequest]
    ) -> StatusPageIncidentDto:
        """Create a status page incident."""
        body = validate_request(
            CreateStatusPageIncidentRequest, body, "statusPages.incidents.create"
        )
        return parse_single(
            StatusPageIncidentDto,
            await api_post(self._client, f"{_page_path(page_id)}/incidents", body),
            f"POST {_page_path(page_id)}/incidents",
        )

    async def update(
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
            await api_put(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/incidents/{incident_id}",
        )

    async def post_update(
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
            await api_post(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/updates",
                body,
            ),
            f"POST {_page_path(page_id)}/incidents/{incident_id}/updates",
        )

    async def publish(
        self, page_id: int | str, incident_id: int | str
    ) -> StatusPageIncidentDto:
        """Publish a draft incident."""
        return parse_single(
            StatusPageIncidentDto,
            await api_post(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/publish",
            ),
            f"POST {_page_path(page_id)}/incidents/{incident_id}/publish",
        )

    async def dismiss(self, page_id: int | str, incident_id: int | str) -> None:
        """Dismiss a draft incident."""
        await api_post(
            self._client,
            f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/dismiss",
        )

    async def delete(self, page_id: int | str, incident_id: int | str) -> None:
        """Delete an incident."""
        await api_delete(
            self._client, f"{_page_path(page_id)}/incidents/{path_param(incident_id)}"
        )


class _Maintenance:
    """Status page maintenance window operations."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(
        self, page_id: int | str, *, page: int = 0, size: int = 20
    ) -> Page[StatusPageIncidentDto]:
        """List maintenance windows on a status page (paginated)."""
        return await fetch_page(
            self._client,
            f"{_page_path(page_id)}/maintenance",
            StatusPageIncidentDto,
            page,
            size,
        )

    async def get(
        self, page_id: int | str, window_id: int | str
    ) -> StatusPageIncidentDto:
        """Get a single maintenance window with timeline."""
        return parse_single(
            StatusPageIncidentDto,
            await api_get(
                self._client,
                f"{_page_path(page_id)}/maintenance/{path_param(window_id)}",
            ),
            f"GET {_page_path(page_id)}/maintenance/{window_id}",
        )

    async def create(
        self, page_id: int | str, body: RequestBody[CreateStatusPageMaintenanceRequest]
    ) -> StatusPageIncidentDto:
        """Schedule a maintenance window on a status page."""
        body = validate_request(
            CreateStatusPageMaintenanceRequest, body, "statusPages.maintenance.create"
        )
        return parse_single(
            StatusPageIncidentDto,
            await api_post(self._client, f"{_page_path(page_id)}/maintenance", body),
            f"POST {_page_path(page_id)}/maintenance",
        )

    async def update(
        self,
        page_id: int | str,
        window_id: int | str,
        body: RequestBody[UpdateStatusPageIncidentRequest],
    ) -> StatusPageIncidentDto:
        """Update a maintenance window."""
        body = validate_request(
            UpdateStatusPageIncidentRequest, body, "statusPages.maintenance.update"
        )
        return parse_single(
            StatusPageIncidentDto,
            await api_put(
                self._client,
                f"{_page_path(page_id)}/maintenance/{path_param(window_id)}",
                body,
            ),
            f"PUT {_page_path(page_id)}/maintenance/{window_id}",
        )

    async def post_update(
        self,
        page_id: int | str,
        window_id: int | str,
        body: RequestBody[CreateStatusPageIncidentUpdateRequest],
    ) -> StatusPageIncidentDto:
        """Post a timeline update on a maintenance window."""
        body = validate_request(
            CreateStatusPageIncidentUpdateRequest,
            body,
            "statusPages.maintenance.postUpdate",
        )
        return parse_single(
            StatusPageIncidentDto,
            await api_post(
                self._client,
                f"{_page_path(page_id)}/maintenance/{path_param(window_id)}/updates",
                body,
            ),
            f"POST {_page_path(page_id)}/maintenance/{window_id}/updates",
        )

    async def publish(
        self, page_id: int | str, window_id: int | str
    ) -> StatusPageIncidentDto:
        """Publish a draft maintenance window."""
        return parse_single(
            StatusPageIncidentDto,
            await api_post(
                self._client,
                f"{_page_path(page_id)}/maintenance/{path_param(window_id)}/publish",
            ),
            f"POST {_page_path(page_id)}/maintenance/{window_id}/publish",
        )

    async def dismiss(self, page_id: int | str, window_id: int | str) -> None:
        """Dismiss a draft maintenance window."""
        await api_post(
            self._client,
            f"{_page_path(page_id)}/maintenance/{path_param(window_id)}/dismiss",
        )

    async def delete(self, page_id: int | str, window_id: int | str) -> None:
        """Delete a maintenance window."""
        await api_delete(
            self._client, f"{_page_path(page_id)}/maintenance/{path_param(window_id)}"
        )


class _Subscribers:
    """Status page subscriber operations."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self, page_id: int | str, *, page: int = 0, size: int = 20
    ) -> Page[StatusPageSubscriberDto]:
        """List confirmed subscribers (paginated)."""
        return await fetch_page(
            self._client,
            f"{_page_path(page_id)}/subscribers",
            StatusPageSubscriberDto,
            page,
            size,
        )

    async def add(
        self, page_id: int | str, body: RequestBody[AdminAddSubscriberRequest]
    ) -> StatusPageSubscriberDto:
        """Add a subscriber (admin)."""
        body = validate_request(
            AdminAddSubscriberRequest, body, "statusPages.subscribers.add"
        )
        return parse_single(
            StatusPageSubscriberDto,
            await api_post(self._client, f"{_page_path(page_id)}/subscribers", body),
            f"POST {_page_path(page_id)}/subscribers",
        )

    async def remove(self, page_id: int | str, subscriber_id: int | str) -> None:
        """Remove a subscriber."""
        await api_delete(
            self._client,
            f"{_page_path(page_id)}/subscribers/{path_param(subscriber_id)}",
        )


class _Domains:
    """Status page custom domain operations."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self, page_id: int | str) -> list[StatusPageCustomDomainDto]:
        """List custom domains on a status page."""
        return await fetch_all_pages(
            self._client, f"{_page_path(page_id)}/domains", StatusPageCustomDomainDto
        )

    async def add(
        self, page_id: int | str, body: RequestBody[AddCustomDomainRequest]
    ) -> StatusPageCustomDomainDto:
        """Add a custom domain."""
        body = validate_request(AddCustomDomainRequest, body, "statusPages.domains.add")
        return parse_single(
            StatusPageCustomDomainDto,
            await api_post(self._client, f"{_page_path(page_id)}/domains", body),
            f"POST {_page_path(page_id)}/domains",
        )

    async def verify(
        self, page_id: int | str, domain_id: int | str
    ) -> StatusPageCustomDomainDto:
        """Trigger domain verification check."""
        return parse_single(
            StatusPageCustomDomainDto,
            await api_post(
                self._client,
                f"{_page_path(page_id)}/domains/{path_param(domain_id)}/verify",
            ),
            f"POST {_page_path(page_id)}/domains/{domain_id}/verify",
        )

    async def remove(self, page_id: int | str, domain_id: int | str) -> None:
        """Remove a custom domain."""
        await api_delete(
            self._client, f"{_page_path(page_id)}/domains/{path_param(domain_id)}"
        )


class StatusPages:
    """Status page management with sub-resources for components, groups,
    incidents, maintenance windows, subscribers, and custom domains."""

    components: _Components
    groups: _Groups
    incidents: _Incidents
    maintenance: _Maintenance
    subscribers: _Subscribers
    domains: _Domains

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)
        self.components = _Components(client)
        self.groups = _Groups(client)
        self.incidents = _Incidents(client)
        self.maintenance = _Maintenance(client)
        self.subscribers = _Subscribers(client)
        self.domains = _Domains(client)

    async def list(self) -> list[StatusPageDto]:
        """List all status pages in the workspace."""
        return await fetch_all_pages(self._client, _BASE, StatusPageDto)

    async def get(self, id: int | str) -> StatusPageDto:
        """Get a status page by ID."""
        return parse_single(
            StatusPageDto,
            await api_get(self._client, _page_path(id)),
            f"GET {_page_path(id)}",
        )

    async def create(self, body: RequestBody[CreateStatusPageRequest]) -> StatusPageDto:
        """Create a status page."""
        body = validate_request(CreateStatusPageRequest, body, "statusPages.create")
        return parse_single(
            StatusPageDto,
            await api_post(self._client, _BASE, body),
            "POST /api/v1/status-pages",
        )

    async def update(
        self, id: int | str, body: RequestBody[UpdateStatusPageRequest]
    ) -> StatusPageDto:
        """Update a status page."""
        body = validate_request(UpdateStatusPageRequest, body, "statusPages.update")
        return parse_single(
            StatusPageDto,
            await api_put(self._client, _page_path(id), body),
            f"PUT {_page_path(id)}",
        )

    async def delete(self, id: int | str) -> None:
        """Delete a status page."""
        await api_delete(self._client, _page_path(id))

    async def reorder_layout(
        self, id: int | str, body: RequestBody[ReorderPageLayoutRequest]
    ) -> None:
        """Batch-reorder the page layout: top-level sections (groups +
        ungrouped components) and, optionally, within-group component ordering.

        Returns 204 No Content on success.
        """
        body = validate_request(
            ReorderPageLayoutRequest, body, "statusPages.reorderLayout"
        )
        await api_put(self._client, f"{_page_path(id)}/layout/reorder", body)
