"""Pydantic-based validation for API requests and responses.

Parses raw JSON dicts through generated Pydantic models, catching
shape mismatches before they propagate as silent bugs.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeAlias, TypeVar, Union

from pydantic import BaseModel, TypeAdapter, ValidationError

from devhelm._errors import DevhelmValidationError

M = TypeVar("M", bound=BaseModel)

# Public type alias used in resource method signatures.  Every "create"/
# "update" body parameter is annotated as ``RequestBody[<Model>]`` so that
# both fully-typed model instances *and* plain dicts (the most ergonomic
# form, and the one shown throughout the README) type-check under
# ``mypy --strict``.  ``validate_request`` normalises both forms before
# any HTTP call is made.
RequestBody: TypeAlias = Union[M, Mapping[str, Any]]


def validate_request(
    model_class: type[M], body: RequestBody[M], context: str = ""
) -> M:
    """Validate a request body against its Pydantic model before sending.

    If *body* is already an instance of *model_class* it passes through.
    Dicts and other mappings are coerced through ``model_validate``,
    raising ``DevhelmError`` on constraint violations.
    """
    if isinstance(body, model_class):
        return body
    try:
        return model_class.model_validate(body)
    except ValidationError as e:
        ctx = f" ({context})" if context else ""
        raise DevhelmValidationError(
            f"Request validation failed{ctx}: {e.error_count()} error(s) — {e}",
            errors=e.errors(),
            cause=e,
        ) from e


def parse_model(model_class: type[M], data: Any, context: str = "") -> M:
    """Parse a raw dict/JSON through a Pydantic model, raising on failure."""
    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        ctx = f" ({context})" if context else ""
        raise DevhelmValidationError(
            f"Response validation failed{ctx}: {e.error_count()} error(s) — {e}",
            errors=e.errors(),
            cause=e,
        ) from e


def parse_single(model_class: type[M], data: Any, context: str = "") -> M:
    """Parse and unwrap a SingleValueResponse envelope: {data: T} -> T as model."""
    if isinstance(data, dict) and "data" in data:
        return parse_model(model_class, data["data"], context)
    return parse_model(model_class, data, context)


def parse_list(model_class: type[M], data: Any, context: str = "") -> list[M]:
    """Parse a list of items through a Pydantic model."""
    if not isinstance(data, list):
        ctx = f" ({context})" if context else ""
        raise DevhelmValidationError(
            f"Expected list, got {type(data).__name__}{ctx}",
        )
    adapter: TypeAdapter[list[M]] = TypeAdapter(list[model_class])  # type: ignore[valid-type]
    try:
        return adapter.validate_python(data)
    except ValidationError as e:
        ctx = f" ({context})" if context else ""
        raise DevhelmValidationError(
            f"List validation failed{ctx}: {e.error_count()} error(s) — {e}",
            errors=e.errors(),
            cause=e,
        ) from e
