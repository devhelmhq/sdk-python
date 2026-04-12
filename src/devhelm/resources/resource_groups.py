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


class ResourceGroups:
    """Logical resource groups."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all resource groups."""
        return fetch_all_pages(self._client, "/api/v1/resource-groups")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List resource groups with manual page control."""
        return fetch_page(self._client, "/api/v1/resource-groups", page, size)

    def get(self, id: int | str) -> Any:
        """Get a resource group by ID."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/resource-groups/{path_param(id)}")
        )

    def create(self, body: dict[str, Any]) -> Any:
        """Create a resource group."""
        return unwrap_single(api_post(self._client, "/api/v1/resource-groups", body))

    def update(self, id: int | str, body: dict[str, Any]) -> Any:
        """Update a resource group."""
        return unwrap_single(
            api_put(self._client, f"/api/v1/resource-groups/{path_param(id)}", body)
        )

    def delete(self, id: int | str) -> None:
        """Delete a resource group."""
        api_delete(self._client, f"/api/v1/resource-groups/{path_param(id)}")

    def add_member(self, group_id: int | str, body: dict[str, Any]) -> Any:
        """Add a member to a resource group."""
        return unwrap_single(
            api_post(
                self._client,
                f"/api/v1/resource-groups/{path_param(group_id)}/members",
                body,
            )
        )

    def remove_member(self, group_id: int | str, member_id: int | str) -> None:
        """Remove a member from a resource group."""
        api_delete(
            self._client,
            f"/api/v1/resource-groups/{path_param(group_id)}/members/{path_param(member_id)}",
        )
