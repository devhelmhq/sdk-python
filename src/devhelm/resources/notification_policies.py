# Generated from src/devhelm/_async/resources/notification_policies.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from devhelm._generated import (
    CreateNotificationPolicyRequest,
    NotificationPolicyDto,
    UpdateNotificationPolicyRequest,
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


class NotificationPolicies:
    """Routing rules for alerts."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def list(self) -> list[NotificationPolicyDto]:
        """List all notification policies (auto-paginates)."""
        return fetch_all_pages(
            self._client, "/api/v1/notification-policies", NotificationPolicyDto
        )

    def list_page(self, page: int, size: int) -> Page[NotificationPolicyDto]:
        """List notification policies with manual page control."""
        return fetch_page(
            self._client,
            "/api/v1/notification-policies",
            NotificationPolicyDto,
            page,
            size,
        )

    def get(self, id: int | str) -> NotificationPolicyDto:
        """Get a notification policy by ID."""
        return parse_single(
            NotificationPolicyDto,
            api_get(self._client, f"/api/v1/notification-policies/{path_param(id)}"),
            f"GET /api/v1/notification-policies/{id}",
        )

    def create(
        self, body: RequestBody[CreateNotificationPolicyRequest]
    ) -> NotificationPolicyDto:
        """Create a notification policy."""
        body = validate_request(
            CreateNotificationPolicyRequest, body, "notificationPolicies.create"
        )
        return parse_single(
            NotificationPolicyDto,
            api_post(self._client, "/api/v1/notification-policies", body),
            "POST /api/v1/notification-policies",
        )

    def update(
        self, id: int | str, body: RequestBody[UpdateNotificationPolicyRequest]
    ) -> NotificationPolicyDto:
        """Update a notification policy."""
        body = validate_request(
            UpdateNotificationPolicyRequest, body, "notificationPolicies.update"
        )
        return parse_single(
            NotificationPolicyDto,
            api_put(
                self._client, f"/api/v1/notification-policies/{path_param(id)}", body
            ),
            f"PUT /api/v1/notification-policies/{id}",
        )

    def delete(self, id: int | str) -> None:
        """Delete a notification policy."""
        api_delete(self._client, f"/api/v1/notification-policies/{path_param(id)}")

    def test(self, id: int | str) -> None:
        """Send a test dispatch to verify policy routing."""
        api_post(self._client, f"/api/v1/notification-policies/{path_param(id)}/test")
