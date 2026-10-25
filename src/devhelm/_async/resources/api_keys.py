from __future__ import annotations

from devhelm._async.pagination import fetch_all_pages, fetch_page
from devhelm._async.transport import Client, api_delete, api_get, api_post, as_transport
from devhelm._generated import ApiKeyCreateResponse, ApiKeyDto, CreateApiKeyRequest
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class ApiKeys:
    """API key management."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> list[ApiKeyDto]:
        """List all API keys."""
        return await fetch_all_pages(self._client, "/api/v1/api-keys", ApiKeyDto)

    async def list_page(self, page: int, size: int) -> Page[ApiKeyDto]:
        """List API keys with manual page control."""
        return await fetch_page(self._client, "/api/v1/api-keys", ApiKeyDto, page, size)

    async def get(self, id: int | str) -> ApiKeyDto:
        """Get a single API key by ID."""
        return parse_single(
            ApiKeyDto,
            await api_get(self._client, f"/api/v1/api-keys/{path_param(id)}"),
            f"GET /api/v1/api-keys/{id}",
        )

    async def create(
        self, body: RequestBody[CreateApiKeyRequest]
    ) -> ApiKeyCreateResponse:
        """Create an API key. Returns the key value (shown only once)."""
        body = validate_request(CreateApiKeyRequest, body, "apiKeys.create")
        return parse_single(
            ApiKeyCreateResponse,
            await api_post(self._client, "/api/v1/api-keys", body),
            "POST /api/v1/api-keys",
        )

    async def revoke(self, id: int | str) -> None:
        """Revoke an API key."""
        await api_post(self._client, f"/api/v1/api-keys/{path_param(id)}/revoke")

    async def delete(self, id: int | str) -> None:
        """Delete an API key."""
        await api_delete(self._client, f"/api/v1/api-keys/{path_param(id)}")
