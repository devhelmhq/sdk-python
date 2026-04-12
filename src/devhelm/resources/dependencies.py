from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import api_delete, api_get, api_post, path_param, unwrap_single
from devhelm._pagination import Page, fetch_all_pages, fetch_page


class Dependencies:
    """Service dependency tracking (service subscriptions)."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all tracked service dependencies."""
        return fetch_all_pages(self._client, "/api/v1/service-subscriptions")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List tracked dependencies with manual page control."""
        return fetch_page(self._client, "/api/v1/service-subscriptions", page, size)

    def get(self, id: int | str) -> Any:
        """Get a tracked dependency by ID."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/service-subscriptions/{path_param(id)}")
        )

    def track(self, slug: str) -> Any:
        """Track a new service dependency by slug."""
        return unwrap_single(
            api_post(self._client, f"/api/v1/service-subscriptions/{path_param(slug)}")
        )

    def delete(self, id: int | str) -> None:
        """Remove a tracked dependency."""
        api_delete(self._client, f"/api/v1/service-subscriptions/{path_param(id)}")
