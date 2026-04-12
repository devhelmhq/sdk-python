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


class NotificationPolicies:
    """Routing rules for alerts."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all notification policies (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/notification-policies")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List notification policies with manual page control."""
        return fetch_page(self._client, "/api/v1/notification-policies", page, size)

    def get(self, id: int | str) -> Any:
        """Get a notification policy by ID."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/notification-policies/{path_param(id)}")
        )

    def create(self, body: dict[str, Any]) -> Any:
        """Create a notification policy."""
        return unwrap_single(
            api_post(self._client, "/api/v1/notification-policies", body)
        )

    def update(self, id: int | str, body: dict[str, Any]) -> Any:
        """Update a notification policy."""
        return unwrap_single(
            api_put(
                self._client, f"/api/v1/notification-policies/{path_param(id)}", body
            )
        )

    def delete(self, id: int | str) -> None:
        """Delete a notification policy."""
        api_delete(self._client, f"/api/v1/notification-policies/{path_param(id)}")

    def test(self, id: int | str) -> None:
        """Send a test dispatch to verify policy routing."""
        api_post(self._client, f"/api/v1/notification-policies/{path_param(id)}/test", {})
