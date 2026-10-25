"""Pydantic-based validation for API requests and responses.

Parses raw JSON dicts through generated Pydantic models, catching
shape mismatches before they propagate as silent bugs.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias, TypeVar, Union, overload
from uuid import UUID

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic_core import ErrorDetails
from typing_extensions import TypeAliasType

from devhelm._errors import DevhelmValidationError

M = TypeVar("M", bound=BaseModel)

# A value inside a request dict: JSON, or anything the generated models
# accept for a field (nested models, UUIDs, datetimes, enum members).
# Type checkers see the recursive union; at runtime it is a TypeAliasType so
# ``typing.get_type_hints`` on resource methods never chases the forward
# reference into a module that does not define it (pydantic's JsonValue does
# the same).
if TYPE_CHECKING:
    RequestValue: TypeAlias = Union[
        str,
        int,
        float,
        bool,
        None,
        BaseModel,
        UUID,
        datetime,
        date,
        Enum,
        Sequence["RequestValue"],
        Mapping[str, "RequestValue"],
    ]
else:
    RequestValue = TypeAliasType(
        "RequestValue",
        Union[
            str,
            int,
            float,
            bool,
            None,
            BaseModel,
            UUID,
            datetime,
            date,
            Enum,
            Sequence["RequestValue"],
            Mapping[str, "RequestValue"],
        ],
    )

# Public type alias used in resource method signatures.  Every "create"/
# "update" body parameter is annotated as ``RequestBody[<Model>]`` so that
# both fully-typed model instances *and* plain dicts (the most ergonomic
# form, and the one shown throughout the README) type-check under
# ``mypy --strict``.  ``validate_request`` normalises both forms before
# any HTTP call is made.
RequestBody: TypeAlias = Union[M, Mapping[str, RequestValue]]


@overload
def validate_request(model_class: type[M], body: M, context: str = "") -> M: ...


@overload
def validate_request(
    model_class: type[M], body: Mapping[str, RequestValue], context: str = ""
) -> M: ...


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


def parse_model(model_class: type[M], data: object, context: str = "") -> M:
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


def parse_single(model_class: type[M], data: object, context: str = "") -> M:
    """Parse and unwrap a SingleValueResponse envelope: {data: T} -> T as model."""
    if isinstance(data, dict) and "data" in data:
        return parse_model(model_class, data["data"], context)
    return parse_model(model_class, data, context)


def parse_keyed_envelope(
    model_class: type[M], data: object, key: str, context: str = ""
) -> M:
    """Parse a one-key envelope such as ``{"event": T}`` or ``{"message": T}``."""
    ctx = f" ({context})" if context else ""
    if not isinstance(data, dict):
        raise DevhelmValidationError(
            f"Expected envelope dict, got {type(data).__name__}{ctx}"
        )
    extra = set(data.keys()) - {key}
    if extra or key not in data:
        raise DevhelmValidationError(
            f"Expected envelope with only `{key}`{ctx}, got {sorted(data.keys())}"
        )
    return parse_model(model_class, data[key], context)


def parse_strict_envelope(
    model_class: type[M], data: object, *, optional: bool = False, context: str = ""
) -> M | None:
    """Parse a strict ``{"data": T}`` envelope, rejecting unknown top-level keys.

    Implements P1 (response extras forbidden) at the envelope layer for
    endpoints whose ``data`` field can legitimately be ``null`` (e.g.
    ``GET /api/v1/deploy/lock`` returns ``{"data": null}`` when no lock is
    held). Unlike :func:`parse_single`, this helper:

    * Raises if the response is not a dict at all.
    * Raises if any top-level key besides ``data`` is present (loud spec
      drift detection — equivalent to ``ConfigDict(extra='forbid')`` on a
      hand-rolled envelope ``BaseModel``, but without forcing the resource
      module to declare a Pydantic class purely to get strictness).
    * Returns ``None`` for ``{"data": null}`` only when ``optional=True``.

    Hand-rolled instead of declaring an envelope ``BaseModel`` because
    Pydantic's mypy plugin synthesises ``__init__(**data: Any)`` on every
    subclass, which would trip ``disallow_any_explicit`` in the resource
    layer.
    """
    ctx = f" ({context})" if context else ""
    if not isinstance(data, dict):
        raise DevhelmValidationError(
            f"Expected envelope dict, got {type(data).__name__}{ctx}"
        )
    extra = set(data.keys()) - {"data"}
    if extra:
        raise DevhelmValidationError(
            f"Unknown envelope fields{ctx}: {sorted(extra)}",
            errors=[
                ErrorDetails(
                    type="extra_forbidden",
                    loc=(key,),
                    msg="Extra inputs are not permitted",
                    input=data[key],
                )
                for key in sorted(extra)
            ],
        )
    inner = data.get("data")
    if inner is None:
        if optional:
            return None
        raise DevhelmValidationError(f"Envelope missing required `data` field{ctx}")
    return parse_model(model_class, inner, context)


def parse_list(model_class: type[M], data: object, context: str = "") -> list[M]:
    """Parse a list of items through a Pydantic model."""
    if not isinstance(data, list):
        ctx = f" ({context})" if context else ""
        raise DevhelmValidationError(f"Expected list, got {type(data).__name__}{ctx}")
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


def merge_body(
    body: BaseModel | Mapping[str, RequestValue] | None,
    fields: Mapping[str, RequestValue],
) -> dict[str, RequestValue]:
    """Combine a body (model or mapping) with keyword fields; fields win.

    Lets every request method take either a generated model, a dict, or the
    model's fields as keyword arguments (snake_case or camelCase).
    """
    base: dict[str, RequestValue] = {}
    if isinstance(body, BaseModel):
        base.update(body.model_dump(by_alias=True, exclude_unset=True))
    elif isinstance(body, Mapping):
        base.update(body)
    elif body is not None:
        raise DevhelmValidationError(
            f"Request body must be a model or a mapping, got {type(body).__name__}"
        )
    base.update(fields)
    return base


def build_request(
    model_class: type[M],
    body: BaseModel | Mapping[str, RequestValue] | None,
    fields: Mapping[str, RequestValue],
    context: str,
) -> M:
    """Validate ``body`` plus keyword ``fields`` as ``model_class``.

    Python field names (``frequency_seconds``) and wire aliases
    (``frequencySeconds``) are both accepted and folded onto the alias, so a
    value given both ways is one key, not an unknown extra.
    """
    if isinstance(body, model_class) and not fields:
        return body
    aliases = {
        name: info.alias
        for name, info in model_class.model_fields.items()
        if info.alias is not None
    }
    merged = {aliases.get(k, k): v for k, v in merge_body(body, {}).items()}
    merged.update({aliases.get(k, k): v for k, v in fields.items()})
    return validate_request(model_class, merged, context)
