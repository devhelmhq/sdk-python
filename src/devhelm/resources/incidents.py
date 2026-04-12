from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import api_delete, api_get, api_post, path_param, unwrap_single
from devhelm._pagination import Page, fetch_all_pages, fetch_page


class Incidents:
    """Manual and auto-detected incidents."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Any]:
        """List all incidents (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/incidents")

    def list_page(self, page: int, size: int) -> Page[Any]:
        """List incidents with manual page control."""
        return fetch_page(self._client, "/api/v1/incidents", page, size)

    def get(self, id: int | str) -> Any:
        """Get a single incident by ID."""
        return unwrap_single(
            api_get(self._client, f"/api/v1/incidents/{path_param(id)}")
        )

    def create(self, body: dict[str, Any]) -> Any:
        """Create a manual incident."""
        return unwrap_single(api_post(self._client, "/api/v1/incidents", body))

    def resolve(self, id: int | str, message: str | None = None) -> Any:
        """Resolve an incident."""
        body = {"message": message} if message else {}
        return unwrap_single(
            api_post(self._client, f"/api/v1/incidents/{path_param(id)}/resolve", body)
        )

    def delete(self, id: int | str) -> None:
        """Delete an incident."""
        api_delete(self._client, f"/api/v1/incidents/{path_param(id)}")
