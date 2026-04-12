from __future__ import annotations

from typing import Any

import httpx

from devhelm._http import api_get, unwrap_single


class Status:
    """Dashboard overview."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def overview(self) -> Any:
        """Get the dashboard overview."""
        return unwrap_single(api_get(self._client, "/api/v1/dashboard/overview"))
