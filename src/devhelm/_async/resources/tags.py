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
from devhelm._generated import CreateTagRequest, TagDto, UpdateTagRequest
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class Tags:
    """Organize monitors with tags."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> list[TagDto]:
        """List all tags (auto-paginates)."""
        return await fetch_all_pages(self._client, "/api/v1/tags", TagDto)

    async def list_page(self, page: int, size: int) -> Page[TagDto]:
        """List tags with manual page control."""
        return await fetch_page(self._client, "/api/v1/tags", TagDto, page, size)

    async def get(self, id: int | str) -> TagDto:
        """Get a tag by ID."""
        return parse_single(
            TagDto,
            await api_get(self._client, f"/api/v1/tags/{path_param(id)}"),
            f"GET /api/v1/tags/{id}",
        )

    async def create(self, body: RequestBody[CreateTagRequest]) -> TagDto:
        """Create a tag."""
        body = validate_request(CreateTagRequest, body, "tags.create")
        return parse_single(
            TagDto,
            await api_post(self._client, "/api/v1/tags", body),
            "POST /api/v1/tags",
        )

    async def update(
        self, id: int | str, body: RequestBody[UpdateTagRequest]
    ) -> TagDto:
        """Update a tag."""
        body = validate_request(UpdateTagRequest, body, "tags.update")
        return parse_single(
            TagDto,
            await api_put(self._client, f"/api/v1/tags/{path_param(id)}", body),
            f"PUT /api/v1/tags/{id}",
        )

    async def delete(self, id: int | str) -> None:
        """Delete a tag."""
        await api_delete(self._client, f"/api/v1/tags/{path_param(id)}")
