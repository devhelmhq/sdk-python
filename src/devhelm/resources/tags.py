# Generated from src/devhelm/_async/resources/tags.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from devhelm._generated import CreateTagRequest, TagDto, UpdateTagRequest
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


class Tags:
    """Organize monitors with tags."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def list(self) -> list[TagDto]:
        """List all tags (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/tags", TagDto)

    def list_page(self, page: int, size: int) -> Page[TagDto]:
        """List tags with manual page control."""
        return fetch_page(self._client, "/api/v1/tags", TagDto, page, size)

    def get(self, id: int | str) -> TagDto:
        """Get a tag by ID."""
        return parse_single(
            TagDto,
            api_get(self._client, f"/api/v1/tags/{path_param(id)}"),
            f"GET /api/v1/tags/{id}",
        )

    def create(self, body: RequestBody[CreateTagRequest]) -> TagDto:
        """Create a tag."""
        body = validate_request(CreateTagRequest, body, "tags.create")
        return parse_single(
            TagDto, api_post(self._client, "/api/v1/tags", body), "POST /api/v1/tags"
        )

    def update(self, id: int | str, body: RequestBody[UpdateTagRequest]) -> TagDto:
        """Update a tag."""
        body = validate_request(UpdateTagRequest, body, "tags.update")
        return parse_single(
            TagDto,
            api_put(self._client, f"/api/v1/tags/{path_param(id)}", body),
            f"PUT /api/v1/tags/{id}",
        )

    def delete(self, id: int | str) -> None:
        """Delete a tag."""
        api_delete(self._client, f"/api/v1/tags/{path_param(id)}")
