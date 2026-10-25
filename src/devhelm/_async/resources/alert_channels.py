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
    AlertChannelDto,
    CreateAlertChannelRequest,
    TestChannelResult,
    UpdateAlertChannelRequest,
)
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class AlertChannels:
    """Slack, email, webhook, and other alert channels."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> list[AlertChannelDto]:
        """List all alert channels (auto-paginates)."""
        return await fetch_all_pages(
            self._client, "/api/v1/alert-channels", AlertChannelDto
        )

    async def list_page(self, page: int, size: int) -> Page[AlertChannelDto]:
        """List alert channels with manual page control."""
        return await fetch_page(
            self._client, "/api/v1/alert-channels", AlertChannelDto, page, size
        )

    async def get(self, id: int | str) -> AlertChannelDto:
        """Get a single alert channel by ID."""
        return parse_single(
            AlertChannelDto,
            await api_get(self._client, f"/api/v1/alert-channels/{path_param(id)}"),
            f"GET /api/v1/alert-channels/{id}",
        )

    async def create(
        self, body: RequestBody[CreateAlertChannelRequest]
    ) -> AlertChannelDto:
        """Create a new alert channel."""
        body = validate_request(CreateAlertChannelRequest, body, "alertChannels.create")
        return parse_single(
            AlertChannelDto,
            await api_post(self._client, "/api/v1/alert-channels", body),
            "POST /api/v1/alert-channels",
        )

    async def update(
        self, id: int | str, body: RequestBody[UpdateAlertChannelRequest]
    ) -> AlertChannelDto:
        """Update an alert channel."""
        body = validate_request(UpdateAlertChannelRequest, body, "alertChannels.update")
        return parse_single(
            AlertChannelDto,
            await api_put(
                self._client, f"/api/v1/alert-channels/{path_param(id)}", body
            ),
            f"PUT /api/v1/alert-channels/{id}",
        )

    async def delete(self, id: int | str) -> None:
        """Delete an alert channel."""
        await api_delete(self._client, f"/api/v1/alert-channels/{path_param(id)}")

    async def test(self, id: int | str) -> TestChannelResult:
        """Send a test notification to an alert channel."""
        return parse_single(
            TestChannelResult,
            await api_post(
                self._client, f"/api/v1/alert-channels/{path_param(id)}/test"
            ),
            f"POST /api/v1/alert-channels/{id}/test",
        )
