"""Transport: retries, idempotency keys, client headers and credentials."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

import devhelm
from devhelm import AsyncDevhelm, Devhelm
from devhelm._async import transport as async_transport
from devhelm._async.transport import AsyncTransport
from devhelm._errors import (
    ConflictError,
    DevhelmTransportError,
    PlatformError,
    RateLimitError,
    ValidationError,
)
from devhelm._http import DevhelmConfig, _sdk_version, build_client, resolve_credentials
from devhelm._sync import transport as sync_transport
from devhelm._sync.transport import Transport, api_get, api_post
from devhelm._transport import NO_RETRY, RetryPolicy

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record sleeps instead of sleeping (sync and async transports)."""
    delays: list[float] = []

    def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    async def fake_async_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(sync_transport, "sleep", fake_sleep)
    monkeypatch.setattr(async_transport, "sleep", fake_async_sleep)
    return delays


def _sequence(responses: list[httpx.Response], seen: list[httpx.Request]) -> Handler:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return queue.pop(0) if len(queue) > 1 else queue[0]

    return handler


def _transport(handler: Handler, policy: RetryPolicy | None = None) -> Transport:
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://api.test"
    )
    return Transport(client, retry=policy)


def _err(status: int, category: str, *, retryable: bool = False) -> dict[str, object]:
    return {
        "status": status,
        "code": "X",
        "category": category,
        "retryable": retryable,
        "message": "m",
        "timestamp": 1,
    }


# ---------- retries ----------


