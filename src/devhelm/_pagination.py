from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from devhelm._errors import DevhelmValidationError
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


class _PageEnvelope(BaseModel):
    """Server-side page metadata as a typed model.

    Items are validated separately via ``parse_list(model_class, ...)`` so the
    envelope only describes the surrounding pagination shape; that keeps this
    layer P5-clean (no casts) without forcing every model to be expressed
    twice. ``extra="forbid"`` so unknown envelope keys surface as a typed
    ``DevhelmValidationError`` (P1) rather than silently disappearing.
    """

    model_config = ConfigDict(extra="forbid")

    data: list[Any] = []  # validated separately
    hasNext: bool = False
    hasPrev: bool = False
    totalElements: int | None = None
    totalPages: int | None = None


class _CursorPageEnvelope(BaseModel):
    """Cursor-page envelope. See ``_PageEnvelope`` for the rationale."""

    model_config = ConfigDict(extra="forbid")

    data: list[Any] = []
    nextCursor: str | None = None
    hasMore: bool = False


def _validate_page(resp: object) -> _PageEnvelope:
    try:
        return _PageEnvelope.model_validate(resp)
    except ValidationError as e:
        # Surface the structured Pydantic errors so callers can introspect
        # the failed location instead of getting a string-summarised
        # `value_error`. Non-`ValidationError` exceptions (network, IO,
        # programmer mistake) intentionally propagate — wrapping them here
        # would mask real bugs as fake "validation" failures.
        raise DevhelmValidationError(
            "Invalid paginated response envelope",
            errors=e.errors(),
            cause=e,
        ) from e


def _validate_cursor_page(resp: object) -> _CursorPageEnvelope:
    try:
        return _CursorPageEnvelope.model_validate(resp)
    except ValidationError as e:
        raise DevhelmValidationError(
            "Invalid cursor-paginated response envelope",
            errors=e.errors(),
            cause=e,
        ) from e


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
        envelope = _validate_page(resp)
        all_items.extend(parse_list(model_class, envelope.data, f"GET {path}"))
        if not envelope.hasNext:
            break
        page += 1

    return all_items


def fetch_page(
    client: httpx.Client, path: str, model_class: type[M], page: int, size: int
) -> Page[M]:
    """Fetch a single page from an offset-paginated endpoint with validation."""
    resp = api_get(client, path, params={"page": page, "size": size})
    envelope = _validate_page(resp)
    return Page(
        data=parse_list(model_class, envelope.data, f"GET {path}"),
        has_next=envelope.hasNext,
        has_prev=envelope.hasPrev,
        total_elements=envelope.totalElements,
        total_pages=envelope.totalPages,
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
    envelope = _validate_cursor_page(resp)
    return CursorPage(
        data=parse_list(model_class, envelope.data, f"GET {path}"),
        next_cursor=envelope.nextCursor,
        has_more=envelope.hasMore,
    )
