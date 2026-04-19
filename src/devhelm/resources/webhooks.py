from __future__ import annotations

import httpx

from devhelm._generated import (
    CreateWebhookEndpointRequest,
    UpdateWebhookEndpointRequest,
    WebhookEndpointDto,
    WebhookTestResult,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single


class Webhooks:
    """Outgoing webhook endpoints."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[WebhookEndpointDto]:
        """List all webhook endpoints (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/webhooks", WebhookEndpointDto)

    def list_page(self, page: int, size: int) -> Page[WebhookEndpointDto]:
        """List webhook endpoints with manual page control."""
        return fetch_page(
            self._client, "/api/v1/webhooks", WebhookEndpointDto, page, size
        )

    def get(self, id: int | str) -> WebhookEndpointDto:
        """Get a webhook endpoint by ID."""
        return parse_single(
            WebhookEndpointDto,
            api_get(self._client, f"/api/v1/webhooks/{path_param(id)}"),
            f"GET /api/v1/webhooks/{id}",
        )

    def create(self, body: CreateWebhookEndpointRequest) -> WebhookEndpointDto:
        """Create a webhook endpoint."""
        return parse_single(
            WebhookEndpointDto,
            api_post(self._client, "/api/v1/webhooks", body),
            "POST /api/v1/webhooks",
        )

    def update(
        self, id: int | str, body: UpdateWebhookEndpointRequest
    ) -> WebhookEndpointDto:
        """Update a webhook endpoint."""
        return parse_single(
            WebhookEndpointDto,
            api_put(self._client, f"/api/v1/webhooks/{path_param(id)}", body),
            f"PUT /api/v1/webhooks/{id}",
        )

    def delete(self, id: int | str) -> None:
        """Delete a webhook endpoint."""
        api_delete(self._client, f"/api/v1/webhooks/{path_param(id)}")

    def test(self, id: int | str) -> WebhookTestResult:
        """Send a test event to this webhook."""
        return parse_single(
            WebhookTestResult,
            api_post(self._client, f"/api/v1/webhooks/{path_param(id)}/test"),
            f"POST /api/v1/webhooks/{id}/test",
        )
