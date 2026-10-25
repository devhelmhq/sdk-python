from __future__ import annotations

from devhelm._async.transport import Client, api_get, as_transport
from devhelm._generated import DashboardOverviewDto
from devhelm._validation import parse_single


class Status:
    """Dashboard overview."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def overview(self) -> DashboardOverviewDto:
        """Get the dashboard overview."""
        return parse_single(
            DashboardOverviewDto,
            await api_get(self._client, "/api/v1/dashboard/overview"),
            "GET /api/v1/dashboard/overview",
        )
