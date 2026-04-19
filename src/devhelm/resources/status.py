from __future__ import annotations

import httpx

from devhelm._generated import DashboardOverviewDto
from devhelm._http import api_get
from devhelm._validation import parse_single


class Status:
    """Dashboard overview."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def overview(self) -> DashboardOverviewDto:
        """Get the dashboard overview."""
        return parse_single(
            DashboardOverviewDto,
            api_get(self._client, "/api/v1/dashboard/overview"),
            "GET /api/v1/dashboard/overview",
        )
