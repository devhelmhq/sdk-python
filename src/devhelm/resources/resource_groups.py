from __future__ import annotations

import httpx

from devhelm._generated import (
    AddResourceGroupMemberRequest,
    CreateResourceGroupRequest,
    ResourceGroupDto,
    ResourceGroupMemberDto,
    UpdateResourceGroupRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single, validate_request


class ResourceGroups:
    """Logical resource groups."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[ResourceGroupDto]:
        """List all resource groups."""
        return fetch_all_pages(
            self._client, "/api/v1/resource-groups", ResourceGroupDto
        )

    def list_page(self, page: int, size: int) -> Page[ResourceGroupDto]:
        """List resource groups with manual page control."""
        return fetch_page(
            self._client, "/api/v1/resource-groups", ResourceGroupDto, page, size
        )

    def get(self, id: int | str) -> ResourceGroupDto:
        """Get a resource group by ID."""
        return parse_single(
            ResourceGroupDto,
            api_get(self._client, f"/api/v1/resource-groups/{path_param(id)}"),
            f"GET /api/v1/resource-groups/{id}",
        )

    def create(self, body: CreateResourceGroupRequest) -> ResourceGroupDto:
        """Create a resource group."""
        body = validate_request(
            CreateResourceGroupRequest, body, "resourceGroups.create"
        )
        return parse_single(
            ResourceGroupDto,
            api_post(self._client, "/api/v1/resource-groups", body),
            "POST /api/v1/resource-groups",
        )

    def update(
        self, id: int | str, body: UpdateResourceGroupRequest
    ) -> ResourceGroupDto:
        """Update a resource group."""
        body = validate_request(
            UpdateResourceGroupRequest, body, "resourceGroups.update"
        )
        return parse_single(
            ResourceGroupDto,
            api_put(self._client, f"/api/v1/resource-groups/{path_param(id)}", body),
            f"PUT /api/v1/resource-groups/{id}",
        )

    def delete(self, id: int | str) -> None:
        """Delete a resource group."""
        api_delete(self._client, f"/api/v1/resource-groups/{path_param(id)}")

    def add_member(
        self, group_id: int | str, body: AddResourceGroupMemberRequest
    ) -> ResourceGroupMemberDto:
        """Add a member to a resource group."""
        body = validate_request(
            AddResourceGroupMemberRequest, body, "resourceGroups.addMember"
        )
        return parse_single(
            ResourceGroupMemberDto,
            api_post(
                self._client,
                f"/api/v1/resource-groups/{path_param(group_id)}/members",
                body,
            ),
            f"POST /api/v1/resource-groups/{group_id}/members",
        )

    def remove_member(self, group_id: int | str, member_id: int | str) -> None:
        """Remove a member from a resource group."""
        api_delete(
            self._client,
            f"/api/v1/resource-groups/{path_param(group_id)}/members/{path_param(member_id)}",
        )
