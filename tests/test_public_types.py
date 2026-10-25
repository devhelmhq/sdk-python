"""The public type surface carries no ``Any`` and no bare ``object`` (doc 42 §5.1.2).

Walks every annotation reachable from the public API: everything in
``devhelm.__all__`` and ``devhelm.types.__all__``, every public method and
property of every resource class (sync and async), and every field of every
generated model. Free-form JSON is typed as pydantic's ``JsonValue``, which is
allowed and not descended into.

Allowlist (third-party types the SDK exposes but does not define):

* ``pydantic_core.ErrorDetails`` — the TypedDict pydantic uses for
  ``DevhelmValidationError.errors``; its ``input`` key is ``Any`` upstream.
"""

from __future__ import annotations

import inspect
import types
import typing
from collections.abc import Iterator
from typing import ForwardRef, get_args, get_origin

import pydantic
import pydantic_core
import pytest
import typing_extensions
from pydantic import BaseModel

import devhelm
import devhelm._async.client
import devhelm._generated
import devhelm.types

ALLOWED_OPAQUE: tuple[object, ...] = (pydantic_core.ErrorDetails,)

_NS: dict[str, object] = {**vars(typing), **vars(devhelm._generated), **vars(devhelm)}

_ALIAS_TYPES = tuple(
    t
    for t in (
        getattr(typing, "TypeAliasType", None),
        getattr(typing_extensions, "TypeAliasType", None),
    )
    if t is not None
)


def _is_json_value(tp: object) -> bool:
    return tp is pydantic.JsonValue


def _walk(
    tp: object, where: str, seen: set[int], ns: dict[str, object]
) -> Iterator[str]:
    if tp is typing.Any:
        yield f"{where}: Any"
        return
    if tp is object:
        yield f"{where}: object"
        return
    if _is_json_value(tp) or tp in ALLOWED_OPAQUE or id(tp) in seen:
        return
    if isinstance(tp, str):
        tp = ForwardRef(tp)
    if isinstance(tp, ForwardRef):
        try:
            resolved = eval(tp.__forward_arg__, ns)  # noqa: S307 (annotation text)
        except NameError as exc:
            yield f"{where}: unresolved {tp.__forward_arg__} ({exc})"
            return
        yield from _walk(resolved, where, seen, ns)
        return
    if isinstance(tp, _ALIAS_TYPES):
        seen.add(id(tp))
        yield from _walk(tp.__value__, f"{where}<{tp.__name__}>", seen, ns)
        return
    yield from _walk_structure(tp, where, seen, ns)


def _walk_structure(
    tp: object, where: str, seen: set[int], ns: dict[str, object]
) -> Iterator[str]:
    """Generic aliases, unions, type variables and TypedDicts."""
    origin = get_origin(tp)
    if origin is typing.Literal:
        return
    if origin is typing.Annotated:
        yield from _walk(get_args(tp)[0], where, seen, ns)
        return
    if origin is not None or isinstance(tp, types.UnionType):
        for arg in get_args(tp):
            if arg is Ellipsis:
                continue
            yield from _walk(arg, where, seen, ns)
        return
    if isinstance(tp, typing.TypeVar):
        if tp.__bound__ is not None:
            yield from _walk(tp.__bound__, where, seen, ns)
        return
    if isinstance(tp, type):
        seen.add(id(tp))
        if typing_extensions.is_typeddict(tp) and tp.__module__.startswith("devhelm"):
            for name, hint in typing.get_type_hints(tp, ns).items():
                yield from _walk(hint, f"{tp.__name__}.{name}", seen, ns)


def _ns_for(obj: object) -> dict[str, object]:
    module = inspect.getmodule(obj)
    return {**_NS, **(vars(module) if module else {})}


def _hints(obj: object) -> dict[str, object]:
    return typing.get_type_hints(obj, _ns_for(obj), include_extras=True)


