from __future__ import annotations

import httpx

from devhelm._generated import (
    AlertChannelDto,
    CreateAlertChannelRequest,
    TestChannelResult,
    UpdateAlertChannelRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single, validate_request


class AlertChannels:
    """Slack, email, webhook, and other alert channels."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[AlertChannelDto]:
        """List all alert channels (auto-paginates)."""
        return fetch_all_pages(self._client, "/api/v1/alert-channels", AlertChannelDto)

    def list_page(self, page: int, size: int) -> Page[AlertChannelDto]:
        """List alert channels with manual page control."""
        return fetch_page(
            self._client, "/api/v1/alert-channels", AlertChannelDto, page, size
        )

    def get(self, id: int | str) -> AlertChannelDto:
        """Get a single alert channel by ID."""
        return parse_single(
            AlertChannelDto,
            api_get(self._client, f"/api/v1/alert-channels/{path_param(id)}"),
            f"GET /api/v1/alert-channels/{id}",
        )

    def create(self, body: CreateAlertChannelRequest) -> AlertChannelDto:
        """Create a new alert channel."""
        body = validate_request(CreateAlertChannelRequest, body, "alertChannels.create")
        return parse_single(
            AlertChannelDto,
            api_post(self._client, "/api/v1/alert-channels", body),
            "POST /api/v1/alert-channels",
        )

    def update(self, id: int | str, body: UpdateAlertChannelRequest) -> AlertChannelDto:
        """Update an alert channel."""
        body = validate_request(UpdateAlertChannelRequest, body, "alertChannels.update")
        return parse_single(
            AlertChannelDto,
            api_put(self._client, f"/api/v1/alert-channels/{path_param(id)}", body),
            f"PUT /api/v1/alert-channels/{id}",
        )

    def delete(self, id: int | str) -> None:
        """Delete an alert channel."""
        api_delete(self._client, f"/api/v1/alert-channels/{path_param(id)}")

    def test(self, id: int | str) -> TestChannelResult:
        """Send a test notification to an alert channel."""
        return parse_single(
            TestChannelResult,
            api_post(self._client, f"/api/v1/alert-channels/{path_param(id)}/test"),
            f"POST /api/v1/alert-channels/{id}/test",
        )
