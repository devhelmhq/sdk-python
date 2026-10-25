#!/usr/bin/env python3
"""Generate the sync client from the async sources.

``src/devhelm/_async`` is the single source of truth for every resource,
the transport, pagination and ``wait``. This script rewrites it into the
blocking client so ``Devhelm`` and ``AsyncDevhelm`` always have the same
surface:

  _async/resources/<name>.py  ->  resources/<name>.py
  _async/client.py            ->  client.py
  _async/<name>.py            ->  _sync/<name>.py

The rewrite is token-level: ``async def``/``await``/``async with``/``async
for`` lose their async keyword, ``AsyncX`` names become ``X``
(``AsyncTransport`` -> ``Transport``, ``httpx.AsyncClient`` -> ``httpx.Client``,
``AsyncIterator`` -> ``Iterator``), and ``devhelm._async._compat`` (asyncio
sleep and Event) becomes ``devhelm._sync._compat`` (time.sleep and
threading.Event). The output is then formatted with ruff.

Usage:
  scripts/unasync.py           write the sync files
  scripts/unasync.py --check   exit 1 if any sync file is stale
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "devhelm"
ASYNC_DIR = PKG / "_async"

# Hand-written in both trees; never generated (paths relative to _async/).
SKIP = {"_compat.py", "__init__.py"}

HEADER = (
    "# Generated from src/devhelm/{source} by scripts/unasync.py.\n"
    "# Do not edit: change the async source and run `make unasync`.\n"
)

SUBSTITUTIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bdevhelm\._async\.resources\b"), "devhelm.resources"),
    (re.compile(r"\bdevhelm\._async\.client\b"), "devhelm.client"),
    (re.compile(r"\bdevhelm\._async\b"), "devhelm._sync"),
    (re.compile(r"\basync def\b"), "def"),
    (re.compile(r"\basync with\b"), "with"),
    (re.compile(r"\basync for\b"), "for"),
    (re.compile(r"\bawait\s+"), ""),
    (re.compile(r"\basynccontextmanager\b"), "contextmanager"),
    (re.compile(r"\b__aenter__\b"), "__enter__"),
    (re.compile(r"\b__aexit__\b"), "__exit__"),
    (re.compile(r"\baclose\b"), "close"),
    (re.compile(r"\baread\b"), "read"),
    (re.compile(r"\baiter_lines\b"), "iter_lines"),
    (re.compile(r"\baiter_bytes\b"), "iter_bytes"),
    (re.compile(r"\bbuild_async_client\b"), "build_client"),
    (re.compile(r"\bAsync([A-Z]\w*)"), r"\1"),
    (re.compile(r"\bAsync\b"), "Blocking"),
    (re.compile(r"\basync\b"), "sync"),
]


def target_for(source: Path) -> Path:
    rel = source.relative_to(ASYNC_DIR)
    if rel.parts[0] == "resources":
        return PKG.joinpath(*rel.parts)
    if rel.as_posix() == "client.py":
        return PKG / "client.py"
    return PKG / "_sync" / rel


def transform(text: str) -> str:
    for pattern, repl in SUBSTITUTIONS:
        text = pattern.sub(repl, text)
    return text


def sources() -> list[Path]:
    return sorted(
        p
        for p in ASYNC_DIR.rglob("*.py")
        if p.relative_to(ASYNC_DIR).as_posix() not in SKIP
        and "__pycache__" not in p.parts
    )


def render(source: Path) -> str:
    text = transform(source.read_text())
    rel = source.relative_to(PKG).as_posix()
    return HEADER.format(source=rel) + text


def ruff(paths: list[Path]) -> None:
    if not paths:
        return
    args = [str(p) for p in paths]
    subprocess.run(
        ["ruff", "check", "--quiet", "--fix", "--select", "I,F401", *args],
        check=False,  # leftovers are reported by `ruff check` in `make lint`
        cwd=ROOT,
    )
    subprocess.run(["ruff", "format", "--quiet", *args], check=True, cwd=ROOT)


def generate(out_root: Path | None = None) -> dict[Path, Path]:
    """Write every sync file (under ``out_root`` when given). Returns
    ``{real target: written path}``."""
    written: dict[Path, Path] = {}
    for source in sources():
        target = target_for(source)
        dest = target if out_root is None else out_root / target.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(source))
        written[target] = dest
    ruff(list(written.values()))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        written = generate()
        print(f"unasync: wrote {len(written)} sync file(s)")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        # Copy the ruff config so formatting matches the repo.
        (tmp_root / "pyproject.toml").write_text((ROOT / "pyproject.toml").read_text())
        written = generate(tmp_root)
        stale = [
            str(target.relative_to(ROOT))
            for target, dest in written.items()
            if not target.exists() or target.read_text() != dest.read_text()
        ]
    # A generated file whose async source is gone is stale too.
    candidates = [
        *(PKG / "resources").glob("*.py"),
        *(PKG / "_sync").glob("*.py"),
        PKG / "client.py",
    ]
    stale += [
        str(path.relative_to(ROOT))
        for path in candidates
        if path not in written
        and path.exists()
        and path.read_text().startswith("# Generated from")
    ]
    if stale:
        print("unasync: stale sync files (run `make unasync`):", file=sys.stderr)
        for name in stale:
            print(f"  {name}", file=sys.stderr)
        return 1
    print("unasync: sync files are up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
