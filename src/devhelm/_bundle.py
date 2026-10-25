"""Collect a check's files for ``POST /bundles`` (doc 42 §5.3, doc 32 D-12).

The Python SDK is an include-set client: it never parses JavaScript or
TypeScript. It sends a set of files and the entrypoint, and the server
resolves the import closure. ``BundleDto.digest`` (the closure digest) is the
revision identity; ``BundleDto.upload_digest`` is the digest of what was
sent, which the SDK recomputes locally and compares.

``code`` takes three forms:

* a path to the entry file (``"./checkout.spec.ts"``);
* ``{"entrypoint": path, "include": [glob, …]}``;
* ``{"entrypoint": "checkout.spec.ts", "files": {path: str | bytes}}``
  (in memory: nothing is read from disk).

For the first two, the bundle root is ``root`` when given, else the nearest
ancestor of the entry file containing ``.git``, else the entry file's
directory. Paths are sent relative to the root. The default include set is
the entry file's directory, recursively, minus ``node_modules/``, ``.git/``,
``dist/``, ``build/``, ``coverage/``, ``*.map``, dotfiles (``.env*``
included) and anything ``.devhelmignore`` (gitignore syntax) matches.
``include`` globs (relative to the root) replace that default. The session
setup file (``auth.setup.ts`` next to the entry file) is always sent when it
exists. Symlinks are refused.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import subprocess
import unicodedata
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TypedDict, final

from typing_extensions import NotRequired

from devhelm._errors import client_error
from devhelm._generated import CodeSource

MAX_FILES = 256
MAX_BYTES = 5 * 1024 * 1024

TEXT_EXTENSIONS = frozenset(
    {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".json",
        ".yml",
        ".yaml",
        ".md",
        ".txt",
        ".html",
        ".css",
    }
)

EXCLUDED_DIRS = frozenset({"node_modules", "dist", "build", "coverage"})
DEFAULT_SETUP_FILE = "auth.setup.ts"
IGNORE_FILE = ".devhelmignore"


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


def _is_text(path: str) -> bool:
    return PurePosixPath(path.lower()).suffix in TEXT_EXTENSIONS


def normalize_content(path: str, content: bytes) -> bytes:
    """CRLF becomes LF for text extensions; every other file is byte for byte."""
    return content.replace(b"\r\n", b"\n") if _is_text(path) else content


def bundle_digest(files: Mapping[str, bytes]) -> str:
    """``sha256:`` + hex SHA-256 over the D-12 framing of ``files``.

    For each file in ascending order of the UTF-8 bytes of its path:
    ``u32be(len(path)) ‖ path ‖ u64be(len(content)) ‖ content``. Paths must
    already be normalised (see :func:`normalize_path`).
    """
    h = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.encode("utf-8")):
        raw_path = path.encode("utf-8")
        content = normalize_content(path, files[path])
        h.update(len(raw_path).to_bytes(4, "big"))
        h.update(raw_path)
        h.update(len(content).to_bytes(8, "big"))
        h.update(content)
    return "sha256:" + h.hexdigest()


def normalize_path(raw: str) -> str:
    """POSIX, NFC, relative, no ``./`` prefix; dotfiles and ``..`` refused."""
    path = raw.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    path = unicodedata.normalize("NFC", path)
    if not path or path.startswith("/") or "\0" in path:
        raise _path_error("Bundle paths must be relative", raw)
    for part in path.split("/"):
        if part in ("", ".", ".."):
            raise _path_error("Bundle paths must not contain parent segments", raw)
        if part.startswith("."):
            raise _path_error("Bundles cannot contain dotfiles or .env files", path)
    return path


def _path_error(message: str, field: str) -> Exception:
    return client_error(
        "validation", "MONITOR_PACKAGE_PATH_INVALID", f"{message}: {field}", field=field
    )


# -- .devhelmignore (gitignore syntax) -----------------------------------------


def _glob_to_regex(pattern: str) -> str:
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
        body = _glob_to_regex(text)
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
            rules.extend((base, line) for line in ignore.read_text().splitlines())
        return cls(rules)


# -- collecting files -------------------------------------------------------------


def _find_root(entry: Path) -> Path:
    for directory in [entry.parent, *entry.parent.parents]:
        if (directory / ".git").exists():
            return directory
    return entry.parent


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise client_error(
            "validation",
            "IMPORT_NOT_IN_BUNDLE",
            f"{path} is outside the bundle root {root}. Pass root= to include it.",
            field=str(path),
        ) from exc


def _refuse_symlink(path: Path, root: Path) -> None:
    if path.is_symlink():
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path
        raise _path_error("Bundles cannot contain symlinks", str(rel))


def _skip_name(name: str, *, is_dir: bool) -> bool:
    if name.startswith("."):
        return True
    if is_dir:
        return name in EXCLUDED_DIRS
    return name.endswith(".map")


def _walk(start: Path, root: Path, ignore: IgnoreRules) -> Iterator[Path]:
    """Yield files under ``start``, pruning excluded and ignored entries."""
    if not start.is_dir():
        return
    stack = [start]
    while stack:
        directory = stack.pop()
        for entry in sorted(directory.iterdir()):
            is_dir = entry.is_dir() and not entry.is_symlink()
            if _skip_name(entry.name, is_dir=is_dir):
                continue
            rel = entry.relative_to(root).as_posix()
            if ignore.ignored(rel, is_dir=is_dir):
                continue
            _refuse_symlink(entry, root)
            if is_dir:
                stack.append(entry)
            elif entry.is_file():
                yield entry


def _literal_prefix(pattern: str) -> tuple[str, bool]:
    """Leading glob-free segments of ``pattern``, and whether that is all of it."""
    parts = pattern.split("/")
    literal: list[str] = []
    for part in parts:
        if any(c in part for c in "*?["):
            break
        literal.append(part)
    return "/".join(literal), len(literal) == len(parts)


def _include_files(
    root: Path, patterns: Sequence[str], ignore: IgnoreRules
) -> set[Path]:
    selected: set[Path] = set()
    for raw in patterns:
        pattern = raw.replace("\\", "/")
        while pattern.startswith("./"):
            pattern = pattern[2:]
        pattern = pattern.lstrip("/")
        prefix, exact = _literal_prefix(pattern)
        start = root / prefix if prefix else root
        if exact and start.is_file():
            _refuse_symlink(start, root)
            selected.add(start)
            continue
        regex = re.compile("^" + _glob_to_regex(pattern) + "$")
        for path in _walk(start, root, ignore):
            if exact or regex.match(path.relative_to(root).as_posix()):
                selected.add(path)
    return selected


def _check_limits(files: Mapping[str, bytes]) -> None:
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


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(  # noqa: S603 (fixed argv, no shell)
            ["git", *args],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = out.stdout.strip()
    return value if out.returncode == 0 and value else None


def detect_source(entry: Path | None, root: Path | None) -> CodeSource | None:
    """Advisory ``source{repo, branch, commit, file}`` from CI env or git."""
    env = os.environ
    repo = env.get("GITHUB_REPOSITORY")
    branch = env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME")
    commit = env.get("GITHUB_SHA")
    file: str | None = None
    if root is not None and (repo is None or commit is None):
        top = _git(root, "rev-parse", "--show-toplevel")
        if top is not None:
            repo = repo or _git(root, "config", "--get", "remote.origin.url")
            branch = branch or _git(root, "rev-parse", "--abbrev-ref", "HEAD")
            commit = commit or _git(root, "rev-parse", "HEAD")
    if entry is not None and root is not None:
        top = _git(root, "rev-parse", "--show-toplevel")
        base = Path(top) if top else root
        try:
            file = entry.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            file = None
    if not any((repo, branch, commit, file)):
        return None
    return CodeSource(
        repo=repo[:512] if repo else None,
        branch=branch[:255] if branch else None,
        commit=commit[:64] if commit else None,
        file=file[:512] if file else None,
    )


def _from_memory(code: FilesCode) -> CollectedBundle:
    files: dict[str, bytes] = {}
    for raw_path, content in code["files"].items():
        path = normalize_path(raw_path)
        if path in files:
            raise _path_error("Duplicate path after normalization", path)
        files[path] = content.encode("utf-8") if isinstance(content, str) else content
    entrypoint = normalize_path(code["entrypoint"])
    if entrypoint not in files:
        raise client_error(
            "validation",
            "MONITOR_PACKAGE_PATH_INVALID",
            f"entrypoint {entrypoint} is not one of the files",
            field="code.entrypoint",
        )
    _check_limits(files)
    return CollectedBundle(
        entrypoint=entrypoint,
        files=files,
        digest=bundle_digest(files),
        root=None,
        source=None,
    )


def _from_disk(
    entry_raw: str | os.PathLike[str],
    include: Sequence[str] | None,
    root_opt: str | os.PathLike[str] | None,
    setup_file: str | None,
) -> CollectedBundle:
    entry_path = Path(entry_raw)
    if entry_path.is_symlink():
        raise _path_error("Bundles cannot contain symlinks", str(entry_path))
    entry = entry_path.resolve()
    if not entry.is_file():
        raise client_error(
            "validation",
            "MONITOR_PACKAGE_PATH_INVALID",
            f"Entry file not found: {entry_raw}",
            field="code.entrypoint",
        )
    root = Path(root_opt).resolve() if root_opt is not None else _find_root(entry)
    entry_rel = _rel(entry, root)
    # .devhelmignore files from the root down to the entry file's directory.
    chain = [entry.parent, *entry.parent.parents]
    ignore = IgnoreRules.load(
        root, [d for d in reversed(chain) if d.is_relative_to(root)]
    )
    if include:
        selected = _include_files(root, include, ignore)
    else:
        selected = set(_walk(entry.parent, root, ignore))
    selected.add(entry)
    setup = entry.parent / (setup_file or DEFAULT_SETUP_FILE)
    if setup.is_file():
        _refuse_symlink(setup, root)
        selected.add(setup.resolve())
    files: dict[str, bytes] = {}
    for path in sorted(selected):
        files[normalize_path(_rel(path, root))] = path.read_bytes()
    _check_limits(files)
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
            return _from_memory(code)
        return _from_disk(code["entrypoint"], code.get("include"), root, setup_file)
    return _from_disk(code, None, root, setup_file)
