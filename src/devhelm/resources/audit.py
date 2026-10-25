# Generated from src/devhelm/_async/resources/audit.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""The workspace audit log."""

from __future__ import annotations

from datetime import datetime

from devhelm._generated import AuditEventDto
from devhelm._pages import Page
from devhelm._sync.pagination import fetch_page
from devhelm._sync.transport import Client, as_transport
from devhelm._transport import QueryValue


class Audit:
    """Who did what, newest first (``GET /api/v1/audit-log``)."""

    def __init__(self, client: Client) -> None:
        self._client = as_transport(client)

    def list(
        self,
        *,
        action: str | None = None,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        from_: datetime | None = None,
        to: datetime | None = None,
        page: int = 0,
        size: int = 50,
    ) -> Page[AuditEventDto]:
        """One page of audit events, filtered by action, actor or resource."""
        params: dict[str, QueryValue] = {
            "action": action,
            "actorId": actor_id,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "from": from_.isoformat() if from_ else None,
            "to": to.isoformat() if to else None,
        }
        return fetch_page(
            self._client,
            "/api/v1/audit-log",
            AuditEventDto,
            page,
            size,
            extra_params=params,
        )
