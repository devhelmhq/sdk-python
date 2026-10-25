# Generated from src/devhelm/_async/pagination.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Page fetchers for offset (``TableValueResult``) and cursor (``CursorPage``)
endpoints, plus the auto-paginating ``fetch_all_*`` helpers."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from devhelm._pages import CursorPage, Page, _validate_cursor_page, _validate_page
from devhelm._sync.transport import Client, api_get
from devhelm._transport import QueryParams, QueryValue
from devhelm._validation import parse_list

M = TypeVar("M", bound=BaseModel)

DEFAULT_PAGE_SIZE = 200
DEFAULT_CURSOR_LIMIT = 100


def fetch_all_pages(
    client: Client,
    path: str,
    model_class: type[M],
    page_size: int = DEFAULT_PAGE_SIZE,
    *,
    extra_params: QueryParams | None = None,
) -> list[M]:
    """Fetch every page from an offset-paginated endpoint.

    ``extra_params`` (server-side filters) apply to every page. ``page`` and
    ``size`` always win over them.
    """
    all_items: list[M] = []
    page = 0
    base: dict[str, QueryValue] = dict(extra_params or {})
    while True:
        resp = api_get(client, path, {**base, "page": page, "size": page_size})
        envelope = _validate_page(resp)
        all_items.extend(parse_list(model_class, envelope.data, f"GET {path}"))
        if not envelope.hasNext:
            break
        page += 1
    return all_items


def fetch_page(
    client: Client,
    path: str,
    model_class: type[M],
    page: int,
    size: int,
    *,
    extra_params: QueryParams | None = None,
) -> Page[M]:
    """Fetch one page from an offset-paginated endpoint."""
    base: dict[str, QueryValue] = dict(extra_params or {})
    return fetch_table(
        client, path, model_class, params={**base, "page": page, "size": size}
    )


def fetch_table(
    client: Client,
    path: str,
    model_class: type[M],
    *,
    params: QueryParams | None = None,
) -> Page[M]:
    """Fetch a ``TableValueResult`` endpoint without forcing page/size."""
    envelope = _validate_page(api_get(client, path, params))
    return Page(
        data=parse_list(model_class, envelope.data, f"GET {path}"),
        has_next=envelope.hasNext,
        has_prev=envelope.hasPrev,
        total_elements=envelope.totalElements,
        total_pages=envelope.totalPages,
        next_cursor=envelope.nextCursor,
    )


def fetch_cursor_page(
    client: Client,
    path: str,
    model_class: type[M],
    cursor: str | None = None,
    limit: int | None = None,
    *,
    extra_params: QueryParams | None = None,
) -> CursorPage[M]:
    """Fetch one page from a cursor-paginated endpoint.

    ``cursor`` and ``limit`` always win over ``extra_params``.
    """
    params: dict[str, QueryValue] = dict(extra_params or {})
    if cursor:
        params["cursor"] = cursor
    if limit:
        params["limit"] = limit
    resp = api_get(client, path, params or None)
    envelope = _validate_cursor_page(resp)
    return CursorPage(
        data=parse_list(model_class, envelope.data, f"GET {path}"),
        next_cursor=envelope.nextCursor,
        has_more=envelope.hasMore,
    )


def fetch_all_cursor_pages(
    client: Client,
    path: str,
    model_class: type[M],
    *,
    limit: int = DEFAULT_CURSOR_LIMIT,
    extra_params: QueryParams | None = None,
) -> list[M]:
    """Walk ``hasMore`` / ``nextCursor`` to the end and return every item."""
    items: list[M] = []
    cursor: str | None = None
    while True:
        page = fetch_cursor_page(
            client, path, model_class, cursor, limit, extra_params=extra_params
        )
        items.extend(page.data)
        if not page.has_more or not page.next_cursor:
            return items
        cursor = page.next_cursor
