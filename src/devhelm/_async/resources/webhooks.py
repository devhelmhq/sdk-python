from __future__ import annotations

from devhelm._async.pagination import fetch_all_pages, fetch_page
from devhelm._async.transport import (
    Client,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._generated import (
    CreateWebhookEndpointRequest,
    UpdateWebhookEndpointRequest,
    WebhookEndpointDto,
    WebhookTestResult,
)
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class Webhooks:
    """Outgoing webhook endpoints."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> list[WebhookEndpointDto]:
        """List all webhook endpoints (auto-paginates)."""
        return await fetch_all_pages(
            self._client, "/api/v1/webhooks", WebhookEndpointDto
        )

    async def list_page(self, page: int, size: int) -> Page[WebhookEndpointDto]:
        """List webhook endpoints with manual page control."""
        return await fetch_page(
            self._client, "/api/v1/webhooks", WebhookEndpointDto, page, size
        )

    async def get(self, id: int | str) -> WebhookEndpointDto:
        """Get a webhook endpoint by ID."""
        return parse_single(
            WebhookEndpointDto,
            await api_get(self._client, f"/api/v1/webhooks/{path_param(id)}"),
            f"GET /api/v1/webhooks/{id}",
        )

    async def create(
        self, body: RequestBody[CreateWebhookEndpointRequest]
    ) -> WebhookEndpointDto:
        """Create a webhook endpoint."""
        body = validate_request(CreateWebhookEndpointRequest, body, "webhooks.create")
        return parse_single(
            WebhookEndpointDto,
            await api_post(self._client, "/api/v1/webhooks", body),
            "POST /api/v1/webhooks",
        )

    async def update(
        self, id: int | str, body: RequestBody[UpdateWebhookEndpointRequest]
    ) -> WebhookEndpointDto:
        """Update a webhook endpoint."""
        body = validate_request(UpdateWebhookEndpointRequest, body, "webhooks.update")
        return parse_single(
            WebhookEndpointDto,
            await api_put(self._client, f"/api/v1/webhooks/{path_param(id)}", body),
            f"PUT /api/v1/webhooks/{id}",
        )

    async def delete(self, id: int | str) -> None:
        """Delete a webhook endpoint."""
        await api_delete(self._client, f"/api/v1/webhooks/{path_param(id)}")

    async def test(self, id: int | str) -> WebhookTestResult:
        """Send a test event to this webhook."""
        return parse_single(
            WebhookTestResult,
            await api_post(self._client, f"/api/v1/webhooks/{path_param(id)}/test"),
            f"POST /api/v1/webhooks/{id}/test",
        )
