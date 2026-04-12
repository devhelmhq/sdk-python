from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import api_delete, api_post, path_param, unwrap_single
from devhelm._pagination import Page, fetch_all_pages, fetch_page


class ApiKeys:
    """API key management."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all API keys."""
        return fetch_all_pages(self._client, "/api/v1/api-keys")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List API keys with manual page control."""
        return fetch_page(self._client, "/api/v1/api-keys", page, size)

    def create(self, body: dict[str, Any]) -> Any:
        """Create an API key. Returns the key value (shown only once)."""
        return unwrap_single(api_post(self._client, "/api/v1/api-keys", body))

    def revoke(self, id: int | str) -> None:
        """Revoke an API key."""
        api_post(self._client, f"/api/v1/api-keys/{path_param(id)}/revoke")

    def delete(self, id: int | str) -> None:
        """Delete an API key."""
        api_delete(self._client, f"/api/v1/api-keys/{path_param(id)}")
