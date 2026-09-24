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
