"""Advisory ``source{repo, branch, commit, file}`` from CI env or git."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from devhelm._generated import CodeSource


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


def _public_remote(url: str | None) -> str | None:
    """The remote URL without credentials (``https://user:token@host/...``)."""
    if url is None:
        return None
    parts = urlsplit(url)
    if parts.username is None and parts.password is None:
        return url
    host = parts.hostname or ""
    netloc = f"{host}:{parts.port}" if parts.port else host
    return urlunsplit(parts._replace(netloc=netloc))


def detect_source(entry: Path | None, root: Path | None) -> CodeSource | None:
    """Advisory ``source{repo, branch, commit, file}`` from CI env or git.

    The ``GITHUB_*`` variables win; git fills what they leave out. A detached
    checkout reports no branch. Credentials in the remote URL are dropped.
    """
    env = os.environ
    repo = env.get("GITHUB_REPOSITORY")
    branch = env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME")
    commit = env.get("GITHUB_SHA")
    top = _git(root, "rev-parse", "--show-toplevel") if root is not None else None
    if root is not None and top is not None:
        repo = repo or _public_remote(
            _git(root, "config", "--get", "remote.origin.url")
        )
        if branch is None:
            head = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
            branch = None if head == "HEAD" else head
        commit = commit or _git(root, "rev-parse", "HEAD")
    file: str | None = None
    if entry is not None and root is not None:
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
