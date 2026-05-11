#!/usr/bin/env python3
"""Generate ``src/devhelm/_enums.py`` from the *un-relaxed* OpenAPI spec.

Why this exists
===============

Under the spec-level Postel's-Law relaxation
(see ``mini/runbooks/api-contract.md`` § 3 and the design notes at
the top of ``../mini/packages/openapi-tools/src/preprocess.ts``)
multi-value enums on response-shape DTOs are dropped from the
preprocessed spec before code generation. That makes the runtime
behaviour tolerant — ``MonitorDto.type`` decodes any string, including
new wire values added by the API after the SDK was built — but it also
removes the StrEnum classes that ``types.py`` historically re-exported
under public-facing names like ``IncidentStatus``,
``CustomDomainStatus``, and ``MonitorDtoType``.

We *also* don't want to depend on ``datamodel-codegen``'s numbered
suffixes (``Status1``…``Status15``, ``Type1``…``Type6``) for the
remaining request-side enums — those numbers shift whenever the spec
gains or loses an enum, which would force a churn of hand-written
imports in ``types.py`` on every schema evolution.

This script eliminates both problems by emitting one ``Literal[...]``
alias per ``(schemaName, propertyName)`` pair for every named
multi-value enum in the **un-relaxed** spec. The alias name is
``<SchemaName><PascalProperty>`` so it is stable across spec evolution
and independent of codegen numbering. ``types.py`` imports everything
from the resulting ``_enums.py`` and re-exports under the SDK's
public-facing aliases (``IncidentStatus``, ``MonitorType``, …).

Sequencing matters: the script is invoked from ``scripts/typegen.sh``
*after* datamodel-codegen has consumed the preprocessed spec, but it
reads the original (un-relaxed) spec directly so multi-value enums
survive even on response DTOs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "docs" / "openapi" / "monitoring-api.json"
OUTPUT = ROOT / "src" / "devhelm" / "_enums.py"


def pascal_property(name: str) -> str:
    parts = re.split(r"[_\-]", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def collect_named_enums(
    spec: dict[str, Any],
) -> dict[str, list[str]]:
    """Return ``{<SchemaName><PascalProperty>: [values]}`` for every
    multi-value enum on any named schema's property — request, response,
    or anywhere in between. Naming is uniform across request and
    response shapes so consumers can reference a stable alias regardless
    of which side a value travels on.
    """
    schemas = (spec.get("components") or {}).get("schemas") or {}
    out: dict[str, list[str]] = {}

    def visit(schema_name: str, properties: dict[str, Any] | None) -> None:
        if not properties:
            return
        for prop_name, prop in properties.items():
            if not isinstance(prop, dict):
                continue
            enum = prop.get("enum")
            # Emit length-1 enums too — those are discriminator tags
            # installed by `inlineDiscriminatorSubtypesWithInfo` and the
            # only way to source the canonical value from the spec
            # rather than hand-coding it. Keeps types.py free of magic
            # strings (e.g. ConfirmationPolicy.type = "multi_region").
            if (
                isinstance(enum, list)
                and len(enum) >= 1
                and all(isinstance(v, str) for v in enum)
            ):
                alias = schema_name + pascal_property(prop_name)
                out[alias] = list(enum)
            items = prop.get("items")
            if isinstance(items, dict):
                items_enum = items.get("enum")
                if (
                    isinstance(items_enum, list)
                    and len(items_enum) >= 1
                    and all(isinstance(v, str) for v in items_enum)
                ):
                    alias = schema_name + pascal_property(prop_name) + "Item"
                    out[alias] = list(items_enum)

    for name, schema in schemas.items():
        # Skip anonymous / lowercase schemas — those are inline types
        # that don't have a stable name and we don't surface them.
        if not name or not name[0].isupper():
            continue
        if not isinstance(schema, dict):
            continue
        visit(name, schema.get("properties"))
        for member in schema.get("allOf") or []:
            if isinstance(member, dict):
                visit(name, member.get("properties"))

    return out


def render(aliases: dict[str, list[str]]) -> str:
    lines = [
        '"""Auto-generated enum literal aliases (uniform request + response).',
        "",
        "DO NOT EDIT — regenerated on every ``typegen.sh`` run from the",
        "*un-relaxed* OpenAPI spec. See ``scripts/emit_response_enums.py``",
        "and ``mini/runbooks/api-contract.md`` § 3 for the design.",
        "",
        "Each alias is a ``typing.Literal[...]`` of the wire-format values",
        "the API currently accepts (request-side) or emits (response-side)",
        "for the named ``<SchemaName><Property>`` field. Naming is",
        "stable: it does not depend on ``datamodel-codegen``'s suffixed",
        "names (``Status1``, ``Type5``…) which shift on every spec change.",
        "",
        "Response-DTO fields decode to plain ``str`` in ``_generated.py``",
        "(Postel-tolerant on receive). Request-DTO fields keep strict",
        "validation through the corresponding ``StrEnum`` in",
        "``_generated.py`` (strict on send). These aliases give SDK",
        "callers a single canonical name they can annotate against in",
        "either direction.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Literal",
        "",
    ]
    for alias in sorted(aliases):
        values = aliases[alias]
        rendered = ", ".join(f'"{v}"' for v in values)
        lines.append(f"{alias} = Literal[{rendered}]")
    lines.append("")
    lines.append("__all__ = [")
    for alias in sorted(aliases):
        lines.append(f'    "{alias}",')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not SPEC_PATH.exists():
        print(f"error: spec not found at {SPEC_PATH}", file=sys.stderr)
        return 1
    spec = json.loads(SPEC_PATH.read_text())
    aliases = collect_named_enums(spec)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(aliases))
    print(f"emit_enums: wrote {len(aliases)} aliases → {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
