"""Pydantic-based response validation for API responses.

Parses raw JSON dicts through generated Pydantic models, catching
shape mismatches before they propagate as silent bugs.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

from devhelm._errors import DevhelmError

M = TypeVar("M", bound=BaseModel)


def parse_model(model_class: type[M], data: Any, context: str = "") -> M:
    """Parse a raw dict/JSON through a Pydantic model, raising DevhelmError on failure."""
    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        ctx = f" ({context})" if context else ""
        raise DevhelmError(
            "VALIDATION",
            f"Response validation failed{ctx}: {e.error_count()} error(s)",
            0,
            str(e),
        ) from e


def parse_single(model_class: type[M], data: Any, context: str = "") -> M:
    """Parse and unwrap a SingleValueResponse envelope: {data: T} -> T as model."""
    if isinstance(data, dict) and "data" in data:
        return parse_model(model_class, data["data"], context)
    return parse_model(model_class, data, context)


def parse_list(model_class: type[M], data: Any, context: str = "") -> list[M]:
    """Parse a list of items through a Pydantic model."""
    if not isinstance(data, list):
        raise DevhelmError(
            "VALIDATION",
            f"Expected list, got {type(data).__name__}{f' ({context})' if context else ''}",
            0,
        )
    adapter: TypeAdapter[list[M]] = TypeAdapter(list[model_class])  # type: ignore[valid-type]
    try:
        return adapter.validate_python(data)
    except ValidationError as e:
        ctx = f" ({context})" if context else ""
        raise DevhelmError(
            "VALIDATION",
            f"List validation failed{ctx}: {e.error_count()} error(s)",
            0,
            str(e),
        ) from e