def test_429_then_200_honours_retry_after(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(
        _sequence(
            [
                httpx.Response(
                    429, json=_err(429, "rate_limit"), headers={"Retry-After": "3"}
                ),
                httpx.Response(200, json={"ok": True}),
            ],
            seen,
        )
    )
    assert api_get(t, "/x") == {"ok": True}
    assert len(seen) == 2
    assert len(slept) == 1
    assert 3.0 <= slept[0] <= 4.0


def test_503_is_retried(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(
        _sequence(
            [
                httpx.Response(503, json=_err(503, "platform")),
                httpx.Response(200, json={"ok": True}),
            ],
            seen,
        )
    )
    assert api_get(t, "/x") == {"ok": True}
    assert len(seen) == 2
    assert len(slept) == 1


def test_retryable_409_is_retried(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(
        _sequence(
            [
                httpx.Response(409, json=_err(409, "conflict", retryable=True)),
                httpx.Response(200, json={"ok": True}),
            ],
            seen,
        )
    )
    assert api_post(t, "/x") == {"ok": True}
    assert len(seen) == 2


def test_non_retryable_409_is_not_retried(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(_sequence([httpx.Response(409, json=_err(409, "conflict"))], seen))
    with pytest.raises(ConflictError):
        api_post(t, "/x")
    assert len(seen) == 1
    assert slept == []


def test_gives_up_after_max_attempts(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(
        _sequence(
            [
                httpx.Response(
                    429, json=_err(429, "rate_limit"), headers={"Retry-After": "1"}
                )
            ],
            seen,
        )
    )
    with pytest.raises(RateLimitError) as exc:
        api_get(t, "/x")
    assert len(seen) == 5
    assert len(slept) == 4
    assert exc.value.retry_after == 1


def test_long_retry_after_is_not_slept_through(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(
        _sequence(
            [
                httpx.Response(
                    429, json=_err(429, "rate_limit"), headers={"Retry-After": "3600"}
                )
            ],
            seen,
        )
    )
    with pytest.raises(RateLimitError):
        api_get(t, "/x")
    assert len(seen) == 1
    assert slept == []


def test_bare_httpx_client_is_not_retried(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    client = httpx.Client(
        transport=httpx.MockTransport(
            _sequence([httpx.Response(503, json=_err(503, "platform"))], seen)
        ),
        base_url="http://api.test",
    )
    with pytest.raises(PlatformError):
        api_get(client, "/x")
    assert len(seen) == 1
    assert NO_RETRY.max_attempts == 1


def test_connect_error_is_retried_then_succeeds(slept: list[float]) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectError("refused", request=request)
        return httpx.Response(200, json={"ok": True})

    assert api_post(_transport(handler), "/x") == {"ok": True}
    assert len(calls) == 3
    assert len(slept) == 2


def test_connect_error_raises_transport_error_when_attempts_run_out(
    slept: list[float],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(DevhelmTransportError) as exc:
        api_get(_transport(handler, RetryPolicy(max_attempts=3)), "/x")
    assert isinstance(exc.value.__cause__, httpx.ConnectError)
    assert len(slept) == 2


# ---------- idempotency keys ----------


def test_post_reuses_one_key_across_retries(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    t = _transport(
        _sequence(
            [
                httpx.Response(503, json=_err(503, "platform")),
                httpx.Response(503, json=_err(503, "platform")),
                httpx.Response(200, json={"ok": True}),
            ],
            seen,
        )
    )
    api_post(t, "/x")
    keys = {r.headers["idempotency-key"] for r in seen}
    assert len(seen) == 3
    assert len(keys) == 1


def test_each_logical_post_gets_a_new_key() -> None:
    seen: list[httpx.Request] = []
    t = _transport(_sequence([httpx.Response(200, json={})], seen))
    api_post(t, "/x")
    api_post(t, "/x")
    assert seen[0].headers["idempotency-key"] != seen[1].headers["idempotency-key"]


def test_caller_key_is_kept() -> None:
    seen: list[httpx.Request] = []
    t = _transport(_sequence([httpx.Response(200, json={})], seen))
    api_post(t, "/x", headers={"Idempotency-Key": "mine"})
    assert seen[0].headers["idempotency-key"] == "mine"


def test_get_has_no_key() -> None:
    seen: list[httpx.Request] = []
    t = _transport(_sequence([httpx.Response(200, json={})], seen))
    api_get(t, "/x")
    assert "idempotency-key" not in seen[0].headers


# ---------- async transport ----------


def test_async_transport_retries_with_one_key(slept: list[float]) -> None:
    seen: list[httpx.Request] = []
    handler = _sequence(
        [
            httpx.Response(
                429, json=_err(429, "rate_limit"), headers={"Retry-After": "2"}
            ),
            httpx.Response(200, json={"ok": True}),
        ],
        seen,
    )

    async def go() -> object:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://api.test"
        ) as client:
            return await async_transport.api_post(AsyncTransport(client), "/x")

    assert asyncio.run(go()) == {"ok": True}
    assert len(seen) == 2
    assert seen[0].headers["idempotency-key"] == seen[1].headers["idempotency-key"]
    assert 2.0 <= slept[0] <= 3.0


def test_async_connect_error_raises_transport_error(slept: list[float]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    async def go() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://api.test"
        ) as client:
            await async_transport.api_get(
                AsyncTransport(client, retry=RetryPolicy(max_attempts=2)), "/x"
            )

    with pytest.raises(DevhelmTransportError):
        asyncio.run(go())
    assert len(slept) == 1


# ---------- client header and credentials ----------


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    for key in (
        "DEVHELM_API_TOKEN",
        "DEVHELM_API_URL",
        "DEVHELM_TELEMETRY",
        "DEVHELM_ORG_ID",
        "DEVHELM_WORKSPACE_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return tmp_path


def _write_context(home: Path, token: str, api_url: str) -> None:
    (home / ".devhelm").mkdir()
    (home / ".devhelm" / "contexts.json").write_text(
        json.dumps(
            {
                "version": 1,
                "current": "work",
                "contexts": {
                    "work": {"name": "work", "apiUrl": api_url, "token": token}
                },
            }
        )
    )


def test_client_header_defaults_to_sdk_python(clean_env: Path) -> None:
    client = build_client(DevhelmConfig(token="t"))
    assert client.headers["x-devhelm-client"] == f"sdk-python/{_sdk_version()}"
    client.close()


def test_client_header_for_wrapper_surface(clean_env: Path) -> None:
    client = build_client(
        DevhelmConfig(token="t", surface="mcp", surface_version="0.9.0")
    )
    assert client.headers["x-devhelm-client"] == "mcp/0.9.0"
    client.close()


def test_client_header_survives_telemetry_opt_out(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEVHELM_TELEMETRY", "0")
    client = build_client(DevhelmConfig(token="t"))
    assert "x-devhelm-surface" not in client.headers
    assert client.headers["x-devhelm-client"].startswith("sdk-python/")
    client.close()


def test_explicit_token_wins(clean_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEVHELM_API_TOKEN", "env")
    _write_context(clean_env, "ctx", "https://ctx.example")
    token, url = resolve_credentials(DevhelmConfig(token="explicit"))
    assert token == "explicit"
    assert url == "https://api.devhelm.io"


def test_env_token_beats_cli_context(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEVHELM_API_TOKEN", "env")
    _write_context(clean_env, "ctx", "https://ctx.example")
    token, url = resolve_credentials(DevhelmConfig(token=""))
    assert token == "env"
    assert url == "https://api.devhelm.io"


def test_cli_context_token_and_url(clean_env: Path) -> None:
    _write_context(clean_env, "ctx", "https://ctx.example/")
    token, url = resolve_credentials(DevhelmConfig(token=""))
    assert token == "ctx"
    assert url == "https://ctx.example"


def test_explicit_and_env_url_beat_context_url(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_context(clean_env, "ctx", "https://ctx.example")
    monkeypatch.setenv("DEVHELM_API_URL", "https://env.example")
    assert resolve_credentials(DevhelmConfig(token=""))[1] == "https://env.example"
    assert (
        resolve_credentials(DevhelmConfig(token="", base_url="https://opt.example"))[1]
        == "https://opt.example"
    )


def test_env_url_overrides_default(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEVHELM_API_URL", "https://env.example")
    assert resolve_credentials(DevhelmConfig(token="t"))[1] == "https://env.example"


def test_malformed_context_file_is_ignored(clean_env: Path) -> None:
    (clean_env / ".devhelm").mkdir()
    (clean_env / ".devhelm" / "contexts.json").write_text("{not json")
    with pytest.raises(ValidationError) as exc:
        resolve_credentials(DevhelmConfig(token=""))
    assert exc.value.code == "NO_TOKEN"


def test_missing_token_raises_no_token(clean_env: Path) -> None:
    with pytest.raises(ValidationError) as exc:
        Devhelm()
    assert exc.value.code == "NO_TOKEN"
    assert exc.value.status == 0
    assert exc.value.category == "validation"
    assert exc.value.next is not None
    assert isinstance(exc.value, devhelm.DevhelmApiError)


def _mock_like(base: httpx.Client, handler: Handler) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url=base.base_url,
        headers=base.headers,
    )


def test_devhelm_client_sends_headers(clean_env: Path) -> None:
    seen: list[httpx.Request] = []
    d = Devhelm(token="tok", org_id="7", workspace_id="9")
    d._transport.client = _mock_like(
        d._http, _sequence([httpx.Response(200, json={})], seen)
    )
    api_post(d._transport, "/api/v1/x")
    req = seen[0]
    assert req.headers["authorization"] == "Bearer tok"
    assert req.headers["x-phelm-org-id"] == "7"
    assert req.headers["x-phelm-workspace-id"] == "9"
    assert req.headers["x-devhelm-client"].startswith("sdk-python/")
    assert "idempotency-key" in req.headers
    # Every resource shares the one retrying transport.
    assert d.monitors._client is d._transport
    assert d.runs._client is d._transport
    assert d._transport.retry.max_attempts == 5
    d.close()


def test_async_devhelm_client_sends_headers(clean_env: Path) -> None:
    seen: list[httpx.Request] = []

    async def go() -> None:
        async with AsyncDevhelm(
            token="tok", surface="mcp", surface_version="1.0.0"
        ) as d:
            d._transport.client = httpx.AsyncClient(
                transport=httpx.MockTransport(
                    _sequence([httpx.Response(200, json={})], seen)
                ),
                base_url=d._http.base_url,
                headers=d._http.headers,
            )
            await async_transport.api_post(d._transport, "/api/v1/x")
            assert d.monitors._client is d._transport
            await d._transport.client.aclose()

    asyncio.run(go())
    assert seen[0].headers["authorization"] == "Bearer tok"
    assert seen[0].headers["x-devhelm-client"] == "mcp/1.0.0"
    assert "idempotency-key" in seen[0].headers


def test_max_attempts_option(clean_env: Path) -> None:
    d = Devhelm(token="t", max_attempts=1)
    assert d._transport.retry.max_attempts == 1
    d.close()
