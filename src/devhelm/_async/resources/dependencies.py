from __future__ import annotations

from devhelm._async.pagination import fetch_all_pages, fetch_page
from devhelm._async.transport import (
    Client,
    api_delete,
    api_get,
    api_patch,
    api_post,
    as_transport,
)
from devhelm._generated import (
    ServiceSubscribeRequest,
    ServiceSubscriptionDto,
    UpdateAlertSensitivityRequest,
)
from devhelm._pages import Page
from devhelm._transport import path_param
from devhelm._validation import parse_single, validate_request


class Dependencies:
    """Service dependency tracking (service subscriptions)."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def list(self) -> list[ServiceSubscriptionDto]:
        """List all tracked service dependencies."""
        return await fetch_all_pages(
            self._client, "/api/v1/service-subscriptions", ServiceSubscriptionDto
        )

    async def list_page(self, page: int, size: int) -> Page[ServiceSubscriptionDto]:
        """List tracked dependencies with manual page control."""
        return await fetch_page(
            self._client,
            "/api/v1/service-subscriptions",
            ServiceSubscriptionDto,
            page,
            size,
        )

    async def get(self, id: int | str) -> ServiceSubscriptionDto:
        """Get a tracked dependency by ID."""
        return parse_single(
            ServiceSubscriptionDto,
            await api_get(
                self._client, f"/api/v1/service-subscriptions/{path_param(id)}"
            ),
            f"GET /api/v1/service-subscriptions/{id}",
        )

    async def track(
        self,
        slug: str,
        *,
        component_id: str | None = None,
        alert_sensitivity: str | None = None,
    ) -> ServiceSubscriptionDto:
        """Track a new service dependency by slug.

        ``component_id`` subscribes to one component instead of the whole
        service. ``alert_sensitivity`` is one of ``ALL``,
        ``INCIDENTS_ONLY``, ``MAJOR_ONLY``, or ``AWARENESS`` (the API
        default — silent tracking with no alert fan-out). The request body
        is omitted entirely when neither kwarg is provided.
        """
        body: ServiceSubscribeRequest | None = None
        if component_id is not None or alert_sensitivity is not None:
            fields: dict[str, str] = {}
            if component_id is not None:
                fields["componentId"] = component_id
            if alert_sensitivity is not None:
                fields["alertSensitivity"] = alert_sensitivity
            body = validate_request(
                ServiceSubscribeRequest, fields, "dependencies.track"
            )
        return parse_single(
            ServiceSubscriptionDto,
            await api_post(
                self._client, f"/api/v1/service-subscriptions/{path_param(slug)}", body
            ),
            f"POST /api/v1/service-subscriptions/{slug}",
        )

    async def update_alert_sensitivity(
        self, subscription_id: int | str, alert_sensitivity: str
    ) -> ServiceSubscriptionDto:
        """Update the alert sensitivity on a tracked dependency.

        ``alert_sensitivity`` is one of ``ALL``, ``INCIDENTS_ONLY``,
        ``MAJOR_ONLY``, or ``AWARENESS``.
        """
        body = validate_request(
            UpdateAlertSensitivityRequest,
            {"alertSensitivity": alert_sensitivity},
            "dependencies.update_alert_sensitivity",
        )
        path = f"/api/v1/service-subscriptions/{path_param(subscription_id)}"
        return parse_single(
            ServiceSubscriptionDto,
            await api_patch(self._client, f"{path}/alert-sensitivity", body),
            f"PATCH /api/v1/service-subscriptions/{subscription_id}/alert-sensitivity",
        )

    async def delete(self, id: int | str) -> None:
        """Remove a tracked dependency."""
        await api_delete(
            self._client, f"/api/v1/service-subscriptions/{path_param(id)}"
        )
