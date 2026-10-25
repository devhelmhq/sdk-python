"""D-12 bundle digest and bundle path rules (doc 32 D-12)."""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Mapping
from pathlib import PurePosixPath

from devhelm._errors import DevhelmApiError, client_error

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
    path = raw.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    path = unicodedata.normalize("NFC", path)
    if not path or path.startswith("/") or "\0" in path:
        raise path_error("Bundle paths must be relative", raw)
    for part in path.split("/"):
        if part == "":
            raise path_error("Bundle paths must not contain empty segments", raw)
        if part in (".", ".."):
            raise path_error("Bundle paths must not contain parent segments", raw)
        if part.startswith("."):
            raise path_error("Bundles cannot contain dotfiles or .env files", path)
    return path


def path_error(message: str, field: str) -> DevhelmApiError:
    return client_error(
        "validation", "MONITOR_PACKAGE_PATH_INVALID", f"{message}: {field}", field=field
    )


# -- .devhelmignore (gitignore syntax) -----------------------------------------
