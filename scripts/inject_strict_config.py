#!/usr/bin/env python3
"""Inject ``model_config = ConfigDict(extra='forbid', populate_by_name=True)``
into every generated Pydantic BaseModel class, and add Pydantic v2
``Field(discriminator=...)`` annotations on tagged-union fields.

datamodel-code-generator does not emit a config block when the source
OpenAPI spec lacks ``additionalProperties: false``. Springdoc never emits
that key, so we patch every generated class here.

Why ``populate_by_name=True``?
==============================
Without it, models with ``validation_alias=camelCase`` reject snake_case
kwargs because ``extra='forbid'`` treats them as unknown keys. Setting
``populate_by_name=True`` lets callers pass *either* the wire alias
(``frequencySeconds=60``) *or* the Python field name
(``frequency_seconds=60``), which makes the SDK feel like a proper
Python library instead of a thin JSON wrapper. Implements P1.Bug5 from
the round-3 DevEx audit.

Why discriminator injection?
============================
Many request bodies (``CreateAssertionRequest.config``, alert channel
configs, etc.) are *tagged unions*: every member has a
``type: Literal["..."]`` (or ``channel_type``, ``check_type``, …) field
that uniquely identifies which subtype applies. Without
``Field(discriminator='type')``, Pydantic tries every union arm in turn
and emits an error per arm — for the 41-member assertion union, that's
**161 errors** for a single bad ``operator`` field. With the
discriminator, Pydantic routes to the correct subtype based on the tag
value and reports only that subtype's errors (typically 1).
Implements P0.Bug4 from the round-3 DevEx audit.

This implements policies P1 (response extras forbidden) and P2 (request
extras forbidden) from `mini/cowork/design/040-codegen-policies.md` plus
the two DevEx fixes above.

The transform is purely syntactic so we can run it on the codegen output
without parsing Python AST. Idempotent: re-runs upgrade an existing
``model_config`` line in place if it's missing the populate_by_name flag
and skip unions already wrapped in ``Annotated[..., Field(...)]``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# RootModel subclasses cannot set `extra='forbid'` (Pydantic raises
# `root-model-extra`), so skip them. Their behavior is governed by the
# inner type, which on its own enforces strict validation.
CLASS_RE = re.compile(r"^class\s+([A-Za-z_][\w]*)\s*\(\s*(BaseModel)\s*\)\s*:\s*$")
CONFIG_LINE = "    model_config = ConfigDict(extra='forbid', populate_by_name=True)"


# StrEnum members that shadow inherited str methods need a `# type: ignore`
# because mypy thinks they're overriding the base method with an incompatible
# type. Listed explicitly so we get failures (instead of silent no-ops) when
# datamodel-codegen renames things.
STR_ENUM_COLLISIONS = {
    # member name -> mypy ignore code
    "count": "assignment",
    "index": "assignment",
    "title": "assignment",
    "lower": "assignment",
    "upper": "assignment",
    "format": "assignment",
}

STR_ENUM_RE = re.compile(r"^class\s+([A-Za-z_][\w]*)\s*\(\s*StrEnum\s*\)\s*:\s*$")
STR_ENUM_MEMBER_RE = re.compile(r"^(\s+)([a-z_][\w]*)\s*=\s*(.+?)\s*$")


def inject(source: str) -> tuple[str, int]:
    """Return (new_source, count_of_classes_modified)."""
    if "from pydantic import" in source and "ConfigDict" not in source:
        source = source.replace(
            "from pydantic import",
            "from pydantic import ConfigDict, ",
            1,
        )
        source = source.replace("ConfigDict, ConfigDict, ", "ConfigDict, ", 1)

    lines = source.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    modified = 0
    in_str_enum = False
    while i < len(lines):
        line = lines[i]
        # Handle StrEnum-member collisions before the BaseModel pass below.
        # We track whether we're inside a StrEnum body and patch any member
        # whose name shadows an inherited str method.
        if STR_ENUM_RE.match(line.rstrip("\n")):
            in_str_enum = True
            out.append(line)
            i += 1
            continue
        if in_str_enum:
            stripped = line.lstrip()
            # End of class body: dedented non-blank line.
            if stripped and not line.startswith((" ", "\t")):
                in_str_enum = False
            else:
                m_member = STR_ENUM_MEMBER_RE.match(line.rstrip("\n"))
                if m_member and m_member.group(2) in STR_ENUM_COLLISIONS:
                    code = STR_ENUM_COLLISIONS[m_member.group(2)]
                    if "type: ignore" not in line:
                        line = line.rstrip("\n") + f"  # type: ignore[{code}]\n"
                        modified += 1
                out.append(line)
                i += 1
                continue

        out.append(line)
        m = CLASS_RE.match(line.rstrip("\n"))
        if not m:
            i += 1
            continue
        # Look at the very next line. If it's already model_config or pass,
        # leave the class alone (idempotency / empty class).
        next_idx = i + 1
        next_line = lines[next_idx] if next_idx < len(lines) else ""
        if "model_config" in next_line:
            # Upgrade the existing config line to include populate_by_name=True
            # if it isn't already there. Idempotent across re-runs.
            if "populate_by_name" not in next_line:
                out.append(CONFIG_LINE + "\n")
                i += 2  # replace the existing model_config line
                modified += 1
                continue
            i += 1
            continue
        # Replace bare `pass` (empty class body) with model_config. Use
        # exact match (NOT startswith) — fields like `passed: Annotated[...]`
        # also start with "pass" but are not empty class markers.
        if next_line.strip() in ("pass", "pass\n"):
            out.append(CONFIG_LINE + "\n")
            i += 2  # skip the pass
            modified += 1
            continue
        out.append(CONFIG_LINE + "\n")
        modified += 1
        i += 1
    return "".join(out), modified


# ---------------------------------------------------------------------------
# Discriminator injection on tagged unions
# ---------------------------------------------------------------------------

# Regex for the first line of a parenthesized union field declaration.
# Matches lines like ``    config: (`` (with arbitrary indentation) and
# captures the indentation + field name so the closing paren is matched at
# the same level.
UNION_OPEN_RE = re.compile(r"^(\s+)(\w+): \(\s*$")
# Regex for the first concrete field in a class body that's a
# ``type: Literal[...]``-style discriminator tag. Captures the field name so
# we can reuse it as the Pydantic discriminator key (matches ``type``,
# ``channel_type``, ``check_type``, etc. — whichever the upstream OpenAPI
# spec used to mark the polymorphic tag).
DISC_FIELD_RE = re.compile(
    r"^    (\w+): (?:Annotated\[\s*)?Literal\[[^\]]+\]"
    r"(?:\s*,\s*Field\([^)]*\))?\s*\]?\s*=\s*"
)


def find_discriminators(source: str) -> dict[str, str]:
    """Build ``{class_name: discriminator_field}`` for classes whose first
    payload field is a single-member ``Literal[...]`` (the codegen pattern
    for OpenAPI ``type``-style tags).

    Only the *first* field after ``model_config`` counts: if a class doesn't
    lead with a discriminator we treat it as untagged and skip it later.
    This matches how the API actually models its sealed unions — every
    polymorphic subtype starts with the tag field.
    """
    result: dict[str, str] = {}
    lines = source.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^class\s+(\w+)\s*\(\s*BaseModel\s*\)\s*:\s*$", line)
        if not m:
            continue
        class_name = m.group(1)
        # Walk class body looking for the first concrete field after
        # ``model_config``. Skip blank lines and the model_config line
        # itself; if the first real field is a Literal, that's the tag.
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if not ln.strip():
                j += 1
                continue
            if ln.strip().startswith("model_config"):
                j += 1
                continue
            mf = DISC_FIELD_RE.match(ln)
            if mf:
                result[class_name] = mf.group(1)
            break
    return result


def patch_unions(source: str, discriminators: dict[str, str]) -> tuple[str, int]:
    """Wrap parenthesized union fields whose members all share the same
    discriminator tag in ``Annotated[Union[...], Field(discriminator=...)]``.

    Leaves untagged unions and mixed-tag unions alone — better to keep
    permissive validation than to silently mis-route. ``ruff format``
    re-flows the rewritten line afterwards so the file still satisfies
    the formatter's line-length rules.
    """
    lines = source.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    modified = 0
    while i < len(lines):
        line = lines[i]
        m = UNION_OPEN_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue
        indent = m.group(1)
        field_name = m.group(2)
        # Find the matching closing paren at the same indentation.
        body: list[str] = []
        j = i + 1
        close_line: str | None = None
        while j < len(lines):
            ln = lines[j]
            if ln.startswith(indent + ")"):
                close_line = ln
                break
            body.append(ln)
            j += 1
        if close_line is None:
            out.append(line)
            i += 1
            continue
        # Parse union members: each line is like ``    Foo`` or ``    | Foo``.
        members: list[str] = []
        has_none = False
        for bl in body:
            content = bl.strip()
            if content.startswith("|"):
                content = content[1:].strip()
            if not content:
                continue
            if content == "None":
                has_none = True
                continue
            members.append(content)
        # All members must be in our discriminator map and agree on the
        # tag name. Otherwise leave the union untagged.
        discs = {discriminators.get(name) for name in members}
        if not members or None in discs or len(discs) != 1:
            out.append(line)
            i += 1
            continue
        disc_field = next(iter(discs))
        union_str = " | ".join(members)
        if has_none:
            union_str += " | None"
        new_annotation = (
            f"{indent}{field_name}: Annotated[{union_str}, "
            f"Field(discriminator={disc_field!r})]"
        )
        # Preserve any default value or trailing whitespace on the close line.
        close_suffix = close_line[len(indent) + 1 :].rstrip("\n")
        if close_suffix:
            new_annotation += close_suffix
        new_annotation += "\n"
        out.append(new_annotation)
        modified += 1
        i = j + 1
    return "".join(out), modified


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inject_strict_config.py <path-to-_generated.py>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    src = path.read_text()
    new_src, modified = inject(src)
    discriminators = find_discriminators(new_src)
    new_src, union_count = patch_unions(new_src, discriminators)
    if new_src != src:
        path.write_text(new_src)
    print(
        f"inject_strict_config: patched {modified} class(es) and "
        f"{union_count} discriminated union(s) in {path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
