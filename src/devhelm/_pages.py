"""Page types and envelope validators shared by the sync and async clients.

``TableValueResult`` (``{data, hasNext, hasPrev, totalElements,
totalPages}``) and ``CursorPage`` (``{data, nextCursor, hasMore}``) are sealed
envelopes: an unknown top-level key is spec drift and raises (AGENTS.md "SDK
Safety"). Items inside ``data`` are validated separately through their
generated models, which tolerate unknown keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from devhelm._errors import DevhelmValidationError

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """A single page from an offset-paginated endpoint."""

    data: list[T] = field(default_factory=list)
    has_next: bool = False
    has_prev: bool = False
    total_elements: int | None = None
    total_pages: int | None = None
    next_cursor: str | None = None


@dataclass
class CursorPage(Generic[T]):
    """A single page from a cursor-paginated endpoint."""

    data: list[T] = field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


class _PageEnvelope(BaseModel):
    """``TableValueResult`` metadata. Items are validated separately.

    ``nextCursor`` is tolerated because a few offset endpoints still send it
    (sdk-python #80); every other unknown key raises.
    """

    model_config = ConfigDict(extra="forbid")

    data: list[JsonValue] = []
    hasNext: bool = False
    hasPrev: bool = False
    totalElements: int | None = None
    totalPages: int | None = None
    nextCursor: str | None = None


class _CursorPageEnvelope(BaseModel):
    """``CursorPage`` envelope. See ``_PageEnvelope``."""

    model_config = ConfigDict(extra="forbid")

    data: list[JsonValue] = []
    nextCursor: str | None = None
    hasMore: bool = False


def _validate_page(resp: object) -> _PageEnvelope:
    try:
        return _PageEnvelope.model_validate(resp)
    except ValidationError as e:
        raise DevhelmValidationError(
            "Invalid paginated response envelope", errors=e.errors(), cause=e
        ) from e


def _validate_cursor_page(resp: object) -> _CursorPageEnvelope:
    try:
        return _CursorPageEnvelope.model_validate(resp)
    except ValidationError as e:
        raise DevhelmValidationError(
            "Invalid cursor-paginated response envelope", errors=e.errors(), cause=e
        ) from e
