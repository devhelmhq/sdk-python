"""Inbound inbox and email helpers."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from devhelm import DevhelmApiError
from devhelm.resources.email import Email
from devhelm.resources.inboxes import Inboxes

INBOX_ID = "550e8400-e29b-41d4-a716-446655440000"
EVENT_ID = "550e8400-e29b-41d4-a716-446655440001"
WHEN = "2026-09-24T12:00:00Z"

EVENT = {
    "id": EVENT_ID,
    "inboxId": INBOX_ID,
    "receivedAt": WHEN,
    "sizeBytes": 2,
    "headers": {},
    "method": "POST",
    "path": "/",
    "sha256": "abc",
    "body": '{"ok":true}',
}

SIGNED = {
    "data": {
        "url": "https://files.example/event",
        "expiresAt": WHEN,
        "filename": "event.bin",
        "contentType": "application/json",
        "sizeBytes": 2,
    }
}


def _json(payload: object, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def test_inbox_wait_unwraps_event_and_downloads_signed_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path.endswith("/wait"):
            return _json({"event": EVENT})
        if request.url.path.endswith("/raw"):
            return _json(SIGNED)
        return _json({"message": str(request.url)}, status=404)

    downloaded: list[str] = []

    def fake_get(url: str, **_kwargs: Any) -> httpx.Response:
        downloaded.append(url)
        return httpx.Response(200, content=b"\x09\x09")

    monkeypatch.setattr(httpx, "get", fake_get)
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://api.test"
    )
    event = Inboxes(client).wait(INBOX_ID, timeout_ms=30_000, http={"method": "POST"})
    assert event.method == "POST"
    assert event.text() == '{"ok":true}'
    assert event.json() == {"ok": True}
    assert event.raw() == b"\x09\x09"
    assert downloaded == ["https://files.example/event"]

    body = json.loads(captured[0].content)
    assert body["timeoutMs"] == 30_000
    assert "receivedAfter" in body
    assert body["http"] == {"method": "POST"}
    assert all("files.example" not in str(request.url) for request in captured)


INBOX = {
    "id": INBOX_ID,
    "workspaceId": 2,
    "name": "stripe",
    "status": "active",
    "publicToken": "tok",
    "httpUrl": "https://api.test/api/v1/ingest/tok",
    "httpResponse": {
        "status": 200,
        "headers": {},
        "body": "",
        "contentType": "text/plain",
        "delayMs": 0,
    },
    "cors": True,
    "retentionDays": 3,
    "maxEvents": 10000,
    "createdAt": WHEN,
    "updatedAt": WHEN,
}

PAGE = {"hasNext": False, "hasPrev": False, "totalElements": 1, "totalPages": 1}


def test_inbox_search_event_filter_and_activity() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/activity"):
            return _json(
                {
                    "data": [
                        {
                            "inboxId": INBOX_ID,
                            "buckets": [{"hour": WHEN, "eventCount": 3}],
                        }
                    ]
                }
            )
        if request.url.path.endswith("/events"):
            return _json({"data": [EVENT], "nextCursor": None, "hasMore": False})
        return _json({"data": [INBOX], **PAGE})

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://api.test"
    )
    inboxes = Inboxes(client)
    assert inboxes.activity([]) == []
    assert seen == []

    rows = inboxes.list(search="stripe")
    assert rows[0].name == "stripe"
    assert seen[0].url.params["search"] == "stripe"

    rows[0].events.list(method="POST", path="/hooks")
    events = next(request for request in seen if request.url.path.endswith("/events"))
    assert events.url.params["method"] == "POST"
    assert events.url.params["path"] == "/hooks"

    activity = inboxes.activity([INBOX_ID])
    assert activity[0].buckets[0].event_count == 3
    act = next(request for request in seen if request.url.path.endswith("/activity"))
    assert act.url.params["inboxIds"] == INBOX_ID


def test_email_query_source_and_domain_activity() -> None:
    domain_id = "550e8400-e29b-41d4-a716-446655440002"
    message_id = "550e8400-e29b-41d4-a716-446655440003"
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/source"):
            return _json({"data": {"source": "Subject: code", "truncated": False}})
        if request.url.path.endswith("/activity"):
            return _json(
                {
                    "data": [
                        {
                            "domainId": domain_id,
                            "buckets": [{"hour": WHEN, "messageCount": 4}],
                        }
                    ]
                }
            )
        if "/messages" in request.url.path:
            return _json(
                {
                    "data": [
                        {
                            "id": message_id,
                            "domainId": domain_id,
                            "receivedAt": WHEN,
                            "sizeBytes": 4,
                            "headers": {},
                            "sha256": "abc",
                        }
                    ],
                    "nextCursor": None,
                    "hasMore": False,
                }
            )
        return _json(
            {
                "data": [
                    {
                        "id": domain_id,
                        "name": "ws.devhelmmail.com",
                        "workspaceId": 2,
                        "kind": "assigned",
                        "status": "active",
                        "mxVerified": True,
                        "retentionDays": 3,
                        "dnsRecords": [],
                        "createdAt": WHEN,
                        "updatedAt": WHEN,
                    }
                ],
                **PAGE,
            }
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://api.test"
    )
    email = Email(client)
    address = email.address(domain="ws.devhelmmail.com", label="signup")
    page = address.messages.list(q="code")
    listed = next(request for request in seen if "/messages" in request.url.path)
    assert listed.url.params["q"] == "code"
    assert listed.url.params["inbox"] == address.local_part
    text = page.data[0].source()
    assert text.source == "Subject: code"
    assert text.truncated is False

    domains = email.domains.list(search="ws")
    assert domains[0].name == "ws.devhelmmail.com"
    activity = email.domains.activity([domain_id])
    assert activity[0].buckets[0].message_count == 4


def test_email_wait_timeout_raises() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _json({"code": "WAIT_TIMEOUT", "message": "timed out"}, status=408)

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://api.test"
    )
    with pytest.raises(DevhelmApiError) as caught:
        Email(client).wait(to="a@b.devhelmmail.com", timeout_ms=1000)
    assert caught.value.status == 408
    assert caught.value.code == "WAIT_TIMEOUT"
