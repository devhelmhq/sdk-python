"""Resolve a ``code`` argument to the files to upload."""

from __future__ import annotations

import io
import os
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, final

from typing_extensions import NotRequired

from devhelm._bundle.digest import bundle_digest, normalize_path, path_error
from devhelm._bundle.ignore import IgnoreRules
from devhelm._bundle.select import find_root, include_files, refuse_symlink, rel, walk
from devhelm._bundle.source import detect_source
from devhelm._errors import client_error
from devhelm._generated import CodeSource

MAX_FILES = 256


MAX_BYTES = 5 * 1024 * 1024


DEFAULT_SETUP_FILE = "auth.setup.ts"


@final
class IncludeCode(TypedDict):
    """``code`` as an entry file plus include globs relative to the root."""

    entrypoint: str
    include: NotRequired[list[str]]


@final
class FilesCode(TypedDict):
    """``code`` held in memory: bundle-relative paths to file contents."""

    entrypoint: str
    files: Mapping[str, str | bytes]


CodeInput = str | os.PathLike[str] | IncludeCode | FilesCode


@dataclass(frozen=True)
class CollectedBundle:
    """The files the SDK will upload, before any network call."""

    entrypoint: str
    files: dict[str, bytes]
    digest: str
    root: Path | None
    source: CodeSource | None

    @property
    def size(self) -> int:
        return sum(len(v) for v in self.files.values())

    def as_text(self) -> dict[str, str] | None:
        """``{path: text}`` when every file is UTF-8, else ``None`` (zip upload)."""
        out: dict[str, str] = {}
        for path, content in self.files.items():
            try:
                out[path] = content.decode("utf-8")
            except UnicodeDecodeError:
                return None
        return out

    def as_zip(self) -> bytes:
        """The files as a zip archive (used when a file is not UTF-8 text)."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(self.files, key=lambda p: p.encode("utf-8")):
                zf.writestr(path, self.files[path])
        return buf.getvalue()


# -- D-12 digest ----------------------------------------------------------------


def check_limits(files: Mapping[str, bytes]) -> None:
    total = sum(len(v) for v in files.values())
    if len(files) <= MAX_FILES and total <= MAX_BYTES:
        return
    sizes: dict[str, int] = {}
    for path, content in files.items():
        top = path.split("/", 1)[0] if "/" in path else "(root)"
        sizes[top] = sizes.get(top, 0) + len(content)
    largest = sorted(sizes.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    raise client_error(
        "validation",
        "BUNDLE_TOO_LARGE",
        f"Bundle has {len(files)} files and {total} bytes; the limit is "
        f"{MAX_FILES} files and {MAX_BYTES} bytes. Narrow it with include= or "
        ".devhelmignore.",
        details={
            "files": len(files),
            "bytes": total,
            "largestDirectories": [{"dir": d, "bytes": b} for d, b in largest],
        },
    )


def from_memory(code: FilesCode) -> CollectedBundle:
    files: dict[str, bytes] = {}
    for raw_path, content in code["files"].items():
        path = normalize_path(raw_path)
        if path in files:
            raise path_error("Duplicate path after normalization", path)
        files[path] = content.encode("utf-8") if isinstance(content, str) else content
    entrypoint = normalize_path(code["entrypoint"])
    if entrypoint not in files:
        raise client_error(
            "validation",
            "MONITOR_PACKAGE_PATH_INVALID",
            f"entrypoint {entrypoint} is not one of the files",
            field="code.entrypoint",
        )
    check_limits(files)
    return CollectedBundle(
        entrypoint=entrypoint,
        files=files,
        digest=bundle_digest(files),
        root=None,
        source=None,
    )


def from_disk(
    entry_raw: str | os.PathLike[str],
    include: Sequence[str] | None,
    root_opt: str | os.PathLike[str] | None,
    setup_file: str | None,
) -> CollectedBundle:
    entry_path = Path(entry_raw)
    if entry_path.is_symlink():
        raise path_error("Bundles cannot contain symlinks", str(entry_path))
    entry = entry_path.resolve()
    if not entry.is_file():
        raise client_error(
            "validation",
            "MONITOR_PACKAGE_PATH_INVALID",
            f"Entry file not found: {entry_raw}",
            field="code.entrypoint",
        )
    root = Path(root_opt).resolve() if root_opt is not None else find_root(entry)
    entry_rel = rel(entry, root)
    # .devhelmignore files from the root down to the entry file's directory.
    chain = [entry.parent, *entry.parent.parents]
    ignore = IgnoreRules.load(
        root, [d for d in reversed(chain) if d.is_relative_to(root)]
    )
    if include:
        selected = include_files(root, include, ignore)
    else:
        selected = set(walk(entry.parent, root, ignore))
    selected.add(entry)
    setup = entry.parent / (setup_file or DEFAULT_SETUP_FILE)
    if setup.is_file():
        refuse_symlink(setup, root)
        selected.add(setup.resolve())
    files: dict[str, bytes] = {}
    for path in sorted(selected):
        key = normalize_path(rel(path, root))
        if key in files:
            raise path_error("Duplicate path after normalization", key)
        files[key] = path.read_bytes()
    check_limits(files)
    return CollectedBundle(
        entrypoint=normalize_path(entry_rel),
        files=files,
        digest=bundle_digest(files),
        root=root,
        source=detect_source(entry, root),
    )


def collect(
    code: CodeInput,
    *,
    root: str | os.PathLike[str] | None = None,
    setup_file: str | None = None,
) -> CollectedBundle:
    """Resolve ``code`` to the files to upload. Reads the disk, never the network."""
    if isinstance(code, dict):
        if "files" in code:
            return from_memory(code)
        return from_disk(code["entrypoint"], code.get("include"), root, setup_file)
    return from_disk(code, None, root, setup_file)
