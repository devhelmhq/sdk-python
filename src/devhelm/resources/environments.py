from __future__ import annotations

import httpx

from devhelm._generated import (
    CreateEnvironmentRequest,
    EnvironmentDto,
    UpdateEnvironmentRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single, validate_request


class Environments:
    """Environment grouping (prod, staging, etc.)."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[EnvironmentDto]:
        """List all environments."""
        return fetch_all_pages(self._client, "/api/v1/environments", EnvironmentDto)

    def list_page(self, page: int, size: int) -> Page[EnvironmentDto]:
        """List environments with manual page control."""
        return fetch_page(
            self._client, "/api/v1/environments", EnvironmentDto, page, size
        )

    def get(self, slug: str) -> EnvironmentDto:
        """Get an environment by slug."""
        return parse_single(
            EnvironmentDto,
            api_get(self._client, f"/api/v1/environments/{path_param(slug)}"),
            f"GET /api/v1/environments/{slug}",
        )

    def create(self, body: CreateEnvironmentRequest) -> EnvironmentDto:
        """Create an environment."""
        body = validate_request(CreateEnvironmentRequest, body, "environments.create")
        return parse_single(
            EnvironmentDto,
            api_post(self._client, "/api/v1/environments", body),
            "POST /api/v1/environments",
        )

    def update(self, slug: str, body: UpdateEnvironmentRequest) -> EnvironmentDto:
        """Update an environment."""
        body = validate_request(UpdateEnvironmentRequest, body, "environments.update")
        return parse_single(
            EnvironmentDto,
            api_put(self._client, f"/api/v1/environments/{path_param(slug)}", body),
            f"PUT /api/v1/environments/{slug}",
        )

    def delete(self, slug: str) -> None:
        """Delete an environment."""
        api_delete(self._client, f"/api/v1/environments/{path_param(slug)}")
