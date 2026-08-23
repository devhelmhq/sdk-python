"""Offset-page envelope must tolerate additive TableValueResult fields."""

from __future__ import annotations

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


def test_page_envelope_ignores_unknown_keys() -> None:
    envelope = _validate_page(
        {"data": [], "hasNext": False, "hasPrev": False, "futureField": True}
    )
    assert envelope.hasNext is False


def test_page_envelope_leaves_items_unparsed() -> None:
    envelope = _validate_page(
        {"data": [{"id": "not-validated-here"}], "hasNext": False, "hasPrev": False}
    )
    assert envelope.data[0]["id"] == "not-validated-here"
