# Generated from src/devhelm/_async/resources/status.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
from __future__ import annotations

from devhelm._generated import DashboardOverviewDto
from devhelm._sync.transport import Client, api_get, as_transport
from devhelm._validation import parse_single


class Status:
    """Dashboard overview."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def overview(self) -> DashboardOverviewDto:
        """Get the dashboard overview."""
        return parse_single(
            DashboardOverviewDto,
            api_get(self._client, "/api/v1/dashboard/overview"),
            "GET /api/v1/dashboard/overview",
        )
