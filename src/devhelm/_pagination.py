from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import httpx
from pydantic import BaseModel

from devhelm._http import DEFAULT_PAGE_SIZE, api_get
from devhelm._validation import parse_list

T = TypeVar("T")
M = TypeVar("M", bound=BaseModel)


@dataclass
class Page(Generic[T]):
    """A single page from an offset-paginated endpoint."""

    data: list[T] = field(default_factory=list)
    has_next: bool = False
    has_prev: bool = False
    total_elements: int | None = None
    total_pages: int | None = None


@dataclass
class CursorPage(Generic[T]):
    """A single page from a cursor-paginated endpoint."""

    data: list[T] = field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


def fetch_all_pages(
    client: httpx.Client,
    path: str,
    model_class: type[M],
    page_size: int = DEFAULT_PAGE_SIZE,
) -> list[M]:
    """Fetch all pages from an offset-paginated endpoint, validating each item."""
    all_items: list[M] = []
    page = 0

    while True:
        resp = api_get(client, path, params={"page": page, "size": page_size})
        raw_items = resp.get("data", []) if isinstance(resp, dict) else []
        items = parse_list(model_class, raw_items, f"GET {path}")
        all_items.extend(items)
        if not (isinstance(resp, dict) and resp.get("hasNext")):
            break
        page += 1

    return all_items


def fetch_page(
    client: httpx.Client, path: str, model_class: type[M], page: int, size: int
) -> Page[M]:
    """Fetch a single page from an offset-paginated endpoint with validation."""
    resp = api_get(client, path, params={"page": page, "size": size})
    raw_items = resp.get("data", []) if isinstance(resp, dict) else []
    items = parse_list(model_class, raw_items, f"GET {path}")
    return Page(
        data=items,
        has_next=bool(resp.get("hasNext")) if isinstance(resp, dict) else False,
        has_prev=bool(resp.get("hasPrev")) if isinstance(resp, dict) else False,
        total_elements=resp.get("totalElements") if isinstance(resp, dict) else None,
        total_pages=resp.get("totalPages") if isinstance(resp, dict) else None,
    )


def fetch_cursor_page(
    client: httpx.Client,
    path: str,
    model_class: type[M],
    cursor: str | None = None,
    limit: int | None = None,
) -> CursorPage[M]:
    """Fetch a single page from a cursor-paginated endpoint with validation."""
    params: dict[str, Any] = {}
    if cursor:
        params["cursor"] = cursor
    if limit:
        params["limit"] = limit

    resp = api_get(client, path, params=params or None)
    raw_items = resp.get("data", []) if isinstance(resp, dict) else []
    items = parse_list(model_class, raw_items, f"GET {path}")
    return CursorPage(
        data=items,
        next_cursor=(resp.get("nextCursor") if isinstance(resp, dict) else None),
        has_more=bool(resp.get("hasMore")) if isinstance(resp, dict) else False,
    )
