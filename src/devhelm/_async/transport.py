"""Async HTTP transport and the request helpers every resource uses.

The transport owns one ``httpx.AsyncClient`` (auth and tenant headers are set
on it) and adds what every call needs: an ``Idempotency-Key`` per logical
POST, bounded retries per ``devhelm._transport``, and typed errors.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

import httpx
from pydantic import BaseModel

from devhelm._async._compat import sleep
from devhelm._errors import DevhelmTransportError
from devhelm._transport import (
    NO_RETRY,
    JsonResponse,
    QueryParams,
    RetryPolicy,
    can_retry,
    checked_json,
    clean_params,
    raise_for_error,
    request_headers,
    retry_delay,
    serialize_body,
    transport_retry_delay,
)


class AsyncTransport:
    """Sends requests with idempotency keys, retries and typed errors."""

    def __init__(
        self, client: httpx.AsyncClient, *, retry: RetryPolicy | None = None
    ) -> None:
        self.client = client
        self.retry = retry or RetryPolicy()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        json: object = None,
        content: bytes | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Send one logical request and return the final response.

        Non-2xx responses are returned, not raised, so callers that need the
        status (``POST /monitors/{id}/test`` answers 200 or 202) can read it.
        Use :func:`api_get` and friends for the raise-on-error path.
        """
        hdrs = request_headers(method, headers)
        retryable = can_retry(method, hdrs)
        query = clean_params(params)
        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self.client.request(
                    method,
                    path,
                    params=query,
                    json=json,
                    content=content,
                    headers=hdrs,
                    timeout=httpx.USE_CLIENT_DEFAULT if timeout is None else timeout,
                )
            except httpx.TransportError as exc:
                delay = (
                    transport_retry_delay(self.retry, attempt) if retryable else None
                )
                if delay is None:
                    raise DevhelmTransportError(
                        f"{type(exc).__name__}: {exc}", cause=exc
                    ) from exc
                await sleep(delay)
                continue
            except httpx.HTTPError as exc:
                raise DevhelmTransportError(
                    f"{type(exc).__name__}: {exc}", cause=exc
                ) from exc
            delay = retry_delay(self.retry, response, attempt) if retryable else None
            if delay is None:
                return response
            await sleep(delay)

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: httpx.Timeout | float | None = None,
    ) -> AsyncIterator[httpx.Response]:
        """Open a streaming response (used for server-sent events).

        Raises the typed error when the server refuses the stream. Streams are
        not retried: the caller falls back to polling instead.
        """
        try:
            async with self.client.stream(
                method,
                path,
                params=clean_params(params),
                headers=dict(headers or {}),
                timeout=httpx.USE_CLIENT_DEFAULT if timeout is None else timeout,
            ) as response:
                if not response.is_success:
                    await response.aread()
                    raise_for_error(response)
                yield response
        except httpx.HTTPError as exc:
            raise DevhelmTransportError(
                f"{type(exc).__name__}: {exc}", cause=exc
            ) from exc


Client = AsyncTransport | httpx.AsyncClient


def as_transport(client: Client) -> AsyncTransport:
    """Wrap a bare ``httpx.AsyncClient`` (no retries) or pass a transport through."""
    if isinstance(client, AsyncTransport):
        return client
    return AsyncTransport(client, retry=NO_RETRY)


Body = BaseModel | Mapping[str, object] | None


async def api_get(
    client: Client, path: str, params: QueryParams | None = None
) -> JsonResponse:
    response = await as_transport(client).request("GET", path, params=params)
    return checked_json(response)


async def api_post(
    client: Client,
    path: str,
    body: Body = None,
    *,
    params: QueryParams | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> JsonResponse:
    response = await as_transport(client).request(
        "POST",
        path,
        params=params,
        json=serialize_body(body),
        headers=headers,
        timeout=timeout,
    )
    return checked_json(response)


async def api_post_with_status(
    client: Client,
    path: str,
    body: Body = None,
    *,
    headers: Mapping[str, str] | None = None,
) -> tuple[int, JsonResponse]:
    """POST that also returns the success status, for endpoints whose body
    depends on it (200 probe result vs 202 queued run)."""
    response = await as_transport(client).request(
        "POST", path, json=serialize_body(body), headers=headers
    )
    return response.status_code, checked_json(response)


async def api_post_bytes(
    client: Client,
    path: str,
    content: bytes,
    content_type: str,
    *,
    params: QueryParams | None = None,
) -> JsonResponse:
    response = await as_transport(client).request(
        "POST",
        path,
        params=params,
        content=content,
        headers={"Content-Type": content_type},
    )
    return checked_json(response)


async def api_put(client: Client, path: str, body: Body) -> JsonResponse:
    response = await as_transport(client).request(
        "PUT", path, json=serialize_body(body)
    )
    return checked_json(response)


async def api_patch(client: Client, path: str, body: Body) -> JsonResponse:
    response = await as_transport(client).request(
        "PATCH", path, json=serialize_body(body)
    )
    return checked_json(response)


async def api_delete(
    client: Client, path: str, params: QueryParams | None = None
) -> JsonResponse:
    response = await as_transport(client).request("DELETE", path, params=params)
    return checked_json(response)


async def api_get_raw(
    client: Client,
    path: str,
    params: QueryParams | None = None,
    *,
    accept: str | None = None,
) -> httpx.Response:
    """GET a non-JSON body (zip, CSV, plain text). Raises on non-2xx."""
    headers = {"Accept": accept} if accept else None
    response = await as_transport(client).request(
        "GET", path, params=params, headers=headers
    )
    raise_for_error(response)
    return response