def _callable_problems(fn: object, where: str) -> Iterator[str]:
    seen: set[int] = set()
    ns = _ns_for(fn)
    for name, hint in _hints(fn).items():
        yield from _walk(hint, f"{where}({name})", seen, ns)


def _class_problems(cls: type) -> Iterator[str]:
    ns = _ns_for(cls)
    if issubclass(cls, BaseModel):
        for name, info in cls.model_fields.items():
            yield from _walk(info.annotation, f"{cls.__name__}.{name}", set(), ns)
        return
    if cls.__module__.startswith(("devhelm", "tests")):
        for name, hint in _hints(cls).items():
            yield from _walk(hint, f"{cls.__name__}.{name}", set(), ns)
    for name, member in vars(cls).items():
        if name.startswith("_") and name not in ("__init__", "__call__"):
            continue
        if isinstance(member, property) and member.fget is not None:
            yield from _callable_problems(member.fget, f"{cls.__name__}.{name}")
        elif inspect.isfunction(member):
            yield from _callable_problems(member, f"{cls.__name__}.{name}")


def _resource_classes() -> list[type]:
    found: dict[str, type] = {}

    def visit(obj: object) -> None:
        for name, value in vars(obj).items():
            module = type(value).__module__
            if name.startswith("_") or not (
                module.startswith("devhelm.resources")
                or module.startswith("devhelm._async.resources")
            ):
                continue
            found[f"{module}.{type(value).__qualname__}"] = type(value)
            visit(value)

    visit(devhelm.Devhelm(token="t", base_url="http://x"))
    visit(devhelm.AsyncDevhelm(token="t", base_url="http://x"))
    return list(found.values())


def _exported() -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    for module in (devhelm, devhelm.types):
        for name in module.__all__:
            out.append((f"{module.__name__}.{name}", getattr(module, name)))
    return out


def test_exported_names_have_no_any_or_object() -> None:
    problems: list[str] = []
    for where, obj in _exported():
        if isinstance(obj, type):
            problems.extend(_class_problems(obj))
        elif inspect.isfunction(obj):
            problems.extend(_callable_problems(obj, where))
        elif isinstance(obj, _ALIAS_TYPES) or get_origin(obj) is not None:
            problems.extend(_walk(obj, where, set(), _NS))
    assert not problems, "\n".join(sorted(set(problems)))


def test_client_and_resource_methods_have_no_any_or_object() -> None:
    classes = [
        devhelm.Devhelm,
        devhelm._async.client.AsyncDevhelm,
        *_resource_classes(),
    ]
    assert len(classes) > 40
    problems: list[str] = []
    for cls in classes:
        problems.extend(_class_problems(cls))
    assert not problems, "\n".join(sorted(set(problems)))


def test_generated_models_have_no_any_or_object() -> None:
    models = [
        obj
        for obj in vars(devhelm._generated).values()
        if isinstance(obj, type)
        and issubclass(obj, BaseModel)
        and obj.__module__ == devhelm._generated.__name__
    ]
    assert len(models) > 500
    problems: list[str] = []
    for model in models:
        problems.extend(_class_problems(model))
    assert not problems, "\n".join(sorted(set(problems)))


@pytest.mark.parametrize(
    "bad", [typing.Any, object, dict[str, typing.Any], list[object]]
)
def test_the_walker_catches_bad_annotations(bad: object) -> None:
    assert list(_walk(bad, "probe", set(), _NS))


def test_the_walker_allows_json_value() -> None:
    assert not list(_walk(dict[str, pydantic.JsonValue], "probe", set(), _NS))


class _Bad:
    body: dict[str, typing.Any]

    def method(self, value: object) -> list[typing.Any]:
        return [value]

    @property
    def prop(self) -> typing.Any:
        return None


def test_the_class_walker_catches_methods_properties_and_attributes() -> None:
    problems = list(_class_problems(_Bad))
    assert any("body" in p for p in problems)
    assert any("method(value)" in p for p in problems)
    assert any("method(return)" in p for p in problems)
    assert any("prop" in p for p in problems)
