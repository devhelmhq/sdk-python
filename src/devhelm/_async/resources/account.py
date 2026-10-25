"""Plan, entitlements and synthetics usage for the current organization."""

from __future__ import annotations

from devhelm._async.transport import Client, api_get, as_transport
from devhelm._generated import EntitlementResponse, SyntheticsUsagePeriodDto
from devhelm._validation import parse_single


class Account:
    """Read-only plan facts: what the plan includes and what is used."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    async def usage(self) -> SyntheticsUsagePeriodDto:
        """Synthetics runs used this period, per meter and per monitor."""
        path = "/api/v1/synthetics/usage"
        return parse_single(
            SyntheticsUsagePeriodDto, await api_get(self._client, path), f"GET {path}"
        )

    async def entitlements(self) -> EntitlementResponse:
        """The plan tier, its entitlements and current usage."""
        path = "/api/v1/entitlements"
        return parse_single(
            EntitlementResponse, await api_get(self._client, path), f"GET {path}"
        )
