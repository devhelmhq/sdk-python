"""Download helpers for short-lived signed object URLs."""

from __future__ import annotations

from pathlib import Path

import httpx

from devhelm._errors import DevhelmTransportError
from devhelm._generated import SignedDownload
from devhelm._http import api_get
from devhelm._validation import parse_single

WAIT_SLACK_SECONDS = 10.0
DEFAULT_WAIT_MS = 30_000


def wait_timeout_seconds(timeout_ms: int) -> float:
    """HTTP deadline for a wait call: the server budget plus slack."""
    return timeout_ms / 1000 + WAIT_SLACK_SECONDS


def fetch_signed(client: httpx.Client, path: str) -> tuple[SignedDownload, bytes]:
    """GET a signed-download envelope, then fetch the URL with no API token."""
    signed = parse_single(SignedDownload, api_get(client, path), f"GET {path}")
    return signed, read_signed_url(signed.url)


def read_signed_url(url: str) -> bytes:
    try:
        response = httpx.get(url, timeout=60.0, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise DevhelmTransportError(f"{type(exc).__name__}: {exc}", cause=exc) from exc
    if response.is_error:
        raise DevhelmTransportError(
            f"Download failed with status {response.status_code}"
        )
    return response.content


def write_download(data: bytes, filename: str, path: str | Path) -> Path:
    """Write bytes to ``path``, or to ``path / filename`` when path is a directory."""
    target = Path(path)
    if (target.exists() and target.is_dir()) or (
        not target.exists() and target.suffix == ""
    ):
        target = target / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target
