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


class AlertChannels:
    """Slack, email, webhook, and other alert channels."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all alert channels (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/alert-channels")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List alert channels with manual page control."""
        return fetch_page(self._client, "/api/v1/alert-channels", page, size)

    def get(self, id: int | str) -> Any:
        """Get a single alert channel by ID."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/alert-channels/{path_param(id)}")
        )

    def create(self, body: dict[str, Any]) -> Any:
        """Create a new alert channel."""
        return unwrap_single(api_post(self._client, "/api/v1/alert-channels", body))

    def update(self, id: int | str, body: dict[str, Any]) -> Any:
        """Update an alert channel."""
        return unwrap_single(
            api_put(self._client, f"/api/v1/alert-channels/{path_param(id)}", body)
        )

    def delete(self, id: int | str) -> None:
        """Delete an alert channel."""
        api_delete(self._client, f"/api/v1/alert-channels/{path_param(id)}")

    def test(self, id: int | str) -> Any:
        """Send a test notification to an alert channel."""
        return unwrap_single(
            api_post(self._client, f"/api/v1/alert-channels/{path_param(id)}/test")
        )
