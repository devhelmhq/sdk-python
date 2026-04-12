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


class Environments:
    """Environment grouping (prod, staging, etc.)."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all environments."""
        return fetch_all_pages(self._client, "/api/v1/environments")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List environments with manual page control."""
        return fetch_page(self._client, "/api/v1/environments", page, size)

    def get(self, slug: str) -> Any:
        """Get an environment by slug."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/environments/{path_param(slug)}")
        )

    def create(self, body: dict[str, Any]) -> Any:
        """Create an environment."""
        return unwrap_single(api_post(self._client, "/api/v1/environments", body))

    def update(self, slug: str, body: dict[str, Any]) -> Any:
        """Update an environment."""
        return unwrap_single(
            api_put(self._client, f"/api/v1/environments/{path_param(slug)}", body)
        )

    def delete(self, slug: str) -> None:
        """Delete an environment."""
        api_delete(self._client, f"/api/v1/environments/{path_param(slug)}")
