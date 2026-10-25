"""Choose the files to send: bundle root, default include set and include globs."""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from pathlib import Path

from devhelm._bundle.digest import path_error
from devhelm._bundle.ignore import IgnoreRules, glob_to_regex
from devhelm._errors import client_error

EXCLUDED_DIRS = frozenset({"node_modules", "dist", "build", "coverage"})


def find_root(entry: Path) -> Path:
    for directory in [entry.parent, *entry.parent.parents]:
        if (directory / ".git").exists():
            return directory
    return entry.parent


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise client_error(
            "validation",
            "IMPORT_NOT_IN_BUNDLE",
            f"{path} is outside the bundle root {root}. Pass root= to include it.",
            field=str(path),
        ) from exc


def refuse_symlink(path: Path, root: Path) -> None:
    if path.is_symlink():
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path
        raise path_error("Bundles cannot contain symlinks", str(rel))


def skip_name(name: str, *, is_dir: bool) -> bool:
    if name.startswith("."):
        return True
    if is_dir:
        return name in EXCLUDED_DIRS
    return name.endswith(".map")


def walk(start: Path, root: Path, ignore: IgnoreRules) -> Iterator[Path]:
    """Yield files under ``start``, pruning excluded and ignored entries."""
    if not start.is_dir():
        return
    stack = [start]
    while stack:
        directory = stack.pop()
        for entry in sorted(directory.iterdir()):
            is_dir = entry.is_dir() and not entry.is_symlink()
            if skip_name(entry.name, is_dir=is_dir):
                continue
            rel = entry.relative_to(root).as_posix()
            if ignore.ignored(rel, is_dir=is_dir):
                continue
            refuse_symlink(entry, root)
            if is_dir:
                stack.append(entry)
            elif entry.is_file():
                yield entry


def literal_prefix(pattern: str) -> tuple[str, bool]:
    """Leading glob-free segments of ``pattern``, and whether that is all of it."""
    parts = pattern.split("/")
    literal: list[str] = []
    for part in parts:
        if any(c in part for c in "*?["):
            break
        literal.append(part)
    return "/".join(literal), len(literal) == len(parts)


def include_files(
    root: Path, patterns: Sequence[str], ignore: IgnoreRules
) -> set[Path]:
    selected: set[Path] = set()
    for raw in patterns:
        pattern = raw.replace("\\", "/")
        while pattern.startswith("./"):
            pattern = pattern[2:]
        pattern = pattern.lstrip("/")
        if ".." in pattern.split("/"):
            raise client_error(
                "validation",
                "IMPORT_NOT_IN_BUNDLE",
                f"include pattern {raw!r} leaves the bundle root {root}. "
                "Pass a wider root= instead.",
                field="code.include",
            )
        prefix, exact = literal_prefix(pattern)
        start = root / prefix if prefix else root
        if exact and start.is_file():
            refuse_symlink(start, root)
            selected.add(start)
            continue
        regex = re.compile("^" + glob_to_regex(pattern) + "$")
        for path in walk(start, root, ignore):
            if exact or regex.match(path.relative_to(root).as_posix()):
                selected.add(path)
    return selected
