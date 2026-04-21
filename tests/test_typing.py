"""Lock in strict typing posture for the SDK.

These tests ensure that:
  * mypy strict + ``disallow_any_explicit`` runs cleanly across the entire
    package, including the previously-excluded ``_generated.py``. The
    JSON-boundary modules (``_errors``, ``_http``, ``_pagination``,
    ``_validation``, ``_generated``) are allowlisted in ``pyproject.toml``
    via ``tool.mypy.overrides`` because they intentionally model unparsed
    JSON; every other module is ``Any``-free.
  * The resource layer — everything customers import — does not use
    ``typing.Any``.
  * The single justified ``# type: ignore`` comment is the only one in
    hand-written code (generated code may add ``[assignment]`` for the
    ``HealthThresholdType.count`` collision documented in ``scripts/typegen.sh``).

Skipped automatically if mypy is unavailable in the runtime environment (e.g.
when shipping the wheel without the ``dev`` group installed).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "devhelm"


def _have_mypy() -> bool:
    return shutil.which("mypy") is not None


@pytest.mark.skipif(not _have_mypy(), reason="mypy not installed")
def test_mypy_strict_passes_including_generated() -> None:
    result = subprocess.run(  # noqa: S603 — fixed argv, no shell.
        ["mypy", "src"], cwd=ROOT, check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "mypy strict (with disallow_any_explicit) must pass for the entire "
        "package including the generated models.\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )


def test_resource_layer_is_any_free() -> None:
    """The resource modules (everything customers import) must not use ``Any``.

    The five JSON-boundary modules are explicitly allowlisted because they
    serialise unparsed JSON; *every other* module — and especially the
    public ``resources/`` package — must stay ``Any``-free so end-user code
    inherits the strict typing guarantees promised in ``pyproject.toml``.
    """
    pattern = re.compile(r"\bAny\b")
    boundary_modules = {
        "_errors.py",
        "_http.py",
        "_pagination.py",
        "_validation.py",
        "_generated.py",
    }
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        if path.name in boundary_modules:
            continue
        text = path.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if pattern.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "The resource layer must stay `Any`-free. If you genuinely need an "
        "untyped JSON value here, prefer parsing it through a Pydantic model "
        "instead of widening the public API:\n" + "\n".join(offenders)
    )


def test_handwritten_modules_have_only_documented_type_ignores() -> None:
    """Catch sneaky `# type: ignore` additions outside the generated file."""
    pattern = re.compile(r"#\s*type:\s*ignore")
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        if path.name == "_generated.py":
            continue
        text = path.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    expected = {
        # `TypeAdapter[list[M]] = TypeAdapter(list[model_class])` would
        # require a higher-kinded type so mypy knows the constructor's
        # value-time generic line up with the annotation's type-time
        # generic. There is no way to express that in PEP-484, so the
        # ignore stays. (See `_validation.parse_list`.)
        "src/devhelm/_validation.py:126: adapter: TypeAdapter[list[M]] = "
        "TypeAdapter(list[model_class])  # type: ignore[valid-type]",
    }
    actual = set(offenders)
    extra = actual - expected
    assert not extra, (
        "Unexpected `# type: ignore` comments outside the generated file. "
        "Each suppression must be documented and added to the test allow-list:\n"
        + "\n".join(sorted(extra))
    )
