"""Page types and blocking page fetchers, kept importable from one place.

The types and envelope validators live in ``devhelm._pages``; the fetchers
are generated into ``devhelm._sync.pagination`` from the async sources.
"""

from __future__ import annotations

from devhelm._pages import (
    CursorPage,
    Page,
    _CursorPageEnvelope,
    _PageEnvelope,
    _validate_cursor_page,
    _validate_page,
)
from devhelm._sync.pagination import (
    DEFAULT_CURSOR_LIMIT,
    DEFAULT_PAGE_SIZE,
    fetch_all_cursor_pages,
    fetch_all_pages,
    fetch_cursor_page,
    fetch_page,
    fetch_table,
)

__all__ = [
    "DEFAULT_CURSOR_LIMIT",
    "DEFAULT_PAGE_SIZE",
    "CursorPage",
    "Page",
    "_CursorPageEnvelope",
    "_PageEnvelope",
    "_validate_cursor_page",
    "_validate_page",
    "fetch_all_cursor_pages",
    "fetch_all_pages",
    "fetch_cursor_page",
    "fetch_page",
    "fetch_table",
]
