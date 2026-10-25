# Generated from src/devhelm/_async/resources/resource_groups.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from devhelm._generated import (
    AddResourceGroupMemberRequest,
    CreateResourceGroupRequest,
    ResourceGroupDto,
    ResourceGroupMemberDto,
    UpdateResourceGroupRequest,
)
from devhelm._pages import Page
from devhelm._sync.pagination import fetch_all_pages, fetch_page
from devhelm._sync.transport import (
    Client,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class ResourceGroups:
    """Logical resource groups."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

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

    def create(self, body: RequestBody[CreateResourceGroupRequest]) -> ResourceGroupDto:
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
        self, id: int | str, body: RequestBody[UpdateResourceGroupRequest]
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
        self, group_id: int | str, body: RequestBody[AddResourceGroupMemberRequest]
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
