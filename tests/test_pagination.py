"""Offset-page envelope: sealed, except for the nextCursor key some
endpoints still send."""

from __future__ import annotations

import pytest

from devhelm._errors import DevhelmValidationError
from devhelm._pagination import _validate_page


def test_page_envelope_accepts_next_cursor() -> None:
    envelope = _validate_page(
        {
            "data": [],
            "hasNext": False,
            "hasPrev": False,
            "totalElements": 0,
            "totalPages": 0,
            "nextCursor": None,
        }
    )
    assert envelope.nextCursor is None
    assert envelope.data == []


def test_page_envelope_rejects_unknown_keys() -> None:
    # TableValueResult is a sealed envelope (AGENTS.md "SDK Safety"): a new
    # top-level key is spec drift and must fail loudly.
    with pytest.raises(DevhelmValidationError):
        _validate_page(
            {"data": [], "hasNext": False, "hasPrev": False, "futureField": True}
        )


def test_page_envelope_leaves_items_unparsed() -> None:
    envelope = _validate_page(
        {"data": [{"id": "not-validated-here"}], "hasNext": False, "hasPrev": False}
    )
    assert envelope.data[0]["id"] == "not-validated-here"
