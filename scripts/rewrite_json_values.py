#!/usr/bin/env python3
"""Type free-form JSON in ``_generated.py`` as ``JsonValue`` instead of ``Any``.

Springdoc emits ``Map<String, Object>`` as ``additionalProperties: {type:
object}``, which datamodel-code-generator turns into
``dict[str, dict[str, Any]]``. That type is wrong twice: the values of those
maps are arbitrary JSON (strings, numbers, lists), so a response such as
``capturePolicySnapshot: {"screenshots": "on_failure"}`` fails validation,
and ``Any`` leaks into the public type surface.

This pass rewrites every such map to ``dict[str, JsonValue]`` and every
remaining ``Any`` type to ``JsonValue`` (pydantic's recursive JSON type, the
same one ``devhelm.JsonValue`` re-exports). Names inside string literals,
such as a description that starts with "Any", are left alone.

Idempotent: a second run finds nothing to rewrite.
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from pathlib import Path

NESTED_MAP_RE = re.compile(r"dict\[str, dict\[str, (?:Any|JsonValue)\]\]")


def _rewrite_imports(source: str) -> str:
    def typing_line(match: re.Match[str]) -> str:
        names = [n.strip() for n in match.group(1).split(",")]
        kept = [n for n in names if n and n != "Any"]
        return f"from typing import {', '.join(kept)}"

    source = re.sub(r"^from typing import (.+)$", typing_line, source, count=1, flags=re.M)

    def pydantic_line(match: re.Match[str]) -> str:
        names = {n.strip() for n in match.group(1).split(",") if n.strip()}
        names.add("JsonValue")
        return f"from pydantic import {', '.join(sorted(names))}"

    return re.sub(r"^from pydantic import (.+)$", pydantic_line, source, count=1, flags=re.M)


def _rewrite_any_names(source: str) -> str:
    lines = source.splitlines(keepends=True)
    hits: list[tuple[int, int]] = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.NAME and tok.string == "Any":
            hits.append(tok.start)
    for row, col in reversed(hits):
        line = lines[row - 1]
        lines[row - 1] = line[:col] + "JsonValue" + line[col + len("Any") :]
    return "".join(lines)


def rewrite(source: str) -> str:
    source = _rewrite_imports(source)
    source = _rewrite_any_names(source)
    return NESTED_MAP_RE.sub("dict[str, JsonValue]", source)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: rewrite_json_values.py <_generated.py>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    before = path.read_text()
    after = rewrite(before)
    path.write_text(after)
    count = before.count("Any") - after.count("Any")
    print(f"rewrite_json_values: {max(count, 0)} Any occurrence(s) typed as JsonValue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
