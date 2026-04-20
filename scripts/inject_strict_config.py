#!/usr/bin/env python3
"""Inject `model_config = ConfigDict(extra='forbid')` into every generated
Pydantic BaseModel and RootModel class.

datamodel-code-generator does not emit a config block when the source
OpenAPI spec lacks `additionalProperties: false`. Springdoc never emits
that key, so we patch every generated class here.

This implements policies P1 (response extras forbidden) and P2 (request
extras forbidden) from `mini/cowork/design/040-codegen-policies.md`.

The transform is purely syntactic: scan each line, find `class Foo(BaseModel):`
or `class Foo(RootModel[...]):` and inject `model_config = ConfigDict(...)`
on the next non-empty indented line.

Idempotent: skips classes that already declare `model_config`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# RootModel subclasses cannot set `extra='forbid'` (Pydantic raises
# `root-model-extra`), so skip them. Their behavior is governed by the
# inner type, which on its own enforces strict validation.
CLASS_RE = re.compile(r"^class\s+([A-Za-z_][\w]*)\s*\(\s*(BaseModel)\s*\)\s*:\s*$")
CONFIG_LINE = "    model_config = ConfigDict(extra='forbid')"


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
    if new_src != src:
        path.write_text(new_src)
    print(f"inject_strict_config: patched {modified} class(es) in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
