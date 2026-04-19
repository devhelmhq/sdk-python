from __future__ import annotations

import httpx

from devhelm._generated import ApiKeyCreateResponse, ApiKeyDto, CreateApiKeyRequest
from devhelm._http import api_delete, api_post, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single


class ApiKeys:
    """API key management."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[ApiKeyDto]:
        """List all API keys."""
        return fetch_all_pages(self._client, "/api/v1/api-keys", ApiKeyDto)

    def list_page(self, page: int, size: int) -> Page[ApiKeyDto]:
        """List API keys with manual page control."""
        return fetch_page(self._client, "/api/v1/api-keys", ApiKeyDto, page, size)

    def create(self, body: CreateApiKeyRequest) -> ApiKeyCreateResponse:
        """Create an API key. Returns the key value (shown only once)."""
        return parse_single(
            ApiKeyCreateResponse,
            api_post(self._client, "/api/v1/api-keys", body),
            "POST /api/v1/api-keys",
        )

    def revoke(self, id: int | str) -> None:
        """Revoke an API key."""
        api_post(self._client, f"/api/v1/api-keys/{path_param(id)}/revoke")

    def delete(self, id: int | str) -> None:
        """Delete an API key."""
        api_delete(self._client, f"/api/v1/api-keys/{path_param(id)}")
