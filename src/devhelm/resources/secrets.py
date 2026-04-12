from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import api_delete, api_post, api_put, path_param, unwrap_single
from devhelm._pagination import Page, fetch_all_pages, fetch_page


class Secrets:
    """Encrypted secrets for monitor auth."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all secrets (metadata only, not values)."""
        return fetch_all_pages(self._client, "/api/v1/secrets")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List secrets with manual page control."""
        return fetch_page(self._client, "/api/v1/secrets", page, size)

    def create(self, body: dict[str, Any]) -> Any:
        """Create a secret."""
        return unwrap_single(api_post(self._client, "/api/v1/secrets", body))

    def update(self, key: str, body: dict[str, Any]) -> Any:
        """Update a secret by key."""
        return unwrap_single(
            api_put(self._client, f"/api/v1/secrets/{path_param(key)}", body)
        )

    def delete(self, key: str) -> None:
        """Delete a secret by key."""
        api_delete(self._client, f"/api/v1/secrets/{path_param(key)}")
