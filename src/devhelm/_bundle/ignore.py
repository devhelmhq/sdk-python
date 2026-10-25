"""``.devhelmignore`` rules (gitignore syntax) for the default include set."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

IGNORE_FILE = ".devhelmignore"


def glob_to_regex(pattern: str) -> str:
    """Translate one gitignore-style glob (no leading ``/``) to a regex body."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out.append("/.*")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            end = pattern.find("]", i + 1)
            if end == -1:
                out.append(re.escape(c))
                i += 1
            else:
                body = pattern[i + 1 : end].replace("\\", "\\\\")
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append(f"[{body}]")
                i = end + 1
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


@dataclass(frozen=True)
class _Rule:
    regex: re.Pattern[str]
    negate: bool
    dir_only: bool


class IgnoreRules:
    """gitignore-syntax rules read from ``.devhelmignore`` files."""

    def __init__(self, rules: Sequence[tuple[str, str]] = ()) -> None:
        # ``rules`` is ``(base, line)``: ``base`` is the bundle-relative
        # directory holding the ignore file ("" for the root).
        self._rules: list[_Rule] = []
        for base, line in rules:
            rule = self._compile(base, line)
            if rule is not None:
                self._rules.append(rule)

    @staticmethod
    def _compile(base: str, line: str) -> _Rule | None:
        text = line.rstrip("\n").rstrip()
        if not text or text.startswith("#"):
            return None
        negate = text.startswith("!")
        if negate:
            text = text[1:]
        if text.startswith("\\"):
            text = text[1:]
        dir_only = text.endswith("/")
        text = text.rstrip("/")
        if not text:
            return None
        anchored = "/" in text
        text = text.lstrip("/")
        body = glob_to_regex(text)
        prefix = re.escape(base + "/") if base else ""
        head = prefix if anchored else prefix + "(?:.*/)?"
        return _Rule(re.compile(f"^{head}{body}$"), negate, dir_only)

    def ignored(self, path: str, *, is_dir: bool) -> bool:
        verdict = False
        for rule in self._rules:
            if rule.dir_only and not is_dir:
                continue
            if rule.regex.match(path):
                verdict = not rule.negate
        return verdict

    @classmethod
    def load(cls, root: Path, dirs: Sequence[Path]) -> IgnoreRules:
        rules: list[tuple[str, str]] = []
        seen: set[Path] = set()
        for directory in dirs:
            ignore = directory / IGNORE_FILE
            if ignore in seen or not ignore.is_file():
                continue
            seen.add(ignore)
            base = directory.relative_to(root).as_posix()
            base = "" if base == "." else base
            rules.extend(
                (base, line) for line in ignore.read_text(encoding="utf-8").splitlines()
            )
        return cls(rules)


# -- collecting files -------------------------------------------------------------
