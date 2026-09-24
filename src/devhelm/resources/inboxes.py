"""Inbound HTTP capture inboxes.

``client.webhooks`` stays outbound alert delivery. ``client.inboxes`` is the
capture URL a sender hits, plus ``wait`` for the captured request.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import httpx

from devhelm._generated import (
    CreateWebhookInboxRequest,
    InboundWebhookHttpResponse,
    UpdateWebhookInboxRequest,
    WaitHttpMatchers,
    WaitWebhookEventRequest,
    WebhookEventDto,
    WebhookInboxDto,
)
from devhelm._http import api_delete, api_get, api_patch, api_post, path_param
from devhelm._pagination import (
    CursorPage,
    Page,
    fetch_all_pages,
    fetch_cursor_page,
    fetch_page,
)
from devhelm._validation import (
    RequestBody,
    parse_keyed_envelope,
    parse_single,
    validate_request,
)
from devhelm.resources.signed_download import (
    DEFAULT_WAIT_MS,
    fetch_signed,
    wait_timeout_seconds,
    write_download,
)

BASE = "/api/v1/webhook/inboxes"


class InboxEvents:
    """Events stored on one inbox."""

    def __init__(self, inboxes: Inboxes, inbox_id: str) -> None:
        self._inboxes = inboxes
        self._inbox_id = inbox_id

    def list(
        self, *, cursor: str | None = None, limit: int | None = None
    ) -> CursorPage[Event]:
        page = fetch_cursor_page(
            self._inboxes._client,
            f"{BASE}/{path_param(self._inbox_id)}/events",
            WebhookEventDto,
            cursor,
            limit,
        )
        return CursorPage(
            data=[self._inboxes._bind_event(self._inbox_id, row) for row in page.data],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )

    def get(self, event_id: str) -> Event:
        path = f"{BASE}/{path_param(self._inbox_id)}/events/{path_param(event_id)}"
        row = parse_single(
            WebhookEventDto, api_get(self._inboxes._client, path), f"GET {path}"
        )
        return self._inboxes._bind_event(self._inbox_id, row)

    def delete(self, event_id: str) -> None:
        api_delete(
            self._inboxes._client,
            f"{BASE}/{path_param(self._inbox_id)}/events/{path_param(event_id)}",
        )

    def clear(self) -> None:
        api_delete(self._inboxes._client, f"{BASE}/{path_param(self._inbox_id)}/events")


class Event:
    """One captured HTTP request."""

    def __init__(self, inboxes: Inboxes, inbox_id: str, dto: WebhookEventDto) -> None:
        self._inboxes = inboxes
        self._inbox_id = inbox_id
        self.id = dto.id
        self.inbox_id = dto.inbox_id
        self.received_at = dto.received_at
        self.size_bytes = dto.size_bytes
        self.source_ip = dto.source_ip
        self.headers = dto.headers
        self.method = dto.method
        self.path = dto.path
        self.query = dto.query
        self.url = dto.url
        self.host = dto.host
        self.body_preview = dto.body_preview
        self.sha256 = dto.sha256

    def raw(self) -> bytes:
        """Download the captured request body."""
        _signed, data = fetch_signed(self._inboxes._client, self._raw_path())
        return data

    def save(self, path: str | Path) -> Path:
        """Write the captured body. A directory path uses the signed filename."""
        signed, data = fetch_signed(self._inboxes._client, self._raw_path())
        return write_download(data, signed.filename, path)

    def delete(self) -> None:
        api_delete(
            self._inboxes._client,
            f"{BASE}/{path_param(self._inbox_id)}/events/{path_param(str(self.id))}",
        )

    def _raw_path(self) -> str:
        return (
            f"{BASE}/{path_param(self._inbox_id)}/events/{path_param(str(self.id))}/raw"
        )


class Inbox:
    """A capture URL and the calls that use it."""

    def __init__(self, inboxes: Inboxes, dto: WebhookInboxDto) -> None:
        self._inboxes = inboxes
        self.id: UUID = dto.id
        self.workspace_id = dto.workspace_id
        self.name = dto.name
        self.status = dto.status
        self.public_token = dto.public_token
        self.http_url = dto.http_url
        self.http_response: InboundWebhookHttpResponse = dto.http_response
        self.cors = dto.cors
        self.retention_days = dto.retention_days
        self.max_events = dto.max_events
        self.created_at = dto.created_at
        self.updated_at = dto.updated_at
        self.events = InboxEvents(inboxes, str(dto.id))

    def wait(
        self,
        *,
        timeout_ms: int = DEFAULT_WAIT_MS,
        received_after: datetime | None = None,
        http: RequestBody[WaitHttpMatchers] | None = None,
    ) -> Event:
        return self._inboxes.wait(
            str(self.id),
            timeout_ms=timeout_ms,
            received_after=received_after,
            http=http,
        )

    def update(self, body: RequestBody[UpdateWebhookInboxRequest]) -> Inbox:
        return self._inboxes.update(str(self.id), body)

    def delete(self) -> None:
        self._inboxes.delete(str(self.id))


class Inboxes:
    """Create capture URLs and wait for the requests sent to them."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def list(self) -> list[Inbox]:
        rows = fetch_all_pages(self._client, BASE, WebhookInboxDto)
        return [self._bind(row) for row in rows]

    def list_page(self, page: int, size: int) -> Page[Inbox]:
        result = fetch_page(self._client, BASE, WebhookInboxDto, page, size)
        return Page(
            data=[self._bind(row) for row in result.data],
            has_next=result.has_next,
            has_prev=result.has_prev,
            total_elements=result.total_elements,
            total_pages=result.total_pages,
            next_cursor=result.next_cursor,
        )

    def get(self, id: str) -> Inbox:
        path = f"{BASE}/{path_param(id)}"
        return self._bind(
            parse_single(WebhookInboxDto, api_get(self._client, path), f"GET {path}")
        )

    def create(
        self,
        *,
        name: str,
        status: str | None = None,
        http_response: object | None = None,
        cors: bool | None = None,
        retention_days: int | None = None,
        max_events: int | None = None,
    ) -> Inbox:
        raw: dict[str, object] = {"name": name}
        if status is not None:
            raw["status"] = status
        if http_response is not None:
            raw["httpResponse"] = http_response
        if cors is not None:
            raw["cors"] = cors
        if retention_days is not None:
            raw["retentionDays"] = retention_days
        if max_events is not None:
            raw["maxEvents"] = max_events
        body = validate_request(CreateWebhookInboxRequest, raw, "inboxes.create")
        return self._bind(
            parse_single(
                WebhookInboxDto, api_post(self._client, BASE, body), f"POST {BASE}"
            )
        )

    def update(self, id: str, body: RequestBody[UpdateWebhookInboxRequest]) -> Inbox:
        payload = validate_request(UpdateWebhookInboxRequest, body, "inboxes.update")
        path = f"{BASE}/{path_param(id)}"
        return self._bind(
            parse_single(
                WebhookInboxDto, api_patch(self._client, path, payload), f"PATCH {path}"
            )
        )

    def delete(self, id: str) -> None:
        api_delete(self._client, f"{BASE}/{path_param(id)}")

    def wait(
        self,
        id: str,
        *,
        timeout_ms: int = DEFAULT_WAIT_MS,
        received_after: datetime | None = None,
        http: RequestBody[WaitHttpMatchers] | None = None,
    ) -> Event:
        matchers = (
            None
            if http is None
            else validate_request(WaitHttpMatchers, http, "inboxes.wait")
        )
        fields: dict[str, object] = {
            "timeoutMs": timeout_ms,
            "receivedAfter": received_after or datetime.now(timezone.utc),
        }
        if matchers is not None:
            fields["http"] = matchers
        body = validate_request(WaitWebhookEventRequest, fields, "inboxes.wait")
        path = f"{BASE}/{path_param(id)}/wait"
        raw = api_post(
            self._client, path, body, timeout=wait_timeout_seconds(timeout_ms)
        )
        return self._bind_event(
            id, parse_keyed_envelope(WebhookEventDto, raw, "event", f"POST {path}")
        )

    def _bind(self, dto: WebhookInboxDto) -> Inbox:
        return Inbox(self, dto)

    def _bind_event(self, inbox_id: str, dto: WebhookEventDto) -> Event:
        return Event(self, inbox_id, dto)
