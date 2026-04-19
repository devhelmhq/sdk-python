from __future__ import annotations

import httpx

from devhelm._generated import (
    CreateNotificationPolicyRequest,
    NotificationPolicyDto,
    UpdateNotificationPolicyRequest,
)
from devhelm._http import api_delete, api_get, api_post, api_put, path_param
from devhelm._pagination import Page, fetch_all_pages, fetch_page
from devhelm._validation import parse_single, validate_request


class NotificationPolicies:
    """Routing rules for alerts."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

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

    def create(self, body: CreateNotificationPolicyRequest) -> NotificationPolicyDto:
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
        self, id: int | str, body: UpdateNotificationPolicyRequest
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
