# Generated from src/devhelm/_async/resources/alert_channels.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from devhelm._generated import (
    AlertChannelDto,
    CreateAlertChannelRequest,
    TestChannelResult,
    UpdateAlertChannelRequest,
)
from devhelm._pages import Page
from devhelm._sync.pagination import fetch_all_pages, fetch_page
from devhelm._sync.transport import (
    Client,
    api_delete,
    api_get,
    api_post,
    api_put,
    as_transport,
)
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class AlertChannels:
    """Slack, email, webhook, and other alert channels."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

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

    def create(self, body: RequestBody[CreateAlertChannelRequest]) -> AlertChannelDto:
        """Create a new alert channel."""
        body = validate_request(CreateAlertChannelRequest, body, "alertChannels.create")
        return parse_single(
            AlertChannelDto,
            api_post(self._client, "/api/v1/alert-channels", body),
            "POST /api/v1/alert-channels",
        )

    def update(
        self, id: int | str, body: RequestBody[UpdateAlertChannelRequest]
    ) -> AlertChannelDto:
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
