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
    CreateNotificationPolicyRequest,
    NotificationPolicyDto,
    UpdateNotificationPolicyRequest,
)
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import RequestBody, parse_single, validate_request


class NotificationPolicies:
    """Routing rules for alerts."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> list[NotificationPolicyDto]:
        """List all notification policies (auto-paginates)."""
        return await fetch_all_pages(
            self._client, "/api/v1/notification-policies", NotificationPolicyDto
        )

    async def list_page(self, page: int, size: int) -> Page[NotificationPolicyDto]:
        """List notification policies with manual page control."""
        return await fetch_page(
            self._client,
            "/api/v1/notification-policies",
            NotificationPolicyDto,
            page,
            size,
        )

    async def get(self, id: int | str) -> NotificationPolicyDto:
        """Get a notification policy by ID."""
        return parse_single(
            NotificationPolicyDto,
            await api_get(
                self._client, f"/api/v1/notification-policies/{path_param(id)}"
            ),
            f"GET /api/v1/notification-policies/{id}",
        )

    async def create(
        self, body: RequestBody[CreateNotificationPolicyRequest]
    ) -> NotificationPolicyDto:
        """Create a notification policy."""
        body = validate_request(
            CreateNotificationPolicyRequest, body, "notificationPolicies.create"
        )
        return parse_single(
            NotificationPolicyDto,
            await api_post(self._client, "/api/v1/notification-policies", body),
            "POST /api/v1/notification-policies",
        )

    async def update(
        self, id: int | str, body: RequestBody[UpdateNotificationPolicyRequest]
    ) -> NotificationPolicyDto:
        """Update a notification policy."""
        body = validate_request(
            UpdateNotificationPolicyRequest, body, "notificationPolicies.update"
        )
        return parse_single(
            NotificationPolicyDto,
            await api_put(
                self._client, f"/api/v1/notification-policies/{path_param(id)}", body
            ),
            f"PUT /api/v1/notification-policies/{id}",
        )

    async def delete(self, id: int | str) -> None:
        """Delete a notification policy."""
        await api_delete(
            self._client, f"/api/v1/notification-policies/{path_param(id)}"
        )

    async def test(self, id: int | str) -> None:
        """Send a test dispatch to verify policy routing."""
        await api_post(
            self._client, f"/api/v1/notification-policies/{path_param(id)}/test"
        )
