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
from devhelm._pagination import Page, fetch_all_pages, fetch_page

_BASE = "/api/v1/status-pages"


def _page_path(page_id: int | str) -> str:
    return f"{_BASE}/{path_param(page_id)}"


class _Components:
    """Status page component operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self, page_id: int | str) -> list[Any]:
        """List all components on a status page."""
        return fetch_all_pages(self._client, f"{_page_path(page_id)}/components")

    def create(self, page_id: int | str, body: dict[str, Any]) -> Any:
        """Add a component to a status page."""
        return unwrap_single(
            api_post(self._client, f"{_page_path(page_id)}/components", body)
        )

    def update(
        self, page_id: int | str, component_id: int | str, body: dict[str, Any]
    ) -> Any:
        """Update a component."""
        return unwrap_single(
            api_put(
                self._client,
                f"{_page_path(page_id)}/components/{path_param(component_id)}",
                body,
            )
        )

    def delete(self, page_id: int | str, component_id: int | str) -> None:
        """Remove a component from a status page."""
        api_delete(
            self._client, f"{_page_path(page_id)}/components/{path_param(component_id)}"
        )

    def reorder(self, page_id: int | str, body: dict[str, Any]) -> None:
        """Batch reorder components."""
        api_put(self._client, f"{_page_path(page_id)}/components/reorder", body)


class _Groups:
    """Status page component group operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self, page_id: int | str) -> list[Any]:
        """List all component groups (with nested components)."""
        return fetch_all_pages(self._client, f"{_page_path(page_id)}/groups")

    def create(self, page_id: int | str, body: dict[str, Any]) -> Any:
        """Create a component group."""
        return unwrap_single(
            api_post(self._client, f"{_page_path(page_id)}/groups", body)
        )

    def update(
        self, page_id: int | str, group_id: int | str, body: dict[str, Any]
    ) -> Any:
        """Update a component group."""
        return unwrap_single(
            api_put(
                self._client,
                f"{_page_path(page_id)}/groups/{path_param(group_id)}",
                body,
            )
        )

    def delete(self, page_id: int | str, group_id: int | str) -> None:
        """Delete a component group."""
        api_delete(self._client, f"{_page_path(page_id)}/groups/{path_param(group_id)}")


class _Incidents:
    """Status page incident operations."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self, page_id: int | str, *, page: int = 0, size: int = 20) -> Page[Any]:
        """List incidents on a status page (paginated)."""
        return fetch_page(self._client, f"{_page_path(page_id)}/incidents", page, size)

    def get(self, page_id: int | str, incident_id: int | str) -> Any:
        """Get a single incident with timeline."""
        return unwrap_single(
            api_get(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}",
            )
        )

    def create(self, page_id: int | str, body: dict[str, Any]) -> Any:
        """Create a status page incident."""
        return unwrap_single(
            api_post(self._client, f"{_page_path(page_id)}/incidents", body)
        )

    def update(
        self, page_id: int | str, incident_id: int | str, body: dict[str, Any]
    ) -> Any:
        """Update an incident."""
        return unwrap_single(
            api_put(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}",
                body,
            )
        )

    def post_update(
        self, page_id: int | str, incident_id: int | str, body: dict[str, Any]
    ) -> Any:
        """Post a timeline update on an incident."""
        return unwrap_single(
            api_post(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/updates",
                body,
            )
        )

    def publish(
        self,
        page_id: int | str,
        incident_id: int | str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """Publish a draft incident."""
        return unwrap_single(
            api_post(
                self._client,
                f"{_page_path(page_id)}/incidents/{path_param(incident_id)}/publish",
                body,
            )
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

    def list(self, page_id: int | str, *, page: int = 0, size: int = 20) -> Page[Any]:
        """List confirmed subscribers (paginated)."""
        return fetch_page(
            self._client, f"{_page_path(page_id)}/subscribers", page, size
        )

    def add(self, page_id: int | str, body: dict[str, Any]) -> Any:
        """Add a subscriber (admin)."""
        return unwrap_single(
            api_post(self._client, f"{_page_path(page_id)}/subscribers", body)
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

    def list(self, page_id: int | str) -> list[Any]:
        """List custom domains on a status page."""
        return fetch_all_pages(self._client, f"{_page_path(page_id)}/domains")

    def add(self, page_id: int | str, body: dict[str, Any]) -> Any:
        """Add a custom domain."""
        return unwrap_single(
            api_post(self._client, f"{_page_path(page_id)}/domains", body)
        )

    def verify(self, page_id: int | str, domain_id: int | str) -> Any:
        """Trigger domain verification check."""
        return unwrap_single(
            api_post(
                self._client,
                f"{_page_path(page_id)}/domains/{path_param(domain_id)}/verify",
            )
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

    def list(self) -> list[Any]:
        """List all status pages in the workspace."""
        return fetch_all_pages(self._client, _BASE)

    def get(self, id: int | str) -> Any:
        """Get a status page by ID."""
        return unwrap_single(api_get(self._client, _page_path(id)))

    def create(self, body: dict[str, Any]) -> Any:
        """Create a status page."""
        return unwrap_single(api_post(self._client, _BASE, body))

    def update(self, id: int | str, body: dict[str, Any]) -> Any:
        """Update a status page."""
        return unwrap_single(api_put(self._client, _page_path(id), body))

    def delete(self, id: int | str) -> None:
        """Delete a status page."""
        api_delete(self._client, _page_path(id))
