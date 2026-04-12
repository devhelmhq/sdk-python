from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import httpx

from devhelm._http import DEFAULT_PAGE_SIZE, api_get

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """A single page from an offset-paginated endpoint."""

    data: list[T] = field(default_factory=list)
    has_next: bool = False
    has_prev: bool = False


@dataclass
class CursorPage(Generic[T]):
    """A single page from a cursor-paginated endpoint."""

    data: list[T] = field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


def fetch_all_pages(
    client: httpx.Client, path: str, page_size: int = DEFAULT_PAGE_SIZE
) -> list[Any]:
    """Fetch all pages from an offset-paginated (Spring Pageable) endpoint."""
    all_items: list[Any] = []
    page = 0

    while True:
        resp = api_get(client, path, params={"page": page, "size": page_size})
        items = resp.get("data", []) if isinstance(resp, dict) else []
        all_items.extend(items)
        if not (isinstance(resp, dict) and resp.get("hasNext")):
            break
        page += 1

    return all_items


def fetch_page(client: httpx.Client, path: str, page: int, size: int) -> Page[Any]:
    """Fetch a single page from an offset-paginated endpoint."""
    resp = api_get(client, path, params={"page": page, "size": size})
    return Page(
        data=resp.get("data", []) if isinstance(resp, dict) else [],
        has_next=bool(resp.get("hasNext")) if isinstance(resp, dict) else False,
        has_prev=bool(resp.get("hasPrev")) if isinstance(resp, dict) else False,
    )


def fetch_cursor_page(
    client: httpx.Client, path: str, cursor: str | None = None, limit: int | None = None
) -> CursorPage[Any]:
    """Fetch a single page from a cursor-paginated endpoint."""
    params: dict[str, Any] = {}
    if cursor:
        params["cursor"] = cursor
    if limit:
        params["limit"] = limit

    resp = api_get(client, path, params=params or None)
    return CursorPage(
        data=resp.get("data", []) if isinstance(resp, dict) else [],
        next_cursor=(resp.get("nextCursor") if isinstance(resp, dict) else None),
        has_more=bool(resp.get("hasMore")) if isinstance(resp, dict) else False,
    )
